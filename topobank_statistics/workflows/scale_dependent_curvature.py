"""Scale-dependent curvature workflow."""

from muflow import WorkflowImplementation
from topobank.analysis.registry import register_implementation
from topobank.manager.models import Surface, Topography

from ._utils import (scale_dependent_roughness_parameter,
                     scale_dependent_roughness_parameter_for_surface)


class ScaleDependentCurvature(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.scale_dependent_curvature"
        display_name = "Scale-dependent curvature"

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
        )

    def surface_implementation(self, analysis, progress_recorder=None):
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
        )


register_implementation(ScaleDependentCurvature)
