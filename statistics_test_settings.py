from topobank.test_settings import *  # noqa: F401, F403

INSTALLED_APPS = INSTALLED_APPS + [  # noqa: F405
    "topobank_rest_api.apps.TopobankRestApiConfig",
    "topobank_statistics.apps.TopobankStatisticsAppConfig",
]

ROOT_URLCONF = "test_urls"
