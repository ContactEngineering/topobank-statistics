"""
Statistical analysis workflows for TopoBank.

Ported to sds-workflows package.
"""

from sds_workflows.workflows import (Autocorrelation,
                                     CurvatureDistribution,
                                     HeightDistribution,
                                     PowerSpectralDensity,
                                     RoughnessParameters,
                                     ScaleDependentCurvature,
                                     ScaleDependentSlope,
                                     SlopeDistribution,
                                     VariableBandwidth)

# Also import topobank-specific registry to trigger registration back into topobank
from topobank.analysis.registry import register_implementation

register_implementation(Autocorrelation)
register_implementation(CurvatureDistribution)
register_implementation(HeightDistribution)
register_implementation(PowerSpectralDensity)
register_implementation(RoughnessParameters)
register_implementation(ScaleDependentCurvature)
register_implementation(ScaleDependentSlope)
register_implementation(SlopeDistribution)
register_implementation(VariableBandwidth)

# Re-export utility constants for backward compatibility
from ._utils import (APP_NAME, GAUSSIAN_FIT_SERIES_NAME,
                     VIZ_ROUGHNESS_PARAMETERS)

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
