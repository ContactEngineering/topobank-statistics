import pytest

from topobank.testing.fixtures import (
    api_rf,
    handle_usage_statistics,
    sync_analysis_functions,
    two_topos,
)  # noqa: F401
from topobank.testing.factories import UserFactory, OrganizationFactory


@pytest.mark.django_db
@pytest.fixture
def user_with_plugin(sync_analysis_functions):  # noqa: F811
    org_name = "Test Organization"
    org = OrganizationFactory(name=org_name, plugins_available="topobank_statistics")
    user = UserFactory()
    user.groups.add(org.group)
    return user
