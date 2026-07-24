from typing import Union

import numpy as np
from muTimer import Timer
from scipy.special import erfcinv
from SurfaceTopography.Container.Averaging import log_average
from SurfaceTopography.Container.common import suggest_length_unit
from SurfaceTopography.Container.ScaleDependentStatistics import \
    scale_dependent_statistical_property
from SurfaceTopography.Exceptions import (CannotPerformAnalysisError,
                                          ReentrantDataError)
from topobank.analysis.registry import register_implementation
from topobank.analysis.workflows import (ContainerProxy,
                                         WorkflowImplementation,
                                         make_alert_entry,
                                         reasonable_bins_argument, wrap_series)
from topobank.files.models import ManifestSet
from topobank.manager.models import Surface, Topography

APP_NAME = "topobank_statistics"
VIZ_ROUGHNESS_PARAMETERS = "roughness-parameters"

# Open-access reference paper (Röttger et al., Surf. Topogr.: Metrol. Prop. 10
# (2022) 035032). Individual workflows link to the relevant section.
CE_PAPER_URL = "https://iopscience.iop.org/article/10.1088/2051-672X/ac860a"

GAUSSIAN_FIT_SERIES_NAME = "Gaussian fit"


class HeightDistribution(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.height_distribution"
        display_name = "Height distribution"
        description = (
            "Probability distribution of surface heights, shown with a Gaussian "
            "fit. The RMS height summarizes the overall vertical roughness of the "
            "measurement."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-4"

        implementations = {
            Topography: "topography_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        bins: Union[int, None] = None
        wfac: int = 5

    def topography_implementation(
        self, analysis, folder: ManifestSet = None, progress_recorder=None, timer=None
    ):
        if timer is None:
            timer = Timer()

        # Get low level topography from SurfaceTopography model
        with timer("read topography"):
            topography = analysis.subject.topography()

        # Get parameters
        bins = self.kwargs.bins
        wfac = self.kwargs.wfac
        if bins is None:
            bins = reasonable_bins_argument(topography)

        profile = topography.heights()

        compressed_profile = np.ma.compressed(profile)
        mean_height = np.mean(profile)
        rms_height = (
            topography.rms_height_from_area()
            if topography.dim == 2
            else topography.rms_height_from_profile()
        )
        # Standard deviation about the mean, used as the width of the Gaussian
        # fit (see GH statistics#38); RMS about zero would be too wide when the
        # heights have a nonzero mean.
        std_height = compressed_profile.std()

        hist, bin_edges = np.histogram(compressed_profile, bins=bins, density=True)

        try:
            unit = topography.unit
        except AttributeError:
            unit = None

        series = [
            dict(
                name="Height distribution",
                x=(bin_edges[:-1] + bin_edges[1:]) / 2,
                y=hist,
            ),
        ]

        # Only add the Gaussian fit when the width is well defined (a flat
        # topography has std == 0, which would divide by zero).
        if std_height > 0 and np.isfinite(std_height):
            minval = mean_height - wfac * std_height
            maxval = mean_height + wfac * std_height
            x_gauss = np.linspace(minval, maxval, 1001)
            y_gauss = np.exp(
                -((x_gauss - mean_height) ** 2) / (2 * std_height**2)
            ) / (np.sqrt(2 * np.pi) * std_height)
            series.append(
                dict(name=GAUSSIAN_FIT_SERIES_NAME, x=x_gauss, y=y_gauss)
            )

        return dict(
            name="Height distribution",
            scalars={
                "Mean Height": dict(value=mean_height, unit=unit),
                "RMS Height": dict(value=rms_height, unit=unit),
            },
            xlabel="Height",
            ylabel="Probability density",
            xunit="" if unit is None else unit,
            yunit="" if unit is None else "{}⁻¹".format(unit),
            series=wrap_series(series),
        )


def _reasonable_histogram_range(arr):
    """Return 'range' argument for np.histogram

    Fixes problem with too small default ranges
    which is roughly arr.max()-arr.min() < 1e-08.
    We take 5*e-8 as threshold in order to be safe.

    Parameters
    ----------
    arr: array
        array to calculate histogram for

    Returns
    -------
    (float, float)
    The lower and upper range of the bins.

    """
    arr_min = arr.min()
    arr_max = arr.max()

    if arr_max - arr_min < 5e-8:
        hist_range = (arr_min - 1e-3, arr_max + 1e-3)
    else:
        hist_range = (arr_min, arr_max)
    return hist_range


def _histogram_with_reentrant_guard(arr, bins, quantity):
    """``np.histogram(density=True)`` with a finite-range guard.

    Raises :class:`ReentrantDataError` when the data is empty or its
    histogram range is not finite (NaN/Inf, e.g. from reentrant/multivalued
    measurements) instead of letting ``np.histogram`` raise a bare
    ``ValueError`` (see GH statistics#30). ``arr`` is expected to already be
    compressed (no masked entries).
    """
    arr = np.asarray(arr)
    # `or` short-circuits so arr.min()/max() are not evaluated for an empty
    # array (which would itself raise).
    if arr.size == 0 or not np.all(np.isfinite([arr.min(), arr.max()])):
        raise ReentrantDataError(
            f"Cannot calculate {quantity} distribution for reentrant measurements."
        )
    try:
        return np.histogram(
            arr, bins=bins, density=True, range=_reasonable_histogram_range(arr)
        )
    except (ValueError, RuntimeError) as exc:
        # Fallback for range/finiteness errors raised from deeper in the stack.
        if exc.args and (
            "is not finite" in str(exc.args[0]) or "is reentrant" in str(exc.args[0])
        ):
            raise ReentrantDataError(
                f"Cannot calculate {quantity} distribution for reentrant measurements."
            )
        raise


def _chauvenet_outlier_mask(arr):
    """Boolean mask of Chauvenet outliers in ``arr`` using a robust scale.

    The scale is estimated from the median absolute deviation (MAD) rather than
    the standard deviation, so the extreme values being detected do not inflate
    the scale used to detect them (for the RMS slope this masking is precisely
    the failure mode we guard against). A value is flagged when it lies more
    than ``z_c`` robust standard deviations from the median, where
    ``z_c = Phi^{-1}(1 - 1 / (4 N))`` is Chauvenet's criterion -- the deviation
    beyond which fewer than half an observation is expected among ``N`` normal
    samples (``~ sqrt(2 ln N)`` for large ``N``).

    Returns
    -------
    mask : np.ndarray of bool
        True for outliers. All-False when the data is too small (< 3 points) or
        has a zero/non-finite robust scale (no outlier can be defined).
    z_c : float
        The threshold in robust standard deviations (NaN when not computed).
    """
    arr = np.asarray(arr)
    n = arr.size
    mask = np.zeros(n, dtype=bool)
    if n < 3:
        return mask, np.nan
    median = np.median(arr)
    # 1.4826 rescales the MAD to a standard-deviation estimate for normal data.
    robust_sigma = 1.4826 * np.median(np.abs(arr - median))
    if not np.isfinite(robust_sigma) or robust_sigma <= 0:
        return mask, np.nan
    # Chauvenet: flag when N * P(|Z| > z_c) < 1/2. With P(|Z| > z) = erfc(z/sqrt2)
    # this gives z_c = sqrt(2) * erfcinv(1 / (2 N)).
    z_c = np.sqrt(2) * erfcinv(1.0 / (2 * n))
    mask = np.abs(arr - median) > z_c * robust_sigma
    return mask, z_c


def _slope_outlier_stats(slopes):
    """Return RMS-slope outlier statistics for a slope array, or ``None``.

    ``slopes`` are the (unmasked) slope values for one direction. When
    Chauvenet outliers are present, returns a dict with ``n_outliers``,
    ``z_c``, ``rms_full`` and ``rms_trimmed`` (the RMS slope with the outliers
    removed); otherwise returns ``None``.
    """
    slopes = np.asarray(slopes)
    mask, z_c = _chauvenet_outlier_mask(slopes)
    n_outliers = int(np.count_nonzero(mask))
    if n_outliers == 0:
        return None
    inliers = slopes[~mask]
    return {
        "n_outliers": n_outliers,
        "z_c": z_c,
        "rms_full": float(np.sqrt(np.mean(slopes**2))),
        "rms_trimmed": (
            float(np.sqrt(np.mean(inliers**2))) if inliers.size else float("nan")
        ),
    }


def _slope_outlier_report(slopes, label, topography_name):
    """Return ``(extra_scalars, alert)`` describing RMS-slope outliers.

    ``slopes`` are the (unmasked) slope values for one direction. When
    Chauvenet outliers are present, the trimmed RMS slope (computed with those
    values removed) is reported alongside a warning; otherwise ``({}, None)`` is
    returned so the RMS slope is presented without embellishment.
    """
    stats = _slope_outlier_stats(slopes)
    if stats is None:
        return {}, None

    extra_scalars = {
        f"RMS Slope, outliers excluded ({label})": dict(
            value=stats["rms_trimmed"], unit="1"
        ),
    }
    message = (
        f"{stats['n_outliers']} extreme local slope value(s) in the {label} "
        f"exceed the Chauvenet outlier threshold (|slope - median| > "
        f"{stats['z_c']:.1f} robust standard deviations). Such values often stem "
        f"from overhangs or other reentrant/measurement artifacts and dominate "
        f"the RMS slope, which drops from {stats['rms_full']:.3g} to "
        f"{stats['rms_trimmed']:.3g} when they are excluded. Interpret the RMS "
        f"slope in the {label} with care."
    )
    alert = make_alert_entry("warning", topography_name, "Slope distribution", message)
    return extra_scalars, alert


def _moments_histogram_gaussian(
    arr, bins, topography, wfac, quantity, label, unit, gaussian=True
):
    """Return moments, histogram and gaussian for an array.
    :param arr: array, array to calculate moments and histogram for
    :param bins: bins argument for np.histogram
    :param topography: SurfaceTopography topography instance, used for histogram ranges
    :param wfac: numeric width factor
    :param quantity: str, what kind of quantity this is (e.g. 'slope')
    :param label: str, how these results should be extra labeled (e.g. 'x direction')
    :param unit: str, unit of the quantity (e.g. '1/nm')
    :param gaussian: bool, if True, add gaussian
    :return: scalars, series

    The result can be used to extend the result dict of the analysis functions, e.g.

    result['scalars'].update(scalars)
    result['series'].extend(series)
    """

    # Compress the (possibly) masked array to drop masked entries before
    # histogramming. np.histogram would otherwise strip the mask via
    # np.asarray and bin the fill values. This also keeps mean/rms consistent
    # with the histogrammed data. For non-masked inputs this simply flattens.
    arr = np.ma.compressed(arr)

    mean = arr.mean()
    rms = np.sqrt((arr**2).mean())
    # Standard deviation about the mean, used as the width of the Gaussian fit
    # (see GH statistics#38). RMS (about zero) overestimates the width whenever
    # the data has a nonzero mean.
    std = arr.std()

    hist, bin_edges = _histogram_with_reentrant_guard(arr, bins, quantity)

    scalars = {
        f"Mean {quantity.capitalize()} ({label})": dict(value=mean, unit=unit),
        f"RMS {quantity.capitalize()} ({label})": dict(value=rms, unit=unit),
    }

    series = [
        dict(
            name=f"{quantity.capitalize()} distribution ({label})",
            x=(bin_edges[:-1] + bin_edges[1:]) / 2,
            y=hist,
        )
    ]

    # Only add the Gaussian fit when the width is well defined (a flat/constant
    # quantity has std == 0, which would divide by zero).
    if gaussian and std > 0 and np.isfinite(std):
        minval = mean - wfac * std
        maxval = mean + wfac * std
        x_gauss = np.linspace(minval, maxval, 1001)
        y_gauss = np.exp(-((x_gauss - mean) ** 2) / (2 * std**2)) / (
            np.sqrt(2 * np.pi) * std
        )

        series.append(
            dict(name=GAUSSIAN_FIT_SERIES_NAME + f" ({label})", x=x_gauss, y=y_gauss)
        )

    return scalars, series


class SlopeDistribution(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.slope_distribution"
        display_name = "Slope distribution"
        description = (
            "Probability distribution of the local surface slope (the first "
            "derivative of height), shown with a Gaussian fit. The RMS slope "
            "reflects how steep the surface is."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-4"

        implementations = {
            Topography: "topography_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        bins: Union[int, None] = None
        wfac: int = 5

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        """Calculates slope distribution for given topography."""
        if timer is None:
            timer = Timer()

        # Get low level topography from SurfaceTopography model
        with timer("read topography"):
            topography = analysis.subject.topography()

        # Get parameters
        bins = self.kwargs.bins
        wfac = self.kwargs.wfac
        if bins is None:
            bins = reasonable_bins_argument(topography)

        scalars = {}
        series = []
        alerts = []
        topography_name = analysis.subject.name
        # .. will be completed below..

        if topography.dim == 2:
            dh_dx, dh_dy = topography.derivative(n=1)

            #
            # Results for x direction
            #
            scalars_slope_x, series_slope_x = _moments_histogram_gaussian(
                dh_dx,
                bins=bins,
                topography=topography,
                wfac=wfac,
                quantity="slope",
                unit="1",
                label="x direction",
            )
            scalars.update(scalars_slope_x)
            series.extend(series_slope_x)
            extra_x, alert_x = _slope_outlier_report(
                np.ma.compressed(dh_dx), "x direction", topography_name
            )
            scalars.update(extra_x)
            if alert_x is not None:
                alerts.append(alert_x)

            #
            # Results for y direction
            #
            scalars_slope_y, series_slope_y = _moments_histogram_gaussian(
                dh_dy,
                bins=bins,
                topography=topography,
                wfac=wfac,
                quantity="slope",
                unit="1",
                label="y direction",
            )
            scalars.update(scalars_slope_y)
            series.extend(series_slope_y)
            extra_y, alert_y = _slope_outlier_report(
                np.ma.compressed(dh_dy), "y direction", topography_name
            )
            scalars.update(extra_y)
            if alert_y is not None:
                alerts.append(alert_y)

            #
            # Results for absolute gradient
            #
            # Not sure so far, how to calculate absolute gradient..
            #
            # absolute_gradients = np.sqrt(dh_dx**2+dh_dy**2)
            # scalars_grad, series_grad = _moments_histogram_gaussian(absolute_gradients, bins=bins, wfac=wfac,
            #                                                         quantity="slope", unit="?",
            #                                                         label='absolute gradient',
            #                                                         gaussian=False)
            # result['scalars'].update(scalars_grad)
            # result['series'].extend(series_grad)

        elif topography.dim == 1:
            dh_dx = topography.derivative(n=1)
            scalars_slope_x, series_slope_x = _moments_histogram_gaussian(
                dh_dx,
                bins=bins,
                topography=topography,
                wfac=wfac,
                quantity="slope",
                unit="1",
                label="x direction",
            )
            scalars.update(scalars_slope_x)
            series.extend(series_slope_x)
            extra_x, alert_x = _slope_outlier_report(
                np.ma.compressed(dh_dx), "x direction", topography_name
            )
            scalars.update(extra_x)
            if alert_x is not None:
                alerts.append(alert_x)
        else:
            raise ValueError(
                "This analysis function can only handle 1D or 2D topographies."
            )

        return dict(
            name="Slope distribution",
            xlabel="Slope",
            ylabel="Probability density",
            xunit="1",
            yunit="1",
            scalars=scalars,
            series=wrap_series(series),
            alerts=alerts,
        )


class CurvatureDistribution(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.curvature_distribution"
        display_name = "Curvature distribution"
        description = (
            "Probability distribution of the local surface curvature (the second "
            "derivative of height), shown with a Gaussian fit. The RMS curvature "
            "reflects how sharply the surface bends."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-4"

        implementations = {
            Topography: "topography_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        bins: Union[list[float], int, None] = None
        wfac: int = 5

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        if timer is None:
            timer = Timer()

        # Get low level topography from SurfaceTopography model
        with timer("read topography"):
            topography = analysis.subject.topography()

        bins = self.kwargs.bins
        wfac = self.kwargs.wfac
        if bins is None:
            bins = reasonable_bins_argument(topography)

        #
        # Calculate the Laplacian
        #
        if topography.dim == 2:
            curv_x, curv_y = topography.derivative(n=2)
            curv = (curv_x + curv_y) / 2
        else:
            curv = topography.derivative(n=2)

        mean_curv = np.mean(curv)
        rms_curv = (
            topography.rms_curvature_from_area()
            if topography.dim == 2
            else topography.rms_curvature_from_profile()
        )

        hist_arr = np.ma.compressed(curv)
        # Standard deviation about the mean, used as the width of the Gaussian
        # fit (see GH statistics#38).
        std_curv = hist_arr.std() if hist_arr.size > 0 else 0.0

        hist, bin_edges = _histogram_with_reentrant_guard(hist_arr, bins, "curvature")

        unit = topography.unit
        inverse_unit = "{}⁻¹".format(unit)

        series = [
            dict(
                name="Curvature distribution",
                x=(bin_edges[:-1] + bin_edges[1:]) / 2,
                y=hist,
            ),
        ]

        # Only add the Gaussian fit when the width is well defined (a flat
        # topography has std == 0, which would divide by zero).
        if std_curv > 0 and np.isfinite(std_curv):
            minval = mean_curv - wfac * std_curv
            maxval = mean_curv + wfac * std_curv
            x_gauss = np.linspace(minval, maxval, 1001)
            y_gauss = np.exp(-((x_gauss - mean_curv) ** 2) / (2 * std_curv**2)) / (
                np.sqrt(2 * np.pi) * std_curv
            )
            series.append(
                dict(name=GAUSSIAN_FIT_SERIES_NAME, x=x_gauss, y=y_gauss)
            )

        return dict(
            name="Curvature distribution",
            scalars={
                "Mean Curvature": dict(value=mean_curv, unit=inverse_unit),
                "RMS Curvature": dict(value=rms_curv, unit=inverse_unit),
            },
            xlabel="Curvature",
            ylabel="Probability density",
            xunit=inverse_unit,
            yunit=unit,
            series=wrap_series(series),
        )


class PowerSpectralDensity(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.power_spectral_density"
        display_name = "Power spectral density"
        description = (
            "Power-spectral density (PSD): how the surface roughness is "
            "distributed across length scales, plotted against wavevector "
            "(large wavevector = short wavelength). A key fingerprint of a "
            "self-affine rough surface."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-6"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        window: Union[str, None] = None
        nb_points_per_decade: int = 10

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        """Calculate Power Spectrum for given topography."""
        # Get low level topography from SurfaceTopography model
        return _workflow(
            analysis.subject,
            "power_spectrum_from_profile",
            "power_spectrum_from_area",
            "Power-spectral density (PSD)",
            "Wavevector",
            "PSD",
            "1D PSD along x",
            "1D PSD along y",
            "q/π × 2D PSD",
            "{}⁻¹",
            "{}³",
            conv_2d_fac=1 / np.pi,
            conv_2d_exponent=1,
            window=self.kwargs.window,
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )

    def surface_implementation(self, analysis, progress_recorder=None, timer=None):
        """Calculate Power Spectrum for given topography."""
        # Get low level topography from SurfaceTopography model

        return _workflow_for_surface(
            analysis.subject,
            progress_recorder,
            "power_spectrum_from_profile",
            "Power-spectral density (PSD)",
            "Wavevector",
            "PSD",
            "1D PSD along x",
            "{}⁻¹",
            "{}³",
            window=self.kwargs.window,
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )


class Autocorrelation(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.autocorrelation"
        display_name = "Autocorrelation"
        description = (
            "Height-difference autocorrelation function (ACF): how the typical "
            "height difference grows with lateral distance. This is the "
            "real-space counterpart of the power-spectral density."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-7"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        nb_points_per_decade: int = 10

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        return _workflow(
            analysis.subject,
            "autocorrelation_from_profile",
            "autocorrelation_from_area",
            "Height-difference autocorrelation function (ACF)",
            "Distance",
            "ACF",
            "Along x",
            "Along y",
            "Radial average",
            "{}",
            "{}²",
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )

    def surface_implementation(self, analysis, progress_recorder=None, timer=None):
        return _workflow_for_surface(
            analysis.subject,
            progress_recorder,
            "autocorrelation_from_profile",
            "Height-difference autocorrelation function (ACF)",
            "Distance",
            "ACF",
            "Along x",
            "{}",
            "{}²",
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )


class VariableBandwidth(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.variable_bandwidth"
        display_name = "Variable bandwidth"
        description = (
            "RMS height measured over progressively larger portions of the "
            "surface (by subdividing the measurement). Reveals how roughness "
            "depends on the observation scale from a single measurement."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-8"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        return _workflow(
            analysis.subject,
            "variable_bandwidth_from_profile",
            "variable_bandwidth_from_area",
            "Variable-bandwidth analysis",
            "Bandwidth",
            "RMS height",
            "Profile decomposition along x",
            "Profile decomposition along y",
            "Areal decomposition",
            "{}",
            "{}",
            folder=analysis.folder,
            timer=timer,
        )

    def surface_implementation(self, analysis, progress_recorder=None, timer=None):
        # Resampling not possible for topographies, but all function for same name must
        # have identical signatures. We hence simply fix `nb_points_per_decade` here.
        nb_points_per_decade = 10
        return _workflow_for_surface(
            analysis.subject,
            progress_recorder,
            "variable_bandwidth_from_profile",
            "Variable-bandwidth analysis",
            "Bandwidth",
            "RMS height",
            "Profile decomposition along x",
            "{}",
            "{}",
            nb_points_per_decade=nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )


def scale_dependent_roughness_parameter(
    topography,
    progress_recorder,
    order_of_derivative,
    name,
    ylabel,
    xname,
    yname,
    xyfunc,
    xyname,
    yunit,
    folder=None,
    timer=None,
    **kwargs,
):
    if timer is None:
        timer = Timer()

    topography_name = topography.name

    with timer("read topography"):
        topography = topography.topography()

    series = []
    alerts = []

    if topography.dim == 2:
        nb_analyses = (
            6  # x-direction, y-direction, xy-direction (reliable + unreliable)
        )
    else:
        nb_analyses = 2  # Just x-direction (reliable + unreliable)
    progress_offset = 0
    progress_callback = (
        None
        if progress_recorder is None
        else lambda i, n: progress_recorder.set_progress(
            progress_offset + i / n, nb_analyses
        )
    )

    def process_series_reliable_unreliable(
        series_name, func_kwargs, is_reliable_visible=False
    ):
        """Add series for reliable and unreliable data.

        Series with reliable data is only added if there is some reliable data.
        Series are added to `series` from out scope.

        Parameters
        ----------
        series_name: str
            name of the series
        func_kwargs: dict
            arguments for `topography.scale_dependent_statistical_property`
        is_reliable_visible: bool
            If True, the series for 'reliable=True' should be visible in the UI.
            Default is False.
        """
        nonlocal series, progress_offset
        try:
            distances, rms_values_sq = topography.scale_dependent_statistical_property(
                **func_kwargs
            )
            series += [
                dict(
                    name=series_name,
                    x=distances,
                    y=np.sqrt(rms_values_sq),
                    visible=is_reliable_visible,
                )
            ]
        except CannotPerformAnalysisError as exc:
            alerts.append(
                make_alert_entry(
                    "warning", topography_name, series_name, str(exc)
                )
            )
        progress_offset += 1

        distances, rms_values_sq = topography.scale_dependent_statistical_property(
            reliable=False, **func_kwargs
        )
        series += [
            dict(
                name=series_name + " (incl. unreliable data)",
                x=distances,
                y=np.sqrt(rms_values_sq),
                visible=False,
            ),
        ]
        progress_offset += 1

    x_kwargs = dict(
        func=lambda x, y=None: np.mean(x * x),
        n=order_of_derivative,
        progress_callback=progress_callback,
        **kwargs,
    )

    process_series_reliable_unreliable(xname, x_kwargs, is_reliable_visible=True)

    if topography.dim == 2:
        y_kwargs = dict(
            func=lambda x, y: np.mean(y * y),
            n=order_of_derivative,
            progress_callback=progress_callback,
            **kwargs,
        )

        process_series_reliable_unreliable(yname, y_kwargs)

        xy_kwargs = dict(
            func=lambda x, y: np.mean(xyfunc(x, y)),
            n=order_of_derivative,
            progress_callback=progress_callback,
            **kwargs,
        )

        process_series_reliable_unreliable(xyname, xy_kwargs)

    unit = topography.unit
    return dict(
        name=name,
        xlabel="Distance",
        ylabel=ylabel,
        xunit=unit,
        yunit=yunit.format(unit),
        xscale="log",
        yscale="log",
        series=wrap_series(series),
        alerts=alerts,
    )


def scale_dependent_roughness_parameter_for_surface(
    surface,
    progress_recorder,
    order_of_derivative,
    name,
    ylabel,
    xname,
    yunit,
    folder=None,
    timer=None,
    **kwargs,
):
    if timer is None:
        timer = Timer()

    topographies = ContainerProxy(surface.topography_set.all())
    unit = suggest_length_unit(topographies, "log")

    series = []
    alerts = []

    # Factor of two for curvature
    # TODO: set_progress(i + 1, n) can report progress > 100% (e.g. on the
    # final step where i + 1 can exceed n); clamp the reported value to n.
    progress_callback = (
        None
        if progress_recorder is None
        else lambda i, n: progress_recorder.set_progress(i + 1, n)
    )

    try:
        with timer("compute"):
            distances, rms_values_sq = scale_dependent_statistical_property(
                topographies,
                lambda x, y=None: np.mean(x * x),
                n=order_of_derivative,
                unit=unit,
                progress_callback=progress_callback,
                **kwargs,
            )
        series = [
            dict(
                name=xname,
                x=distances,
                y=np.sqrt(rms_values_sq),
            )
        ]
    except CannotPerformAnalysisError as exc:
        alerts.append(
            make_alert_entry(
                "warning", surface.name, xname, str(exc)
            )
        )

    return dict(
        name=name,
        xlabel="Distance",
        ylabel=ylabel,
        xunit=unit,
        yunit=yunit.format(unit),
        xscale="log",
        yscale="log",
        series=wrap_series(series),
        alerts=alerts,
    )


class ScaleDependentSlope(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.scale_dependent_slope"
        display_name = "Scale-dependent slope"
        description = (
            "RMS slope computed as a function of scale, showing how the apparent "
            "steepness of the surface changes with the length scale at which you "
            "probe it."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-5"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        nb_points_per_decade: int = 10

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        return scale_dependent_roughness_parameter(
            analysis.subject,
            progress_recorder,
            1,
            "Scale-dependent slope",
            "Slope",
            "Slope in x-direction",
            "Slope in y-direction",
            lambda x, y: x * x + y * y,
            "Gradient",
            "1",
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )

    def surface_implementation(self, analysis, progress_recorder=None, timer=None):
        return scale_dependent_roughness_parameter_for_surface(
            analysis.subject,
            progress_recorder,
            1,
            "Scale-dependent slope",
            "Slope",
            "Slope in x-direction",
            "1",
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )


class ScaleDependentCurvature(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.scale_dependent_curvature"
        display_name = "Scale-dependent curvature"
        description = (
            "RMS curvature computed as a function of scale, showing how the "
            "apparent sharpness of surface features changes with the length "
            "scale at which you probe it."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-5"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        nb_points_per_decade: int = 10

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        return scale_dependent_roughness_parameter(
            analysis.subject,
            progress_recorder,
            2,
            "Scale-dependent curvature",
            "Curvature",
            "Curvature in x-direction",
            "Curvature in y-direction",
            lambda x, y: (x + y) ** 2 / 4,
            "1/2 Laplacian",
            "{}⁻¹",
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )

    def surface_implementation(self, analysis, progress_recorder=None, timer=None):
        return scale_dependent_roughness_parameter_for_surface(
            analysis.subject,
            progress_recorder,
            2,
            "Scale-dependent curvature",
            "Curvature",
            "Curvature in x-direction",
            "{}⁻¹",
            nb_points_per_decade=self.kwargs.nb_points_per_decade,
            folder=analysis.folder,
            timer=timer,
        )


class RoughnessParameters(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.roughness_parameters"
        display_name = "Roughness parameters"
        visualization_type = VIZ_ROUGHNESS_PARAMETERS
        description = (
            "Scalar roughness parameters (RMS height, slope and curvature) for "
            "profiles (1D) and areas (2D), with their ISO/ASME symbols. These "
            "values are specific to this measurement's bandwidth, not the whole "
            "physical surface."
        )
        reference_url = f"{CE_PAPER_URL}#stmpac860as4-4"

        implementations = {
            Topography: "topography_implementation",
        }

    def topography_implementation(self, analysis, progress_recorder=None, timer=None):
        """Calculate roughness parameters for given topography.

        Parameters
        ----------
        topography : topobank.manager.models.Topography
        progress_recorder : ProgressRecorder or None
        folder : str or None

        Returns
        -------
        list of dicts where each dict has keys

         quantity, e.g. 'RMS height' or 'RMS gradient'
         direction, e.g. 'x' or None
         from, e.g. 'profile (1D)' or 'area (2D)' or ''
         symbol, e.g. 'Sq' or ''
         value, a number or NaN
         unit, e.g. 'nm'
        """

        if timer is None:
            timer = Timer()

        # Get low level topography from SurfaceTopography model
        with timer("read topography"):
            topography = analysis.subject.topography()

        # noinspection PyBroadException
        try:
            unit = topography.unit
            inverse_unit = "{}⁻¹".format(unit)
        except KeyError:
            unit = None
            inverse_unit = None

        is_2D = topography.dim == 2
        if not is_2D and not (topography.dim == 1):
            raise ValueError(
                "This analysis function can only handle 1D or 2D topographies."
            )

        FROM_1D = "profile (1D)"
        FROM_2D = "area (2D)"

        #
        # RMS height
        #
        result = [
            {
                "quantity": "RMS height",
                "from": FROM_1D,
                "symbol": "Rq",
                "direction": "x",
                "value": topography.rms_height_from_profile(),
                "unit": unit,
            }
        ]
        if is_2D:
            result.extend(
                [
                    {
                        "quantity": "RMS height",
                        "from": FROM_1D,
                        "symbol": "Rq",
                        "direction": "y",
                        "value": topography.transpose().rms_height_from_profile(),
                        "unit": unit,
                    },
                    {
                        "quantity": "RMS height",
                        "from": FROM_2D,
                        "symbol": "Sq",
                        "direction": None,
                        "value": topography.rms_height_from_area(),
                        "unit": unit,
                    },
                ]
            )
        #
        # RMS curvature
        #
        if is_2D:
            result.extend(
                [
                    {
                        "quantity": "RMS curvature",
                        "from": FROM_1D,
                        "symbol": "",
                        "direction": "y",
                        "value": topography.transpose().rms_curvature_from_profile(),
                        "unit": inverse_unit,
                    },
                    {
                        "quantity": "RMS curvature",
                        "from": FROM_2D,
                        "symbol": "",
                        "direction": None,
                        "value": topography.rms_curvature_from_area(),
                        "unit": inverse_unit,
                    },
                ]
            )

        # RMS curvature in x direction is needed for 1D and 2D
        result.append(
            {
                "quantity": "RMS curvature",
                "from": FROM_1D,
                "symbol": "",
                "direction": "x",
                "value": topography.rms_curvature_from_profile(),
                "unit": inverse_unit,
            }
        )

        #
        # RMS gradient/slope
        #
        result.extend(
            [
                {
                    "quantity": "RMS slope",
                    "from": FROM_1D,
                    "symbol": "R&Delta;q",
                    "direction": "x",
                    "value": topography.rms_slope_from_profile(),  # x direction
                    "unit": 1,
                }
            ]
        )
        if is_2D:
            result.extend(
                [
                    {
                        "quantity": "RMS slope",
                        "from": FROM_1D,
                        "symbol": "R&Delta;q",  # HTML
                        "direction": "y",
                        "value": topography.transpose().rms_slope_from_profile(),  # y direction
                        "unit": 1,
                    },
                    {
                        "quantity": "RMS gradient",
                        "from": FROM_2D,
                        "symbol": "",
                        "direction": None,
                        "value": topography.rms_gradient(),
                        "unit": 1,
                    },
                ]
            )

        #
        # RMS slope with outliers excluded (#35)
        #
        # Extreme local slopes -- typically overhang/reentrant artifacts -- can
        # dominate the RMS slope. When Chauvenet outliers are present in a
        # direction, additionally report the RMS slope computed with those
        # values removed, so the artifact-free value is visible next to the raw
        # one. Nothing is added when the slopes are clean.
        #
        if is_2D:
            dh_dx, dh_dy = topography.derivative(n=1)
            slopes_by_direction = [("x", dh_dx), ("y", dh_dy)]
        else:
            slopes_by_direction = [("x", topography.derivative(n=1))]
        for direction, slopes in slopes_by_direction:
            stats = _slope_outlier_stats(np.ma.compressed(slopes))
            if stats is not None:
                result.append(
                    {
                        "quantity": "RMS slope, outliers excluded",
                        "from": FROM_1D,
                        "symbol": "R&Delta;q",
                        "direction": direction,
                        "value": stats["rms_trimmed"],
                        "unit": 1,
                    }
                )

        #
        # Bandwidth (pixel_size, scan_size), see GH #677
        #
        lower_bound, upper_bound = topography.bandwidth()
        result.extend(
            [
                {
                    "quantity": "Bandwidth: lower bound",
                    "from": FROM_2D if is_2D else FROM_1D,
                    "symbol": "",
                    "direction": None,
                    "value": lower_bound,
                    "unit": unit,
                },
                {
                    "quantity": "Bandwidth: upper bound",
                    "from": FROM_2D if is_2D else FROM_1D,
                    "symbol": "",
                    "direction": None,
                    "value": upper_bound,
                    "unit": unit,
                },
            ]
        )

        return result


def _workflow(
    topography,
    funcname_profile,
    funcname_area,
    name,
    xlabel,
    ylabel,
    xname,
    yname,
    aname,
    xunit,
    yunit,
    conv_2d_fac=1.0,
    conv_2d_exponent=0,
    folder=None,
    timer=None,
    **kwargs,
):
    if timer is None:
        timer = Timer()

    topography_name = topography.name

    # Switch to low level topography from SurfaceTopography model
    with timer("read topography"):
        topography = topography.topography()

    alerts = []  # list of dicts with keys 'alert_class', 'message'
    series = []  # list of dicts with series data, keys: 'name', 'x', 'y', 'visible'

    func = getattr(topography, funcname_profile)

    try:
        r, A = func(**kwargs)
        # Remove NaNs
        r = r[np.isfinite(A)]
        A = A[np.isfinite(A)]

        series += [
            dict(
                name=xname,
                x=r,
                y=A,
            ),
        ]
    except CannotPerformAnalysisError as exc:
        alerts.append(
            make_alert_entry(
                "warning", topography_name, xname, str(exc)
            )
        )

    # Create dataset with unreliable data
    ru, Au = func(reliable=False, **kwargs)

    # Remove NaNs
    ru = ru[np.isfinite(Au)]
    Au = Au[np.isfinite(Au)]

    if topography.dim == 2:

        transpose_func = getattr(topography.transpose(), funcname_profile)
        areal_func = getattr(topography, funcname_area)

        try:
            r_T, A_T = transpose_func(**kwargs)
            # Remove NaNs
            r_T = r_T[np.isfinite(A_T)]
            A_T = A_T[np.isfinite(A_T)]
            series += [
                dict(
                    name=yname,
                    x=r_T,
                    y=A_T,
                    visible=False,  # We hide everything by default except for the first data series
                ),
            ]
        except CannotPerformAnalysisError as exc:
            alerts.append(
                make_alert_entry(
                    "warning", topography_name, yname, str(exc)
                )
            )

        try:
            r_2D, A_2D = areal_func(**kwargs)
            # Remove NaNs
            r_2D = r_2D[np.isfinite(A_2D)]
            A_2D = A_2D[np.isfinite(A_2D)]
            series += [
                dict(
                    name=aname,
                    x=r_2D,
                    y=(
                        conv_2d_fac * A_2D
                        if conv_2d_exponent == 0
                        else conv_2d_fac * r_2D**conv_2d_exponent * A_2D
                    ),
                    visible=False,
                ),
            ]
        except CannotPerformAnalysisError as exc:
            alerts.append(
                make_alert_entry(
                    "warning", topography_name, aname, str(exc)
                )
            )

        ru_T, Au_T = transpose_func(reliable=False, **kwargs)
        ru_2D, Au_2D = areal_func(reliable=False, **kwargs)

        # Remove NaNs
        ru_T = ru_T[np.isfinite(Au_T)]
        Au_T = Au_T[np.isfinite(Au_T)]
        ru_2D = ru_2D[np.isfinite(Au_2D)]
        Au_2D = Au_2D[np.isfinite(Au_2D)]

    #
    # Add series with unreliable data
    #
    series += [
        dict(
            name="{} (incl. unreliable data)".format(xname),
            x=ru,
            y=Au,
            visible=False,
        ),
    ]

    if topography.dim == 2:
        series += [
            dict(
                name="{} (incl. unreliable data)".format(yname),
                x=ru_T,
                y=Au_T,
                visible=False,
            ),
            dict(
                name="{} (incl. unreliable data)".format(aname),
                x=ru_2D,
                y=(
                    conv_2d_fac * Au_2D
                    if conv_2d_exponent == 0
                    else conv_2d_fac * ru_2D**conv_2d_exponent * Au_2D
                ),
                visible=False,
            ),
        ]

    unit = topography.unit

    # Return metadata for results as a dictionary (to be stored in the postgres database)
    return dict(
        name=name,
        xlabel=xlabel,
        ylabel=ylabel,
        xunit=xunit.format(unit),
        yunit=yunit.format(unit),
        xscale="log",
        yscale="log",
        series=wrap_series(series),
        alerts=alerts,
    )


def _workflow_for_surface(
    surface,
    progress_recorder,
    funcname_profile,
    name,
    xlabel,
    ylabel,
    xname,
    xunit,
    yunit,
    folder=None,
    timer=None,
    **kwargs,
):
    """Calculate average analysis result for a surface."""
    if timer is None:
        timer = Timer()

    topographies = ContainerProxy(surface.topography_set.all())
    unit = suggest_length_unit(topographies, "log")

    series = []
    alerts = []

    # TODO: set_progress(i + 1, n) can report progress > 100% (e.g. on the
    # final step where i + 1 can exceed n); clamp the reported value to n.
    progress_callback = (
        None
        if progress_recorder is None
        else lambda i, n: progress_recorder.set_progress(i + 1, n)
    )

    try:
        with timer("compute"):
            r, A = log_average(
                topographies,
                funcname_profile,
                unit,
                progress_callback=progress_callback,
                **kwargs,
            )

        # Remove NaNs
        r = r[np.isfinite(A)]
        A = A[np.isfinite(A)]

        #
        # Build series
        #
        series += [
            dict(
                name=xname,
                x=r,
                y=A,
            )
        ]
    except CannotPerformAnalysisError as exc:
        alerts.append(
            make_alert_entry(
                "warning", surface.name, xname, str(exc)
            )
        )

    # Return metadata for results as a dictionary (to be stored in the postgres database)
    result = dict(
        name=name,
        xlabel=xlabel,
        ylabel=ylabel,
        xunit=xunit.format(unit),
        yunit=yunit.format(unit),
        xscale="log",
        yscale="log",
        series=wrap_series(series),
        alerts=alerts,
    )

    return result


register_implementation(HeightDistribution)
register_implementation(SlopeDistribution)
register_implementation(CurvatureDistribution)
register_implementation(PowerSpectralDensity)
register_implementation(Autocorrelation)
register_implementation(VariableBandwidth)
register_implementation(ScaleDependentSlope)
register_implementation(ScaleDependentCurvature)
register_implementation(RoughnessParameters)
