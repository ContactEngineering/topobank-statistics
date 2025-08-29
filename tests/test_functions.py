import math

import numpy as np
import pint
import pytest
from numpy.testing import assert_allclose
from SurfaceTopography import NonuniformLineScan, Topography
from topobank.analysis.models import Workflow
from topobank.testing.utils import AnalysisResultMock, FakeTopographyModel

from topobank_statistics.workflows import (Autocorrelation,
                                           CurvatureDistribution,
                                           HeightDistribution,
                                           PowerSpectralDensity,
                                           RoughnessParameters,
                                           ScaleDependentSlope,
                                           SlopeDistribution,
                                           VariableBandwidth)

EXPECTED_KEYS_FOR_DIST_ANALYSIS = sorted(
    ["name", "scalars", "xlabel", "ylabel", "xunit", "yunit", "series"]
)
EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS = sorted(
    [
        "alerts",
        "name",
        "xlabel",
        "ylabel",
        "xunit",
        "yunit",
        "xscale",
        "yscale",
        "series",
    ]
)


###############################################################################
# Tests for line scans
###############################################################################


def test_height_distribution_simple_line_scan():
    x = np.array((1, 2, 3))
    y = 2 * x

    t = NonuniformLineScan(x, y, unit="nm").detrend(detrend_mode="center")

    topography = FakeTopographyModel(t)

    result = HeightDistribution().topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_DIST_ANALYSIS

    assert result["name"] == "Height distribution"
    assert result["scalars"] == {
        "Mean Height": {"value": 0, "unit": "nm"},
        "RMS Height": {"value": math.sqrt(4.0 / 3), "unit": "nm"},
    }

    assert result["xlabel"] == "Height"
    assert result["ylabel"] == "Probability density"
    assert result["xunit"] == "nm"
    assert result["yunit"] == "nm⁻¹"

    assert len(result["series"]) == 2

    exp_bins = np.array([-1, 1])  # expected values for height bins
    exp_height_dist_values = [1.0 / 6, 2.0 / 6]  # expected values
    series0 = result["series"][0]
    np.testing.assert_almost_equal(series0["x"], exp_bins)
    np.testing.assert_almost_equal(series0["y"], exp_height_dist_values)

    # not testing gauss values yet since number of points is unknown
    # proposal: use a well tested function instead of own formula


def test_slope_distribution_simple_line_scan():
    x = np.array((1, 2, 3, 4))
    y = -2 * x

    t = NonuniformLineScan(x, y).detrend(detrend_mode="center")

    topography = FakeTopographyModel(t)

    result = SlopeDistribution(bins=3).topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_DIST_ANALYSIS

    assert result["name"] == "Slope distribution"
    assert result["scalars"] == {
        "Mean Slope (x direction)": dict(
            value=-2.0, unit="1"
        ),  # absolute value of slope
        "RMS Slope (x direction)": dict(value=2.0, unit="1"),  # absolute value of slope
    }

    assert result["xlabel"] == "Slope"
    assert result["ylabel"] == "Probability density"
    assert result["xunit"] == "1"
    assert result["yunit"] == "1"

    assert len(result["series"]) == 2

    exp_bins = np.array([-2 - 1 / 1500, -2, -2 + 1 / 1500])  # for slopes
    exp_slope_dist_values = [0, 1500, 0]  # integral with dx=1/3 results to 1
    series0 = result["series"][0]
    np.testing.assert_almost_equal(series0["x"], exp_bins)
    np.testing.assert_almost_equal(series0["y"], exp_slope_dist_values)

    # not testing gauss values yet since number of points is unknown
    # proposal: use a well tested function instead of own formula


