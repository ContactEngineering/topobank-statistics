from django.urls import path

from .workflows import APP_NAME, VIZ_ROUGHNESS_PARAMETERS
from .views import roughness_parameters_card_view

# App name determines the internal name space
app_name = APP_NAME
urlprefix = 'plugins/statistics/'
urlpatterns = [
    # GET
    # * Triggers analyses if not yet running
    # * Return state of analyses
    # * Return plot configuration for finished analyses
    path(
        f'card/{VIZ_ROUGHNESS_PARAMETERS}/<str:workflow>',
        view=roughness_parameters_card_view,
        name=f'card-{VIZ_ROUGHNESS_PARAMETERS}'
    ),
]
