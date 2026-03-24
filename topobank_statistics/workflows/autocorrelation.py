"""Autocorrelation workflow."""

from muflow import WorkflowImplementation
from topobank.analysis.registry import register_implementation
from topobank.manager.models import Surface, Topography

from ._utils import _analysis_function, _analysis_function_for_surface


class Autocorrelation(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.autocorrelation"
        display_name = "Autocorrelation"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        nb_points_per_decade: int = 10

    def topography_implementation(self, analysis, progress_recorder=None):
        return _analysis_function(
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
        )

    def surface_implementation(self, analysis, progress_recorder=None):
        return _analysis_function_for_surface(
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
        )


register_implementation(Autocorrelation)