def test_curvature_distribution_simple_line_scan():
    unit = "nm"
    x = np.arange(10)
    y = -2 * x**2  # constant curvature

    t = NonuniformLineScan(x, y, unit=unit).detrend(detrend_mode="center")
    topography = FakeTopographyModel(t)

    bins = np.array(
        (-4.75, -4.25, -3.75, -3.25)
    )  # special for this test in order to know results
    result = CurvatureDistribution(bins=bins).topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_DIST_ANALYSIS

    assert result["name"] == "Curvature distribution"

    assert pytest.approx(result["scalars"]["Mean Curvature"]["value"]) == -4
    assert pytest.approx(result["scalars"]["RMS Curvature"]["value"]) == 4
    assert result["scalars"]["Mean Curvature"]["unit"] == "{}⁻¹".format(unit)
    assert result["scalars"]["RMS Curvature"]["unit"] == "{}⁻¹".format(unit)

    assert result["xlabel"] == "Curvature"
    assert result["ylabel"] == "Probability density"
    assert result["xunit"] == "{}⁻¹".format(unit)
    assert result["yunit"] == unit

    assert len(result["series"]) == 2

    exp_bins = (bins[1:] + bins[:-1]) / 2
    exp_curv_dist_values = [0, 2, 0]

    # integral over dx= should be 1
    assert np.trapz(exp_curv_dist_values, exp_bins) == pytest.approx(1)

    series0 = result["series"][0]
    np.testing.assert_almost_equal(series0["x"], exp_bins)
    np.testing.assert_almost_equal(series0["y"], exp_curv_dist_values)

    # not testing gauss values yet since number of points is unknown
    # proposal: use a well tested function instead of own formula


def test_power_spectrum_simple_nonuniform_linescan():
    unit = "nm"
    x = np.arange(10)
    y = -2 * x**2  # constant curvature

    t = NonuniformLineScan(x, y, unit=unit).detrend(detrend_mode="center")
    topography = FakeTopographyModel(t)

    result = PowerSpectralDensity().topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS

    assert result["name"] == "Power-spectral density (PSD)"

    assert result["xlabel"] == "Wavevector"
    assert result["ylabel"] == "PSD"
    assert result["xunit"] == "{}⁻¹".format(unit)
    assert result["yunit"] == "{}³".format(unit)

    assert len(result["series"]) == 2

    s0, s1 = result["series"]

    assert s0["name"] == "1D PSD along x"
    assert s1["name"] == "1D PSD along x (incl. unreliable data)"

    # TODO Also check values here as integration test?


def test_autocorrelation_simple_nonuniform_topography():
    x = np.arange(5)
    h = 2 * x

    t = NonuniformLineScan(x, h, unit="nm").detrend("center")
    topography = FakeTopographyModel(t)

    result = Autocorrelation().topography_implementation(AnalysisResultMock(topography))

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS

    assert result["name"] == "Height-difference autocorrelation function (ACF)"

    # TODO Check result values for autocorrelation


def test_variable_bandwidth_simple_nonuniform_linescan():
    x = np.arange(5)
    h = 2 * x

    t = NonuniformLineScan(x, h, unit="nm").detrend("center")
    topography = FakeTopographyModel(t)

    result = VariableBandwidth().topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS

    assert result["name"] == "Variable-bandwidth analysis"
    # TODO Check result values for bandwidth


###############################################################################
# Tests for 2D topographies
###############################################################################


@pytest.fixture
def simple_linear_2d_topography():
    """Simple 2D topography, which is linear in y"""
    unit = "nm"
    y = np.arange(10).reshape((1, -1))
    x = np.arange(5).reshape((-1, 1))
    arr = -2 * y + 0 * x  # only slope in y direction
    t = Topography(arr, (5, 10), unit=unit).detrend("center")
    return t


