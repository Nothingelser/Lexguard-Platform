from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from apps.stations.models import PoliceStation


@login_required
def station_registry(request):
    stations = PoliceStation.objects.filter(is_active=True).order_by("county", "sub_county", "name")
    by_county = {}
    for station in stations:
        by_county.setdefault(station.county, []).append(station)

    county_stats = (
        PoliceStation.objects.filter(is_active=True)
        .values("county")
        .annotate(count=Count("id"))
        .order_by("county")
    )

    return render(
        request,
        "stations/registry.html",
        {
            "by_county": by_county,
            "county_stats": county_stats,
            "total_stations": stations.count(),
            "region": "Coast",
        },
    )
