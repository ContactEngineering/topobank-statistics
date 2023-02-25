import math

from django.views.generic import TemplateView

from topobank.analysis.utils import round_to_significant_digits
#from topobank.analysis.views import SimpleCardView
from topobank.analysis.registry import register_card_view_class

from .functions import ART_ROUGHNESS_PARAMETERS

NUM_SIGNIFICANT_DIGITS_RMS_VALUES = 5


@register_card_view_class(ART_ROUGHNESS_PARAMETERS)
#class RoughnessParametersCardView(SimpleCardView):

class RoughnessParametersCardView:
    template_name_pattern = "topobank_statistics/roughnessparameters_card_{template_flavor}.html"

    @staticmethod
    def _convert_value(v):
        if v is not None:
            if math.isnan(v):
                v = None  # will be interpreted as null in JS, replace there with NaN!
                # It's not easy to pass NaN as JSON:
                # https://stackoverflow.com/questions/15228651/how-to-parse-json-string-containing-nan-in-node-js
            elif math.isinf(v):
                return 'infinity'
            else:
                # convert float32 to float, round to fixed number of significant digits
                v = round_to_significant_digits(float(v),
                                                NUM_SIGNIFICANT_DIGITS_RMS_VALUES)
        return v

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        analyses_success = context['analyses_success']

        data = []
        for analysis in analyses_success:
            analysis_result = analysis.result

            for d in analysis_result:
                d['value'] = self._convert_value(d['value'])

                if not d['direction']:
                    d['direction'] = ''
                if not d['from']:
                    d['from'] = ''
                if not d['symbol']:
                    d['symbol'] = ''

                # put topography in every line
                topo = analysis.subject
                d.update(dict(topography_name=topo.name,
                              topography_url=topo.get_absolute_url()))

            data.extend(analysis_result)

        #
        # find out all existing keys while keeping order
        #
        all_keys = []
        for d in data:
            for k in d.keys():
                if k not in all_keys:
                    all_keys.append(k)

        #
        # make sure every dict has all keys
        #
        for k in all_keys:
            for d in data:
                d.setdefault(k)

        #
        # create table
        #
        context.update(dict(
            table_data=data
        ))

        return context


class ExampleView(TemplateView):
    template_name = "topobank_statistics/example.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .apps import __version__ as version
        context['plugin_version'] = version
        return context
