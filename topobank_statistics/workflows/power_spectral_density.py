"""Power spectral density workflow."""

from typing import Union

import numpy as np
from muflow import WorkflowImplementation
from topobank.analysis.registry import register_implementation
from topobank.manager.models import Surface, Topography

from ._utils import _analysis_function, _analysis_function_for_surface


class PowerSpectralDensity(WorkflowImplementation):
    class Meta:
        name = "topobank_statistics.power_spectral_density"
        display_name = "Power spectrum"

        implementations = {
            Topography: "topography_implementation",
            Surface: "surface_implementation",
        }

    class Parameters(WorkflowImplementation.Parameters):
        window: Union[str, None] = None
        nb_points_per_decade: int = 10

    def topography_implementation(self, analysis, progress_recorder=None):
        """Calculate Power Spectrum for given topography."""
        # Get low level topography from SurfaceTopography model
        return _analysis_function(
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
        )

    def surface_implementation(self, analysis, progress_recorder=None):
        """Calculate Power Spectrum for given topography."""
        # Get low level topography from SurfaceTopography model

        return _analysis_function_for_surface(
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
        )


register_implementation(PowerSpectralDensity)
