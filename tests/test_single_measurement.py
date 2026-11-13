"""
Dataset-level (averaged) analyses of a dataset with a single measurement.

Regression test for topobank#616: averaging the per-measurement results used
to interpolate each series with scipy's interp1d, which fails with "x and y
arrays must have at least 2 entries" in some single-measurement cases. A
dataset with one measurement must give a proper averaged curve.
"""

import numpy as np
import pytest
from SurfaceTopography import NonuniformLineScan, Topography
from topobank.testing.utils import AnalysisResultMock

from topobank_statistics.workflows import (Autocorrelation,
                                           PowerSpectralDensity,
                                           ScaleDependentCurvature,
                                           ScaleDependentSlope,
                                           VariableBandwidth)


class _Measurement:
    def __init__(self, topography):
        self._topography = topography

    def topography(self):
        return self._topography


class _Measurements:
    def __init__(self, measurements):
        self._measurements = measurements

    def all(self):
        return self._measurements


class _Dataset:
    """Stands in for a Surface, as the `simple_surface` fixture does."""

    def __init__(self, topography):
        self._measurements = [_Measurement(topography)]

    @property
    def topography_set(self):
        return _Measurements(self._measurements)


def _map():
    nx, ny = 113, 123
    heights = np.resize(np.sin(np.arange(nx) * 2 * np.pi / (nx * 0.3)), (nx, ny))
    return Topography(heights, (1, 1), periodic=False, unit="um")


def _line_scan():
    x = np.arange(278) * 100 / 278
    return NonuniformLineScan(x, np.cos(x * np.pi / 2), unit="nm")


@pytest.mark.parametrize("measurement", [_map, _line_scan], ids=["map", "line_scan"])
@pytest.mark.parametrize(
    "workflow",
    [
        PowerSpectralDensity(nb_points_per_decade=3),
        Autocorrelation(nb_points_per_decade=3),
        VariableBandwidth(),
        ScaleDependentSlope(nb_points_per_decade=3),
        ScaleDependentCurvature(nb_points_per_decade=3),
    ],
    ids=lambda workflow: type(workflow).__name__,
)
def test_average_of_single_measurement(workflow, measurement):
    result = workflow.surface_implementation(
        AnalysisResultMock(_Dataset(measurement()))
    )

    # The average of one measurement is a real curve, not an empty result
    assert not result.get("alerts"), result["alerts"]
    assert result["series"]
    for s in result["series"]:
        assert len(s["x"]) == len(s["y"])
        assert len(np.ma.compressed(np.ma.asarray(s["y"]))) >= 2
