"""Special test for reentrant surfaces"""

import io

import pytest
from SurfaceTopography.Exceptions import ReentrantDataError
from SurfaceTopography.IO import read_topography

from topobank.testing.utils import AnalysisResultMock
from topobank_statistics.functions import (
    Autocorrelation,
    CurvatureDistribution,
    PowerSpectralDensity,
    ScaleDependentCurvature,
    ScaleDependentSlope,
    SlopeDistribution,
)

from .test_functions import FakeTopographyModel


@pytest.fixture
def reentrant_line_scan():
    """Return a reentrant line scan."""
    data = """
    0 1
    1 1
    2 1
    2 2
    3 2
    4 2
    """
    in_mem_file = io.StringIO(data)
    return read_topography(in_mem_file)


@pytest.mark.parametrize(
    "analysis_class",
    [
        PowerSpectralDensity,
        SlopeDistribution,
        CurvatureDistribution,
        Autocorrelation,
        ScaleDependentSlope,
        ScaleDependentCurvature,
    ],
)
def test_raises_reentrant_data_error(reentrant_line_scan, analysis_class):
    topo = FakeTopographyModel(reentrant_line_scan)
    with pytest.raises(ReentrantDataError):
        analysis_class().topography_implementation(AnalysisResultMock(topo))