def test_height_distribution_simple_2d_topography(simple_linear_2d_topography):
    exp_unit = simple_linear_2d_topography.unit
    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = HeightDistribution(bins=10).topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_DIST_ANALYSIS

    assert result["name"] == "Height distribution"

    assert pytest.approx(result["scalars"]["Mean Height"]["value"]) == 0.0
    assert pytest.approx(result["scalars"]["RMS Height"]["value"]) == np.sqrt(33)
    assert result["scalars"]["Mean Height"]["unit"] == exp_unit
    assert result["scalars"]["RMS Height"]["unit"] == exp_unit

    assert result["xlabel"] == "Height"
    assert result["ylabel"] == "Probability density"
    assert result["xunit"] == exp_unit
    assert result["yunit"] == "{}⁻¹".format(exp_unit)

    assert len(result["series"]) == 2

    exp_bins = np.array(
        [-8.1, -6.3, -4.5, -2.7, -0.9, 0.9, 2.7, 4.5, 6.3, 8.1]
    )  # for heights
    exp_height_dist_values = (
        np.ones((10,)) * 1 / (10 * 1.8)
    )  # each interval has width of 1.8, 10 intervals
    series0, series1 = result["series"]

    assert series0["name"] == "Height distribution"

    np.testing.assert_almost_equal(series0["x"], exp_bins)
    np.testing.assert_almost_equal(series0["y"], exp_height_dist_values)

    assert series1["name"] == "Gaussian fit"
    # TODO not testing gauss values yet since number of points is unknown
    # proposal: use a well tested function instead of own formula


def test_slope_distribution_simple_2d_topography(simple_linear_2d_topography):
    # resulting heights follow this function: h(x,y)=-4y+9
    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = SlopeDistribution(bins=3).topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_DIST_ANALYSIS

    assert result["name"] == "Slope distribution"

    assert pytest.approx(result["scalars"]["Mean Slope (x direction)"]["value"]) == 0.0
    assert pytest.approx(result["scalars"]["Mean Slope (y direction)"]["value"]) == -2.0
    assert pytest.approx(result["scalars"]["RMS Slope (x direction)"]["value"]) == 0.0
    assert pytest.approx(result["scalars"]["RMS Slope (y direction)"]["value"]) == 2.0

    for kind, dir in zip(["Mean", "RMS"], ["x", "y"]):
        assert result["scalars"][f"{kind} Slope ({dir} direction)"]["unit"] == "1"

    assert result["xlabel"] == "Slope"
    assert result["ylabel"] == "Probability density"
    assert result["xunit"] == "1"
    assert result["yunit"] == "1"

    assert len(result["series"]) == 4

    exp_bins_x = np.array([-1.0 / 1500, 0, 1.0 / 1500])  # for slopes
    exp_slope_dist_values_x = [0, 1500, 0]
    series0, series1, series2, series3 = result["series"]

    assert series0["name"] == "Slope distribution (x direction)"

    np.testing.assert_almost_equal(series0["x"], exp_bins_x)
    np.testing.assert_almost_equal(series0["y"], exp_slope_dist_values_x)

    exp_bins_y = np.array([-2 - 1.0 / 1500, -2, -2 + 1.0 / 1500])  # for slopes
    exp_slope_dist_values_y = [0, 1500, 0]

    assert series1["name"] == "Gaussian fit (x direction)"

    assert series2["name"] == "Slope distribution (y direction)"

    np.testing.assert_almost_equal(series2["x"], exp_bins_y)
    np.testing.assert_almost_equal(series2["y"], exp_slope_dist_values_y)

    assert series3["name"] == "Gaussian fit (y direction)"
    # TODO not testing gauss values yet since number of points is unknown
    # proposal: use a well tested function instead of own formula


