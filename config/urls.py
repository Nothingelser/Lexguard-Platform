"""URL configuration for LexGuard Platform."""

import config.admin  # noqa: F401 — LexGuard admin branding
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import include, path
from django.urls import re_path

from apps.analytics.views import command_dashboard
from config.views import home, static_asset, legal_terms, legal_privacy, legal_license

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("cases/", include("apps.cases.urls")),
    path("stations/", include("apps.stations.urls")),
    path("suspects/", include("apps.suspects.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("", home, name="dashboard"),
    path("command/", command_dashboard, name="command_dashboard"),
    path("legal/terms/", legal_terms, name="legal_terms"),
    path("legal/privacy/", legal_privacy, name="legal_privacy"),
    path("legal/license/", legal_license, name="legal_license"),
]

if not settings.USE_MANIFEST_STATICFILES:
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", static_asset),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
