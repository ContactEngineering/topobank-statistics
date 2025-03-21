from django.urls import reverse


def test_api():
    """Test API routes"""
    assert (
        reverse(
            "topobank_statistics:card-roughness-parameters", kwargs=dict(workflow="abc")
        )
        == "/plugins/statistics/card/roughness-parameters/abc"
    )