def test_curvature_distribution_simple_2d_topography(simple_linear_2d_topography):
    unit = simple_linear_2d_topography.unit
    # resulting heights follow this function: h(x,y)=-4y+9

    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = CurvatureDistribution(bins=3).topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_DIST_ANALYSIS

    assert result["name"] == "Curvature distribution"

    assert pytest.approx(result["scalars"]["Mean Curvature"]["value"]) == 0.0
    assert pytest.approx(result["scalars"]["RMS Curvature"]["value"]) == 0.0
    assert result["scalars"]["Mean Curvature"]["unit"] == "{}⁻¹".format(unit)
    assert result["scalars"]["RMS Curvature"]["unit"] == "{}⁻¹".format(unit)

    assert result["xlabel"] == "Curvature"
    assert result["ylabel"] == "Probability density"
    assert result["xunit"] == "{}⁻¹".format(unit)
    assert result["yunit"] == unit

    assert len(result["series"]) == 2

    s0, s1 = result["series"]

    exp_bins = np.array([-1.0 / 1500, 0, 1.0 / 1500])  # for curvatures
    exp_curvature_dist_values = [0, 1500, 0]

    assert s0["name"] == "Curvature distribution"

    np.testing.assert_almost_equal(s0["x"], exp_bins)
    np.testing.assert_almost_equal(s0["y"], exp_curvature_dist_values)

    assert s1["name"] == "Gaussian fit"
    # Not further testing gaussian here


def test_curvature_distribution_simple_2d_topography_periodic():
    unit = "nm"

    y = np.arange(100).reshape((1, -1))

    arr = np.sin(y / 2 / np.pi)  # only slope in y direction, second derivative is -sin

    t = Topography(arr, (100, 100), periodic=True, unit=unit).detrend("center")
    # resulting heights follow this function: h(x,y)=-2y+9

    topography = FakeTopographyModel(t)
    result = CurvatureDistribution(bins=3).topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_DIST_ANALYSIS

    assert result["name"] == "Curvature distribution"

    assert pytest.approx(result["scalars"]["Mean Curvature"]["value"]) == 0.0
    assert result["scalars"]["Mean Curvature"]["unit"] == "{}⁻¹".format(unit)


def test_power_spectrum_simple_2d_topography(simple_linear_2d_topography):
    unit = simple_linear_2d_topography.unit
    # resulting heights follow this function: h(x,y)=-2y+9

    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = PowerSpectralDensity().topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS

    assert result["name"] == "Power-spectral density (PSD)"

    assert result["xlabel"] == "Wavevector"
    assert result["ylabel"] == "PSD"
    assert result["xunit"] == "{}⁻¹".format(unit)
    assert result["yunit"] == "{}³".format(unit)

    assert len(result["series"]) == 6

    s0, s1, s2, s3, s4, s5 = result["series"]

    assert s0["name"] == "1D PSD along x"
    assert s1["name"] == "1D PSD along y"
    assert s2["name"] == "q/π × 2D PSD"
    assert s3["name"] == "1D PSD along x (incl. unreliable data)"
    assert s4["name"] == "1D PSD along y (incl. unreliable data)"
    assert s5["name"] == "q/π × 2D PSD (incl. unreliable data)"

    # TODO Also check values here as integration test?


def test_autocorrelation_simple_2d_topography(simple_linear_2d_topography):
    # resulting heights follow this function: h(x,y)=-2y+9
    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = Autocorrelation().topography_implementation(AnalysisResultMock(topography))

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS

    assert result["name"] == "Height-difference autocorrelation function (ACF)"

    # TODO Check result values for autocorrelation


def test_scale_dependent_slope_simple_2d_topography(simple_linear_2d_topography):
    # resulting heights follow this function: h(x,y)=-2y+9
    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = ScaleDependentSlope().topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS

    assert result["name"] == "Scale-dependent slope"
    for dataset in result["series"]:
        if dataset["name"] == "Along y":
            np.testing.assert_almost_equal(dataset["y"], 2 * np.ones_like(dataset["y"]))


def test_variable_bandwidth_simple_2d_topography(simple_linear_2d_topography):
    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = VariableBandwidth().topography_implementation(
        AnalysisResultMock(topography)
    )

    assert sorted(result.keys()) == EXPECTED_KEYS_FOR_PLOT_CARD_ANALYSIS

    assert result["name"] == "Variable-bandwidth analysis"
    # TODO Check result values for bandwidth


