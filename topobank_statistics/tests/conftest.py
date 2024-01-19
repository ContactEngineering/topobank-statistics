import pytest

from topobank.fixtures import api_rf, handle_usage_statistics, sync_analysis_functions  # noqa: F401
from topobank.manager.tests.utils import two_topos  # noqa: F401
from topobank.organizations.tests.utils import OrganizationFactory
from topobank.users.tests.factories import UserFactory


@pytest.mark.django_db
@pytest.fixture
def user_with_plugin(sync_analysis_functions):  # noqa: F811
    org_name = "Test Organization"
    org = OrganizationFactory(name=org_name, plugins_available="topobank_statistics")
    user = UserFactory()
    user.groups.add(org.group)
    return user
