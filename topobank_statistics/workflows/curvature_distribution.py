"""Curvature distribution workflow."""

from typing import Union

import numpy as np
from muflow import WorkflowImplementation
from SurfaceTopography.Exceptions import ReentrantDataError
from topobank.analysis.registry import register_implementation
from topobank.analysis.workflows import reasonable_bins_argument, wrap_series
from topobank.manager.models import Topography

from ._utils import GAUSSIAN_FIT_SERIES_NAME, _reasonable_histogram_range


class CurvatureDistribution(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.curvature_distribution"
        display_name = "Curvature distribution"

        implementations = {
            Topography: "topography_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        bins: Union[list[float], int, None] = None
        wfac: int = 5

    def topography_implementation(self, analysis, progress_recorder=None):
        # Get low level topography from SurfaceTopography model
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

        try:
            hist, bin_edges = np.histogram(
                hist_arr,
                bins=bins,
                range=_reasonable_histogram_range(hist_arr),
                density=True,
            )
        except (ValueError, RuntimeError) as exc:
            # Workaround for GH #683 in order to recognize reentrant measurements.
            # Replace with catching of specific exception when
            # https://github.com/ContactEngineering/SurfaceTopography/issues/108 is implemented.
            if (len(exc.args) > 0) and (
                (exc.args[0] == "supplied range of [-inf, inf] is not finite")
                or ("is reentrant" in exc.args[0])
            ):
                raise ReentrantDataError(
                    "Cannot calculate curvature distribution for reentrant measurements."
                )
            raise

        minval = mean_curv - wfac * rms_curv
        maxval = mean_curv + wfac * rms_curv
        x_gauss = np.linspace(minval, maxval, 1001)
        y_gauss = np.exp(-((x_gauss - mean_curv) ** 2) / (2 * rms_curv**2)) / (
            np.sqrt(2 * np.pi) * rms_curv
        )

        unit = topography.unit
        inverse_unit = "{}⁻¹".format(unit)

        series = [
            dict(
                name="Curvature distribution",
                x=(bin_edges[:-1] + bin_edges[1:]) / 2,
                y=hist,
            ),
            dict(
                name=GAUSSIAN_FIT_SERIES_NAME,
                x=x_gauss,
                y=y_gauss,
            ),
        ]

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


register_implementation(CurvatureDistribution)