def test_roughness_parameters(simple_linear_2d_topography):
    unit = simple_linear_2d_topography.unit
    inverse_unit = "{}⁻¹".format(unit)
    topography = FakeTopographyModel(simple_linear_2d_topography)
    result = RoughnessParameters().topography_implementation(
        AnalysisResultMock(topography)
    )

    ureg = pint.UnitRegistry()
    ureg.formatter.default_format = "~P"

    expected = [
        {
            "quantity": "RMS height",
            "direction": "x",
            "from": "profile (1D)",
            "symbol": "Rq",
            "value": 0,
            "unit": unit,
        },
        {
            "quantity": "RMS height",
            "direction": "y",
            "from": "profile (1D)",
            "symbol": "Rq",
            "value": 5.74456264,
            "unit": unit,
        },
        {
            "quantity": "RMS height",
            "direction": None,
            "from": "area (2D)",
            "symbol": "Sq",
            "value": np.sqrt(33),
            "unit": unit,
        },
        {
            "quantity": "RMS curvature",
            "direction": "y",
            "from": "profile (1D)",
            "symbol": "",
            "value": 0,
            "unit": inverse_unit,
        },
        {
            "quantity": "RMS curvature",
            "direction": None,
            "from": "area (2D)",
            "symbol": "",
            "value": 0,
            "unit": inverse_unit,
        },
        {
            "quantity": "RMS curvature",
            "direction": "x",
            "from": "profile (1D)",
            "symbol": "",
            "value": 0,
            "unit": inverse_unit,
        },
        {
            "quantity": "RMS slope",
            "direction": "x",
            "from": "profile (1D)",
            "symbol": "R&Delta;q",
            "value": 0,
            "unit": 1,
        },
        {
            "quantity": "RMS slope",
            "direction": "y",
            "from": "profile (1D)",
            "symbol": "R&Delta;q",
            "value": 2,
            "unit": 1,
        },
        {
            "quantity": "RMS gradient",
            "direction": None,
            "from": "area (2D)",
            "symbol": "",
            "value": 2,
            "unit": 1,
        },
        {
            "quantity": "Bandwidth: lower bound",
            "direction": None,
            "from": "area (2D)",
            "symbol": "",
            "value": 1.0,
            "unit": unit,
        },
        {
            "quantity": "Bandwidth: upper bound",
            "direction": None,
            "from": "area (2D)",
            "symbol": "",
            "value": 7.5,
            "unit": unit,
        },
    ]

    # Look whether all fields are included
    assert len(result) == len(expected)

    # compare all fields in detail
    for exp, actual in zip(expected, result):
        assert_allclose(
            exp["value"],
            actual["value"],
            atol=1e-14,
            err_msg=f"Different values: exp: {exp}, actual: {actual}",
        )
        del exp["value"]
        del actual["value"]
        assert exp == actual


###############################################################################
# Testing analysis functions for surfaces
###############################################################################


@pytest.fixture
def simple_surface():
    class WrapTopography:
        def __init__(self, t):
            self._t = t

        def topography(self):
            return self._t

    class WrapRequest:
        def __init__(self, c):
            self._c = c

        def all(self):
            return self._c

    class WrapSurface:
        def __init__(self, c):
            self._c = c

        @property
        def topography_set(self):
            return WrapRequest(self._c)

    nx, ny = 113, 123
    sx, sy = 1, 1
    lx = 0.3
    topographies = [
        Topography(
            np.resize(np.sin(np.arange(nx) * sx * 2 * np.pi / (nx * lx)), (nx, ny)),
            (sx, sy),
            periodic=False,
            unit="um",
        )
    ]

    nx = 278
    sx = 100
    lx = 2
    x = np.arange(nx) * sx / nx
    topographies += [NonuniformLineScan(x, np.cos(x * np.pi / lx), unit="nm")]

    return WrapSurface([WrapTopography(t) for t in topographies])


