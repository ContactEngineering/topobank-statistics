"""
Making urls from topobank available for tests.
"""

from django.urls import include, path

urlpatterns = [
    path(
        "files/",
        include("topobank.files.urls", namespace="files"),
    ),
    path(
        "users/",
        include("topobank.users.urls", namespace="users"),
    ),
    path(
        "manager/",
        include("topobank.manager.urls", namespace="manager"),
    ),
    path(
        "analysis/",
        include("topobank.analysis.urls", namespace="analysis"),
    ),
]
