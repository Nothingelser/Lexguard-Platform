"""LexGuard Django admin branding, dashboard stats, and layout configuration."""

from datetime import timedelta

from django.contrib.admin import AdminSite
from django.contrib import admin
from django.utils import timezone

APP_SECTION_META = {
    "accounts": {
        "order": 0,
        "title": "Personnel & Access",
        "subtitle": "Roles, badges, provisioning, and account locks",
        "icon": "personnel",
    },
    "cases": {
        "order": 1,
        "title": "Investigations",
        "subtitle": "Case files, evidence, MO tags, and audit logs",
        "icon": "cases",
    },
    "suspects": {
        "order": 2,
        "title": "Suspect Registry",
        "subtitle": "Profiles, identifiers, and cross-case links",
        "icon": "suspects",
    },
    "stations": {
        "order": 3,
        "title": "Station Network",
        "subtitle": "Regional stations, codes, and activation status",
        "icon": "stations",
    },
    "auth": {
        "order": 4,
        "title": "System Groups",
        "subtitle": "Django auth groups and permissions",
        "icon": "system",
    },
}


def _build_dashboard_stats():
    from apps.accounts.models import User
    from apps.cases.models import AuditLog, Case, CaseStatus
    from apps.stations.models import PoliceStation
    from apps.suspects.models import Suspect

    week_ago = timezone.now() - timedelta(days=7)
    open_statuses = {CaseStatus.OPEN, CaseStatus.INVESTIGATING}

    return [
        {
            "key": "personnel",
            "label": "Active personnel",
            "value": User.objects.filter(is_active=True).count(),
            "hint": "Staff accounts currently enabled",
            "url_name": "admin:accounts_user_changelist",
        },
        {
            "key": "cases",
            "label": "Open investigations",
            "value": Case.objects.filter(status__in=open_statuses).count(),
            "hint": "Cases open or under investigation",
            "url_name": "admin:cases_case_changelist",
        },
        {
            "key": "stations",
            "label": "Active stations",
            "value": PoliceStation.objects.filter(is_active=True).count(),
            "hint": "Stations available in the field network",
            "url_name": "admin:stations_policestation_changelist",
        },
        {
            "key": "suspects",
            "label": "Suspect profiles",
            "value": Suspect.objects.count(),
            "hint": "Registered suspect records",
            "url_name": "admin:suspects_suspect_changelist",
        },
        {
            "key": "audit",
            "label": "Audit events (7d)",
            "value": AuditLog.objects.filter(created_at__gte=week_ago).count(),
            "hint": "Logged actions in the last seven days",
            "url_name": "admin:cases_auditlog_changelist",
        },
    ]


def _prepare_app_list(app_list):
    enriched = []
    for app in app_list:
        meta = APP_SECTION_META.get(app["app_label"], {})
        enriched.append(
            {
                **app,
                "section_title": meta.get("title", app["name"]),
                "section_subtitle": meta.get("subtitle", "Registered models and records"),
                "section_icon": meta.get("icon", "system"),
                "section_order": meta.get("order", 99),
            }
        )
    enriched.sort(key=lambda item: (item["section_order"], item["name"].lower()))
    return enriched


_original_index = AdminSite.index


def lexguard_admin_index(self, request, extra_context=None):
    app_list = _prepare_app_list(self.get_app_list(request))
    context = {
        **(extra_context or {}),
        "app_list": app_list,
        "dashboard_stats": _build_dashboard_stats(),
    }
    return _original_index(self, request, context)


AdminSite.index = lexguard_admin_index

admin.site.site_header = "LexGuard Command Console"
admin.site.site_title = "LexGuard Admin"
admin.site.index_title = "Operations Dashboard"
admin.site.login_template = "admin/login.html"
