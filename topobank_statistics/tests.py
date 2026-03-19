import pytest
from topobank.analysis.models import Workflow


@pytest.mark.django_db
def test_autoload_analysis_functions():
    from django.core.management import call_command

    import topobank_statistics.workflows  # noqa: F401

    call_command('register_analysis_functions')

    # remember number of functions
    num_funcs = Workflow.objects.count()

    expected_funcs_names = sorted([
        'Height distribution',
        'Slope distribution',
        'Curvature distribution',
        'Power spectrum',
        'Autocorrelation',
        'Variable bandwidth',
        'Scale-dependent slope',
        'Scale-dependent curvature',
    ])

    assert len(expected_funcs_names) <= num_funcs

    available_funcs_names = Workflow.objects.values_list("display_name", flat=True)

    for efn in expected_funcs_names:
        assert efn in available_funcs_names

    #
    # Call should be idempotent
    #
    call_command('register_analysis_functions')
    assert num_funcs == Workflow.objects.count()
