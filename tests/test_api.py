import pytest
from django.urls import reverse


@pytest.mark.urls("test_urls")
def test_api():
    """Test API routes"""
    assert (
        reverse(
            "topobank_statistics:card-roughness-parameters", kwargs=dict(workflow="abc")
        )
        == "/plugins/statistics/card/roughness-parameters/abc"
    )
