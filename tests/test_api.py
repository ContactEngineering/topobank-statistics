from django.urls import reverse


def test_api():
    """Test API routes"""
    assert reverse('topobank_statistics:card-roughness-parameters',
                   kwargs=dict(function_id=123)) == '/plugins/statistics/card/roughness-parameters/123'
