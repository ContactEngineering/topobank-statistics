import pytest


@pytest.mark.django_db
def test_autoload_workflows():
    import topobank_statistics.workflows  # noqa: F401

    from topobank.analysis.registry import get_implementation, get_workflow_names

    available_display_names = [
        get_implementation(name=n).Meta.display_name for n in get_workflow_names()
    ]

    expected_display_names = [
        'Height distribution',
        'Slope distribution',
        'Curvature distribution',
        'Power spectrum',
        'Autocorrelation',
        'Variable bandwidth',
        'Scale-dependent slope',
        'Scale-dependent curvature',
    ]

    for name in expected_display_names:
        assert name in available_display_names
