"""Variable bandwidth workflow."""

from muflow import WorkflowImplementation
from topobank.analysis.registry import register_implementation
from topobank.manager.models import Surface, Topography

from ._utils import _analysis_function, _analysis_function_for_surface


class VariableBandwidth(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.variable_bandwidth"
        display_name = "Variable bandwidth"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    def topography_implementation(self, analysis, progress_recorder=None):
        return _analysis_function(
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
        )

    def surface_implementation(self, analysis, progress_recorder=None):
        # Resampling not possible for topographies, but all function for same name must
        # have identical signatures. We hence simply fix `nb_points_per_decade` here.
        nb_points_per_decade = 10
        return _analysis_function_for_surface(
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
        )


register_implementation(VariableBandwidth)
