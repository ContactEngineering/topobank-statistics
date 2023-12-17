from importlib.metadata import version

from topobank.plugins import PluginConfig

__version__ = version("topobank-statistics")


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
        # TODO can this be done with signals?

        # noinspection PyUnresolvedReferences
        import topobank_statistics.functions
        # noinspection PyUnresolvedReferences
        import topobank_statistics.views
        # noinspection PyUnresolvedReferences
        import topobank_statistics.downloads
