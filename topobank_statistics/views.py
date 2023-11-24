import math

from rest_framework.decorators import api_view
from rest_framework.response import Response

from trackstats.models import Metric

from topobank.usage_stats.utils import increase_statistics_by_date_and_object
from topobank.analysis.utils import round_to_significant_digits
from topobank.analysis.controller import AnalysisController

NUM_SIGNIFICANT_DIGITS_RMS_VALUES = 5


@api_view(['GET'])
def roughness_parameters_card_view(request, **kwargs):
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
                v = round_to_significant_digits(float(v), NUM_SIGNIFICANT_DIGITS_RMS_VALUES)
        return v

    controller = AnalysisController.from_request(request, **kwargs)

    #
    # for statistics, count views per function
    #
    increase_statistics_by_date_and_object(Metric.objects.ANALYSES_RESULTS_VIEW_COUNT, obj=controller.function)

    #
    # Trigger missing analyses
    #
    controller.trigger_missing_analyses()

    #
    # Filter only successful ones
    #
    analyses_success = controller.get(['su'], True)

    #
    # Basic context data
    #
    context = controller.get_context(request=request)

    data = []
    for analysis in analyses_success:
        analysis_result = analysis.result

        for d in analysis_result:
            d['value'] = _convert_value(d['value'])

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
    context['tableData'] = data

    #
    # Return context
    #
    return Response(context)
