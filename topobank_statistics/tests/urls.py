"""
Making urls from topobank available for tests.
"""
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from topobank.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path(
        "manager/",
        include("topobank.manager.urls", namespace="manager"),
    ),
    path(
        "analysis/",
        include("topobank.analysis.urls", namespace="analysis"),
    ),
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)
