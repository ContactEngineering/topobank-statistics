pytest_plugins = "topobank.fixtures"

import pytest

from topobank.manager.tests.utils import UserFactory
from topobank.organizations.tests.utils import OrganizationFactory


@pytest.mark.django_db
@pytest.fixture
def user_with_plugin():
    org_name = "Test Organization"
    org = OrganizationFactory(name=org_name, plugins_available="topobank_statistics")
    user = UserFactory()
    user.groups.add(org.group)
    return user

