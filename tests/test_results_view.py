import tempfile

import numpy as np
import openpyxl
import pytest
from topobank.analysis.models import Workflow
from topobank.manager.utils import subjects_to_base64
from topobank.testing.factories import (SurfaceFactory, Topography2DFactory,
                                        TopographyAnalysisFactory)

from topobank_statistics.views import (NUM_SIGNIFICANT_DIGITS_RMS_VALUES,
                                       roughness_parameters_card_view)


@pytest.mark.urls("test_urls")
@pytest.mark.parametrize("template_flavor", ["list", "detail"])
@pytest.mark.django_db
def test_roughness_params_rounded(
    api_rf, mocker, template_flavor, user_with_plugin, handle_usage_statistics, settings
):
    settings.DELETE_EXISTING_FILES = True

    def myfunc(*args, **kwargs):
        """Return some fake values for testing rounding"""
        return [
            {
                "quantity": "RMS Height",
                "direction": None,
                "from": "area (2D)",
                "symbol": "Sq",
                "value": np.float32(1.2345678),
                "unit": "m",
            },
            {
                "quantity": "RMS Height",
                "direction": "x",
                "from": "profile (1D)",
                "symbol": "Rq",
                "value": np.float32(8.7654321),
                "unit": "m",
            },
            {
                "quantity": "RMS Curvature",
                "direction": None,
                "from": "profile (1D)",
                "symbol": "",
                "value": np.float32(0.9),
                "unit": "1/m",
            },
            {
                "quantity": "RMS Slope",
                "direction": "x",
                "from": "profile (1D)",
                "symbol": "S&Delta;q",
                "value": np.float32(-1.56789),
                "unit": 1,
            },
            {
                "quantity": "RMS Slope",
                "direction": "y",
                "from": "profile (1D)",
                "symbol": "S&Delta;q",
                "value": np.float32("nan"),
                "unit": 1,
            },
        ]

    m = mocker.patch(
        "topobank.analysis.models.Workflow.eval",
        new_callable=mocker.PropertyMock,
    )
    m.return_value = myfunc

    surf = SurfaceFactory(created_by=user_with_plugin)
    topo = Topography2DFactory(size_x=1, size_y=1, surface=surf)

    func = Workflow.objects.get(name="topobank_statistics.roughness_parameters")
    TopographyAnalysisFactory(subject_topography=topo, function=func)

    request = api_rf.get(
        f"/plugins/statistics/card/roughness-parameters/{func.name}",
        {"workflow": func.name, "subjects": subjects_to_base64([topo])},
    )
    assert m.call_count == 1
    request.user = topo.surface.created_by
    request.session = {}

    response = roughness_parameters_card_view(request)
    assert response.status_code == 200

    # we want rounding to 5 digits
    assert NUM_SIGNIFICANT_DIGITS_RMS_VALUES == 5

    topo_url = topo.get_absolute_url()

    exp_table_data = [
        {
            "quantity": "RMS Height",
            "direction": "",
            "from": "area (2D)",
            "symbol": "Sq",
            "value": 1.2346,
            "unit": "m",
            "topography_name": topo.name,
            "topography_url": topo_url,
        },
        {
            "quantity": "RMS Height",
            "direction": "x",
            "from": "profile (1D)",
            "symbol": "Rq",
            "value": 8.7654,
            "unit": "m",
            "topography_name": topo.name,
            "topography_url": topo_url,
        },
        {
            "quantity": "RMS Curvature",
            "direction": "",
            "from": "profile (1D)",
            "symbol": "",
            "value": 0.9,
            "unit": "1/m",
            "topography_name": topo.name,
            "topography_url": topo_url,
        },
        {
            "quantity": "RMS Slope",
            "direction": "x",
            "from": "profile (1D)",
            "symbol": "S&Delta;q",
            "value": -1.5679,
            "unit": 1,
            "topography_name": topo.name,
            "topography_url": topo_url,
        },
        {
            "quantity": "RMS Slope",
            "direction": "y",
            "from": "profile (1D)",
            "symbol": "S&Delta;q",
            "value": None,
            "unit": 1,
            "topography_name": topo.name,
            "topography_url": topo_url,
        },
    ]

    assert response.data["tableData"] == exp_table_data

    #
    # We do not render response here, because this causes problems
    # when resolving static files from topobank package
    #
    # response.render()
    # assert b"1.2346" in response.content
    # assert b"8.7654" in response.content
    # assert b"0.9" in response.content
    # assert b"-1.5679" in response.content
    # assert b"NaN" in response.content
