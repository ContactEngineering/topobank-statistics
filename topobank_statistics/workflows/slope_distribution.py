"""Slope distribution workflow."""

from typing import Union

from muflow import WorkflowImplementation
from topobank.analysis.registry import register_implementation
from topobank.analysis.workflows import reasonable_bins_argument, wrap_series
from topobank.manager.models import Topography

from ._utils import _moments_histogram_gaussian


class SlopeDistribution(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.slope_distribution"
        display_name = "Slope distribution"

        implementations = {
            Topography: "topography_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        bins: Union[int, None] = None
        wfac: int = 5

    def topography_implementation(self, analysis, progress_recorder=None):
        """Calculates slope distribution for given topography."""
        # Get low level topography from SurfaceTopography model
        topography = analysis.subject.topography()

        # Get parameters
        bins = self.kwargs.bins
        wfac = self.kwargs.wfac
        if bins is None:
            bins = reasonable_bins_argument(topography)

        scalars = {}
        series = []
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
        )


register_implementation(SlopeDistribution)
