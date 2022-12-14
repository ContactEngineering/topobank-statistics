from django.urls import path, re_path
from django.contrib.auth.decorators import login_required

from .views import ExampleView

app_name = "statistics"
urlpatterns = [
    # Define extra urls here
    path(
        'example',  # just as example, will be accessible as 'plugins/topobank_statistics/example'
        view=login_required(ExampleView.as_view()),
        name='example'
    ),
]
