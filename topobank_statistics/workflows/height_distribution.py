"""Height distribution workflow."""

from typing import Union

import numpy as np
from muflow import WorkflowImplementation
from topobank.analysis.context import TopobankWorkflowContext
from topobank.analysis.registry import register_implementation
from topobank.analysis.workflows import reasonable_bins_argument, wrap_series
from topobank.files.models import ManifestSet
from topobank.manager.models import Topography

from ._utils import GAUSSIAN_FIT_SERIES_NAME


class HeightDistribution(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.height_distribution"
        display_name = "Height distribution"

        implementations = {
            Topography: "topography_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        bins: Union[int, None] = None
        wfac: int = 5

    def execute(self, context: TopobankWorkflowContext) -> dict:
        """Execute height distribution analysis.

        This is the context-based interface. The subject is already
        resolved to a SurfaceTopography object.

        Parameters
        ----------
        context : TopobankWorkflowContext
            Workflow context with subject, kwargs, and file I/O.

        Returns
        -------
        dict
            Result containing scalars, series, and metadata.
        """
        topography = context.subject

        # Use workflow instance kwargs (from constructor/Parameters)
        bins = self.kwargs.bins
        wfac = self.kwargs.wfac
        if bins is None:
            bins = reasonable_bins_argument(topography)

        profile = topography.heights()

        mean_height = np.mean(profile)
        rms_height = (
            topography.rms_height_from_area()
            if topography.dim == 2
            else topography.rms_height_from_profile()
        )

        hist, bin_edges = np.histogram(
            np.ma.compressed(profile), bins=bins, density=True
        )

        minval = mean_height - wfac * rms_height
        maxval = mean_height + wfac * rms_height
        x_gauss = np.linspace(minval, maxval, 1001)
        y_gauss = np.exp(-((x_gauss - mean_height) ** 2) / (2 * rms_height**2)) / (
            np.sqrt(2 * np.pi) * rms_height
        )

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
            dict(
                name=GAUSSIAN_FIT_SERIES_NAME,
                x=x_gauss,
                y=y_gauss,
            ),
        ]

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

    def topography_implementation(
        self, analysis, folder: ManifestSet = None, progress_recorder=None
    ):
        """Legacy implementation for backward compatibility.

        Delegates to execute() using DjangoWorkflowContext.
        """
        from topobank.analysis.context import DjangoWorkflowContext

        context = DjangoWorkflowContext(
            analysis, progress_recorder=progress_recorder
        )
        return self.execute(context)


register_implementation(HeightDistribution)
