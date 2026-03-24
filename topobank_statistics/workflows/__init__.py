"""
Statistical analysis workflows for TopoBank.

This module contains workflow implementations for various statistical
analyses of surface topography data. Each workflow is in its own file
and registers itself with the topobank workflow registry on import.
"""

# Re-export utility constants for backward compatibility
from ._utils import (APP_NAME, GAUSSIAN_FIT_SERIES_NAME,
                     VIZ_ROUGHNESS_PARAMETERS)
# Import all workflows to trigger registration
from .autocorrelation import Autocorrelation
from .curvature_distribution import CurvatureDistribution
from .height_distribution import HeightDistribution
from .power_spectral_density import PowerSpectralDensity
from .roughness_parameters import RoughnessParameters
from .scale_dependent_curvature import ScaleDependentCurvature
from .scale_dependent_slope import ScaleDependentSlope
from .slope_distribution import SlopeDistribution
from .variable_bandwidth import VariableBandwidth

__all__ = [
    # Workflows
    "Autocorrelation",
    "CurvatureDistribution",
    "HeightDistribution",
    "PowerSpectralDensity",
    "RoughnessParameters",
    "ScaleDependentCurvature",
    "ScaleDependentSlope",
    "SlopeDistribution",
    "VariableBandwidth",
    # Constants
    "APP_NAME",
    "GAUSSIAN_FIT_SERIES_NAME",
    "VIZ_ROUGHNESS_PARAMETERS",
]
