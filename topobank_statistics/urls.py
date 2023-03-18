from django.urls import path
from django.contrib.auth.decorators import login_required

from .functions import APP_NAME, VIZ_ROUGHNESS_PARAMETERS
from .views import roughness_parameters_card_view

# App name determines the internal name space, e.g. example can be references
# as 'statistics:example'
app_name = APP_NAME
urlpatterns = [
    # POST
    # * Triggers analyses if not yet running
    # * Return state of analyses
    # * Return plot configuration for finished analyses
    # This is a post request because the request parameters are complex.
    path(
        f'card/{VIZ_ROUGHNESS_PARAMETERS}',
        view=login_required(roughness_parameters_card_view),
        name=f'card-{VIZ_ROUGHNESS_PARAMETERS}'
    ),
]
