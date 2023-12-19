"""
Making urls from topobank available for tests.
"""

from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path(
        "manager/",
        include("topobank.manager.urls", namespace="manager"),
    ),
    path(
        "users/",
        include("topobank.users.urls", namespace="users"),
    ),
    path(
        "analysis/",
        include("topobank.analysis.urls", namespace="analysis"),
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
