import pytest
from topobank.testing.factories import OrganizationFactory, UserFactory
from topobank.testing.fixtures import api_rf  # noqa: F401
from topobank.testing.fixtures import handle_usage_statistics  # noqa: F401
from topobank.testing.fixtures import sync_analysis_functions  # noqa: F401
from topobank.testing.fixtures import two_topos  # noqa: F401


@pytest.fixture
def user_with_plugin(db, sync_analysis_functions):  # noqa: F811
    org_name = "Test Organization"
    org = OrganizationFactory(name=org_name, plugins_available=["topobank_statistics"])
    user = UserFactory()
    user.groups.add(org.group)
    return user
