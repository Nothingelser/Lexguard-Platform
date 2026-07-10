from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from apps.accounts.permissions import require_commander, require_station_officer
from apps.analytics.pattern_matcher import (
    category_breakdown,
    crime_distribution,
    find_pattern_matches,
    precinct_performance,
    regional_mo_alerts,
    subcounty_hotspots,
)
from apps.cases.models import AuditLog, Case


@login_required
def station_dashboard(request):
    import json

    if request.user.is_commander:
        return render(request, "command/dashboard.html", _command_context())

    if not require_station_officer(request.user):
        return HttpResponseForbidden("No station assigned.")

    cases = Case.objects.filter(station=request.user.station)
    open_cases = cases.exclude(status="closed").count()
    closed_cases = cases.filter(status="closed").count()
    total = open_cases + closed_cases
    backlog_pct = round((open_cases / total) * 100, 1) if total else 0
    recent = cases.order_by("-opened_at")[:5]
    activity = AuditLog.objects.filter(station=request.user.station).select_related("user")[:8]
    categories = list(category_breakdown(station_id=request.user.station_id))

    return render(
        request,
        "station/dashboard.html",
        {
            "station": request.user.station,
            "open_cases": open_cases,
            "closed_cases": closed_cases,
            "total_cases": total,
            "backlog_pct": backlog_pct,
            "recent_cases": recent,
            "activity": activity,
            "category_json": json.dumps({c["crime_category"]: c["count"] for c in categories}),
        },
    )


def _command_context():
    import json

    from apps.cases.models import Case as CaseModel

    performance = precinct_performance()
    distribution = list(crime_distribution())
    county_totals = {}
    for row in distribution:
        county = row["station__county"]
        county_totals[county] = county_totals.get(county, 0) + row["count"]

    alerts = regional_mo_alerts()
    hotspots = list(subcounty_hotspots()[:12])
    max_hotspot = hotspots[0]["count"] if hotspots else 1

    subcounty_totals = {}
    for row in subcounty_hotspots():
        label = row["station__sub_county"] or "Unspecified"
        subcounty_totals[label] = subcounty_totals.get(label, 0) + row["count"]

    return {
        "performance": performance,
        "distribution": distribution,
        "county_totals": county_totals,
        "county_totals_json": json.dumps(county_totals),
        "subcounty_totals_json": json.dumps(subcounty_totals),
        "total_cases": CaseModel.objects.count(),
        "open_cases": CaseModel.objects.exclude(status="closed").count(),
        "station_count": len(performance),
        "county_count": len(county_totals),
        "region_name": "Coast",
        "alert_count": len(alerts),
        "top_alerts": alerts[:5],
        "hotspots": hotspots,
        "max_hotspot": max_hotspot,
    }


@login_required
def commander_dashboard(request):
    if not require_commander(request.user):
        return HttpResponseForbidden("Command access only.")

    recent_cases = (
        Case.objects.select_related("station")
        .order_by("-opened_at")[:8]
    )
    open_cases = Case.objects.exclude(status="closed").count()
    closed_cases = Case.objects.filter(status="closed").count()
    county_pressure = (
        Case.objects.values("station__county")
        .annotate(count=Count("id"))
        .order_by("-count", "station__county")[:5]
    )
    max_count = county_pressure[0]["count"] if county_pressure else 1
    recent_alerts = regional_mo_alerts(limit=6)

    return render(
        request,
        "command/home.html",
        {
            "region_name": "Coast",
            "total_cases": Case.objects.count(),
            "open_cases": open_cases,
            "closed_cases": closed_cases,
            "recent_cases": recent_cases,
            "county_pressure": county_pressure,
            "max_count": max_count,
            "recent_alerts": recent_alerts,
            "command_console_url": "command_dashboard",
        },
    )


@login_required
def command_dashboard(request):
    if not require_commander(request.user):
        return HttpResponseForbidden("Command access only.")
    return render(request, "command/dashboard.html", _command_context())


@login_required
def regional_alerts(request):
    if not require_commander(request.user):
        return HttpResponseForbidden("Command access only.")
    return render(
        request,
        "analytics/alerts.html",
        {"alerts": regional_mo_alerts(min_score=3, limit=50)},
    )


@login_required
def pattern_match(request, pk):
    if not require_commander(request.user):
        return HttpResponseForbidden("Command access only.")

    case = get_object_or_404(Case.objects.select_related("station"), pk=pk)
    matches = find_pattern_matches(case)
    template = "analytics/partials/match_results.html" if request.htmx else "analytics/pattern_match.html"
    return render(request, template, {"case": case, "matches": matches})


@login_required
def export_csv(request):
    if not require_commander(request.user):
        return HttpResponseForbidden("Command access only.")

    import csv

    performance = precinct_performance()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="lexguard-precinct-report.csv"'
    writer = csv.writer(response)
    writer.writerow(["Station Code", "Station Name", "County", "Open", "Closed", "Closure Rate %", "Avg Resolution Days"])
    for row in performance:
        writer.writerow([
            row["station"].code,
            row["station"].name,
            row["station"].county,
            row["open"],
            row["closed"],
            row["closure_rate"],
            row["avg_resolution_days"] or "",
        ])
    return response


@login_required
def export_excel(request):
    if not require_commander(request.user):
        return HttpResponseForbidden("Command access only.")

    from apps.analytics.exports import build_precinct_workbook

    data = build_precinct_workbook()
    response = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="lexguard-regional-report.xlsx"'
    return response