def test_psd_for_surface(simple_surface):
    """Testing PSD for an artificial surface."""

    result = PowerSpectralDensity(nb_points_per_decade=3).surface_implementation(
        AnalysisResultMock(simple_surface)
    )

    expected_result = {
        "name": "Power-spectral density (PSD)",
        "xlabel": "Wavevector",
        "ylabel": "PSD",
        "xunit": "nm⁻¹",
        "yunit": "nm³",
        "xscale": "log",
        "yscale": "log",
        "series": [
            {
                "name": "1D PSD along x",
                # This is a pure regression test
                "x": [
                    6.283185e-03,
                    1.503970e-02,
                    3.281944e-02,
                    6.922845e-02,
                    1.589340e-01,
                    3.147830e-01,
                    7.102774e-01,
                    1.576467e00,
                    3.436698e00,
                    7.409395e00,
                    1.380985e01,
                ],
                "y": [
                    8.380153e05,
                    1.444988e05,
                    9.826013e04,
                    3.596532e05,
                    5.352438e06,
                    1.219130e06,
                    2.709713e-08,
                    1.241935e00,
                    4.943693e-09,
                    4.544197e-13,
                    1.752703e-05,
                ],
            }
        ],
        "alerts": [],
    }

    for k in ["name", "xunit", "yunit", "xlabel", "ylabel", "xscale", "yscale"]:
        assert expected_result[k] == result[k]

    assert expected_result["series"][0]["name"] == result["series"][0]["name"]
    assert_allclose(
        expected_result["series"][0]["x"], result["series"][0]["x"], rtol=1e-6
    )
    assert_allclose(
        expected_result["series"][0]["y"], result["series"][0]["y"], rtol=1e-6
    )


def test_autocorrelation_for_surface(simple_surface):
    """Testing autocorrelation for an artificial surface."""

    result = Autocorrelation(nb_points_per_decade=3).surface_implementation(
        AnalysisResultMock(simple_surface)
    )

    expected_result = {
        "name": "Height-difference autocorrelation function (ACF)",
        "xlabel": "Distance",
        "ylabel": "ACF",
        "xunit": "nm",
        "yunit": "nm²",
        "xscale": "log",
        "yscale": "log",
        "series": [
            {
                "name": "Along x",
                # This is a pure regression test
                "x": [
                    3.237410e-01,
                    7.194245e-01,
                    1.492413,
                    3.247700,
                    8.111829,
                    1.683517e01,
                    3.496530e01,
                    7.431925e01,
                    1.592920e02,
                    3.451327e02,
                    7.345133e02,
                ],
                "y": [
                    6.372497e-02,
                    2.788402e-01,
                    7.872059e-01,
                    3.479716e-01,
                    2.909510e05,
                    4.353897e05,
                    2.104788e05,
                    2.454415e05,
                    5.123730e05,
                    4.951154e05,
                    5.092170e05,
                ],
            }
        ],
    }

    for k in ["name", "xunit", "yunit", "xlabel", "ylabel", "xscale", "yscale"]:
        assert expected_result[k] == result[k]

    assert expected_result["series"][0]["name"] == result["series"][0]["name"]
    assert_allclose(
        expected_result["series"][0]["x"], result["series"][0]["x"], rtol=1e-6
    )
    assert_allclose(
        expected_result["series"][0]["y"], result["series"][0]["y"], rtol=1e-6
    )


