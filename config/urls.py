"""URL configuration for LexGuard Platform."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.urls import re_path

from apps.analytics.views import command_dashboard
from config.views import home, static_asset

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("cases/", include("apps.cases.urls")),
    path("stations/", include("apps.stations.urls")),
    path("suspects/", include("apps.suspects.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("", home, name="dashboard"),
    path("command/", command_dashboard, name="command_dashboard"),
]

if not settings.USE_MANIFEST_STATICFILES:
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", static_asset),
    ]
