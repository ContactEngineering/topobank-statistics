from django.apps import AppConfig


class StatisticsAppConfig(AppConfig):
    default = True
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'topobank_statistics'
    verbose_name = "Statistical Analysis"

    def ready(self):
        # make sure the functions are registered now
        import topobank_statistics.views  # noqa: F401
        import topobank_statistics.workflows  # noqa: F401
