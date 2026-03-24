"""Shared utility functions for statistical workflows."""

import numpy as np
from SurfaceTopography.Container.Averaging import log_average
from SurfaceTopography.Container.common import suggest_length_unit
from SurfaceTopography.Container.ScaleDependentStatistics import \
    scale_dependent_statistical_property
from SurfaceTopography.Exceptions import (CannotPerformAnalysisError,
                                          ReentrantDataError)
from topobank.analysis.workflows import (ContainerProxy, make_alert_entry,
                                         wrap_series)

APP_NAME = "topobank_statistics"
VIZ_ROUGHNESS_PARAMETERS = "roughness-parameters"
GAUSSIAN_FIT_SERIES_NAME = "Gaussian fit"


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

    arr = arr.flatten()

    mean = arr.mean()
    rms = np.sqrt((arr**2).mean())

    try:
        hist, bin_edges = np.histogram(
            arr, bins=bins, density=True, range=_reasonable_histogram_range(arr)
        )
    except (ValueError, RuntimeError) as exc:
        # Workaround for GH #683 in order to recognize reentrant measurements.
        # Replace with catching of specific exception when
        # https://github.com/ContactEngineering/SurfaceTopography/issues/108 is implemented.
        if (len(exc.args) > 0) and (
            (exc.args[0] == "supplied range of [0.0, inf] is not finite")
            or ("is reentrant" in exc.args[0])
        ):
            raise ReentrantDataError(
                "Cannot calculate curvature distribution for reentrant measurements."
            )
        raise

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

    if gaussian:
        minval = mean - wfac * rms
        maxval = mean + wfac * rms
        x_gauss = np.linspace(minval, maxval, 1001)
        y_gauss = np.exp(-((x_gauss - mean) ** 2) / (2 * rms**2)) / (
            np.sqrt(2 * np.pi) * rms
        )

        series.append(
            dict(name=GAUSSIAN_FIT_SERIES_NAME + f" ({label})", x=x_gauss, y=y_gauss)
        )

    return scalars, series


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
    **kwargs,
):
    topography_name = topography.name
    topography_url = topography.get_absolute_url()

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
                    "warning", topography_name, topography_url, series_name, str(exc)
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
            func=lambda x, y=None: np.mean(x * x),
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
    **kwargs,
):
    topographies = ContainerProxy(surface.topography_set.all())
    unit = suggest_length_unit(topographies, "log")

    series = []
    alerts = []

    # Factor of two for curvature
    progress_callback = (
        None
        if progress_recorder is None
        else lambda i, n: progress_recorder.set_progress(i + 1, n)
    )

    try:
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
                "warning", surface.name, surface.get_absolute_url(), xname, str(exc)
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


def _analysis_function(
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
    **kwargs,
):
    topography_name = topography.name
    topography_url = topography.get_absolute_url()

    # Switch to low level topography from SurfaceTopography model
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
                "warning", topography_name, topography_url, xname, str(exc)
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
                    "warning", topography_name, topography_url, yname, str(exc)
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
                    "warning", topography_name, topography_url, aname, str(exc)
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


def _analysis_function_for_surface(
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
    **kwargs,
):
    """Calculate average analysis result for a surface."""
    topographies = ContainerProxy(surface.topography_set.all())
    unit = suggest_length_unit(topographies, "log")

    series = []
    alerts = []

    progress_callback = (
        None
        if progress_recorder is None
        else lambda i, n: progress_recorder.set_progress(i + 1, n)
    )

    try:
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
                "warning", surface.name, surface.get_absolute_url(), xname, str(exc)
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