def test_variable_bandwidth_for_surface(simple_surface):
    """Testing variable bandwidth for an artificial surface."""

    result = VariableBandwidth().surface_implementation(
        AnalysisResultMock(simple_surface)
    )

    expected_result = {
        "name": "Variable-bandwidth analysis",
        "xlabel": "Bandwidth",
        "ylabel": "RMS height",
        "xunit": "nm",
        "yunit": "nm",
        "xscale": "log",
        "yscale": "log",
        "series": [
            {
                "name": "Profile decomposition along x",
                # This is a pure regression test
                "x": [
                    3.892199e-01,
                    7.784397e-01,
                    1.556879e00,
                    3.113759e00,
                    6.227518e00,
                    1.171622e01,
                    2.348236e01,
                    4.706498e01,
                    5.991179e01,
                    9.433142e01,
                    1.250000e02,
                    2.500000e02,
                    5.000000e02,
                    1.000000e03,
                ],
                "y": [
                    9.832030e-03,
                    3.501679e-02,
                    1.304232e-01,
                    4.237846e-01,
                    6.662862e-01,
                    6.774048e-01,
                    6.856179e-01,
                    6.874945e-01,
                    6.678760e02,
                    6.875201e-01,
                    7.008752e02,
                    7.070114e02,
                    7.081023e02,
                    7.085611e02,
                ],
            }
        ],
    }

    for k in ["name", "xunit", "yunit", "xlabel", "ylabel", "xscale", "yscale"]:
        assert expected_result[k] == result[k]

    assert expected_result["series"][0]["name"] == result["series"][0]["name"]
    assert_allclose(
        expected_result["series"][0]["x"], result["series"][0]["x"], rtol=1e-6
    )
    assert_allclose(
        expected_result["series"][0]["y"], result["series"][0]["y"], rtol=1e-6
    )


def test_scale_dependent_slope_for_surface(simple_surface):
    """Testing scale-dependent slope for an artificial surface."""

    result = ScaleDependentSlope(nb_points_per_decade=3).surface_implementation(
        AnalysisResultMock(simple_surface)
    )

    expected_result = {
        "name": "Scale-dependent slope",
        "xlabel": "Distance",
        "ylabel": "Slope",
        "xunit": "nm",
        "yunit": "1",
        "xscale": "log",
        "yscale": "log",
        "series": [
            {
                "name": "Slope in x-direction",
                # This is a pure regression test
                "x": [
                    0.464159,
                    1.0,
                    2.154435,
                    4.641589,
                    10.0,
                    21.544347,
                    46.415888,
                    100.0,
                    215.443469,
                    464.158883,
                ],
                "y": [
                    1.060357,
                    0.975031,
                    0.633874,
                    0.143609,
                    74.384165,
                    33.003073,
                    16.146693,
                    2.761759,
                    5.296848,
                    1.332137,
                ],
            }
        ],
    }

    for k in ["name", "xunit", "yunit", "xlabel", "ylabel", "xscale", "yscale"]:
        assert expected_result[k] == result[k]

    assert expected_result["series"][0]["name"] == result["series"][0]["name"]
    assert_allclose(
        expected_result["series"][0]["x"], result["series"][0]["x"], atol=1e-6
    )
    assert_allclose(
        expected_result["series"][0]["y"], result["series"][0]["y"], atol=1e-6
    )


@pytest.mark.django_db
def test_sync_analysis_functions():  # TODO move to main project
    # TODO this test has a problem: It's not independent from the available functions

    from django.core.management import call_command

    call_command("register_analysis_functions")

    available_funcs_names = list(
        x[0] for x in Workflow.objects.values_list("name")
    )

    expected_funcs_names = sorted(
        [
            "topobank_statistics.height_distribution",
            "topobank_statistics.slope_distribution",
            "topobank_statistics.curvature_distribution",
            "topobank_statistics.power_spectral_density",
            "topobank_statistics.autocorrelation",
            "topobank_statistics.variable_bandwidth",
            "topobank_statistics.roughness_parameters",
            "topobank_statistics.scale_dependent_slope",
            "topobank_statistics.scale_dependent_curvature",
        ]
    )

    assert len(expected_funcs_names) <= len(available_funcs_names)

    for efn in expected_funcs_names:
        assert efn in available_funcs_names

    #
    # Call should be idempotent
    #
    call_command("register_analysis_functions")
    assert len(available_funcs_names) == Workflow.objects.count()
