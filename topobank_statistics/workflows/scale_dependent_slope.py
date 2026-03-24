"""Scale-dependent slope workflow."""

from muflow import WorkflowImplementation
from topobank.analysis.registry import register_implementation
from topobank.manager.models import Surface, Topography

from ._utils import (scale_dependent_roughness_parameter,
                     scale_dependent_roughness_parameter_for_surface)


class ScaleDependentSlope(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.scale_dependent_slope"
        display_name = "Scale-dependent slope"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        nb_points_per_decade: int = 10

    def topography_implementation(self, analysis, progress_recorder=None):
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
        )

    def surface_implementation(self, analysis, progress_recorder=None):
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
        )


register_implementation(ScaleDependentSlope)
