"""Special test for reentrant surfaces"""

import io
import tempfile

import pytest
from SurfaceTopography.Exceptions import ReentrantDataError
from SurfaceTopography.IO import read_topography

from topobank_statistics.testing import LocalTopobankContext
from topobank_statistics.workflows import (
    Autocorrelation,
    CurvatureDistribution,
    PowerSpectralDensity,
    ScaleDependentCurvature,
    ScaleDependentSlope,
    SlopeDistribution,
)


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
    ctx = LocalTopobankContext(
        path=tempfile.mkdtemp(),
        kwargs={},
        topography=reentrant_line_scan,
    )
    with pytest.raises(ReentrantDataError):
        analysis_class().execute(ctx)
