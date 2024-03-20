from topobank.plugins import PluginConfig

from .version import __version__


class StatisticsPluginConfig(PluginConfig):
    default = True
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'topobank_statistics'
    verbose_name = "Statistical Analysis"

    class TopobankPluginMeta:
        name = "Statistical Analysis"
        version = __version__
        description = """
        Provides the following statistical analysis functions:
        - Height/Curvature/Slope Distribution
        - Autocorrelation
        - Power Spectrum
        - Roughness Parameters
        - Scale-dependent slope/curvature
        - Variable bandwidth
        """
        logo = "topobank_statistics/static/images/ce_logo.svg"
        restricted = False  # Accessible for all users, without permissions

    def ready(self):
        # make sure the functions are registered now
        import topobank_statistics.functions  # noqa: F401
        import topobank_statistics.views  # noqa: F401
        import topobank_statistics.downloads  # noqa: F401
