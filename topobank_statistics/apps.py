from importlib.metadata import version
__version__ = version("topobank-statistics")

try:
    from topobank.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use topobank 0.92.0 or above to use this plugin!")


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
        # compatibility = "topobank>=0.92.0"

    def ready(self):
        # make sure the functions are registered now
        # TODO can this be done with signals?

        # noinspection PyUnresolvedReferences
        import topobank_statistics.functions
        # noinspection PyUnresolvedReferences
        import topobank_statistics.views
        # noinspection PyUnresolvedReferences
        import topobank_statistics.downloads

