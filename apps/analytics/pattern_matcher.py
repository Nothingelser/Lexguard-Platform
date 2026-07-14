"""Deterministic cross-precinct modus operandi pattern matching."""

from django.db.models import Count

from apps.cases.models import Case, MOTagOption


def _normalize_mo(payload):
    return payload if isinstance(payload, dict) else {}


def _tag_weights():
    weights = {}
    for option in MOTagOption.objects.filter(is_active=True):
        weights[(option.category, option.value)] = option.weight
    return weights


def score_case_pair(source: Case, candidate: Case, weights: dict | None = None) -> int:
    """Return weighted similarity score between two cases' MO tag sets."""
    if source.pk == candidate.pk:
        return 0
    if source.station_id == candidate.station_id:
        return 0

    weights = weights or _tag_weights()
    source_mo = _normalize_mo(getattr(source, "safe_modus_operandi", source.modus_operandi))
    candidate_mo = _normalize_mo(getattr(candidate, "safe_modus_operandi", candidate.modus_operandi))

    score = 0
    for category, value in source_mo.items():
        if candidate_mo.get(category) == value:
            score += weights.get((category, value), 1)
    return score


def find_pattern_matches(source_case: Case, min_score: int = 2, limit: int = 20):
    """Find cross-station cases with similar MO signatures."""
    weights = _tag_weights()
    matches = []
    candidates = (
        Case.objects.exclude(station=source_case.station)
        .select_related("station")
    )
    for candidate in candidates:
        if not _normalize_mo(getattr(candidate, "safe_modus_operandi", candidate.modus_operandi)):
            continue
        score = score_case_pair(source_case, candidate, weights)
        if score >= min_score:
            matches.append({"case": candidate, "score": score})

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:limit]


def regional_mo_alerts(min_score: int = 3, limit: int = 25):
    """Scan all open cases for cross-precinct MO linkages above a fixed threshold."""
    sources = (
        Case.objects.exclude(status="closed")
        .select_related("station")
    )
    alerts = []
    seen = set()

    for source in sources:
        if not _normalize_mo(getattr(source, "safe_modus_operandi", source.modus_operandi)):
            continue
        for match in find_pattern_matches(source, min_score=min_score, limit=5):
            pair = tuple(sorted([source.pk, match["case"].pk]))
            if pair in seen:
                continue
            seen.add(pair)
            alerts.append({"source": source, "target": match["case"], "score": match["score"]})

    alerts.sort(key=lambda item: item["score"], reverse=True)
    return alerts[:limit]


def subcounty_hotspots():
    """Aggregate case counts by sub-county for geospatial intensity mapping."""
    return (
        Case.objects.values("station__sub_county", "station__county", "crime_category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )


def category_breakdown(station_id=None):
    qs = Case.objects.all()
    if station_id:
        qs = qs.filter(station_id=station_id)
    return qs.values("crime_category").annotate(count=Count("id")).order_by("-count")


def precinct_performance():
    """Compute open/closed ratios and average resolution time per station."""
    from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q

    stats = []
    from apps.stations.models import PoliceStation

    for station in PoliceStation.objects.filter(is_active=True):
        cases = Case.objects.filter(station=station)
        total = cases.count()
        closed = cases.filter(status="closed").count()
        open_count = cases.exclude(status="closed").count()
        avg_days = (
            cases.filter(status="closed", closed_at__isnull=False)
            .annotate(
                duration=ExpressionWrapper(F("closed_at") - F("opened_at"), output_field=DurationField())
            )
            .aggregate(avg=Avg("duration"))["avg"]
        )
        stats.append(
            {
                "station": station,
                "total": total,
                "closed": closed,
                "open": open_count,
                "closure_rate": round((closed / total) * 100, 1) if total else 0,
                "avg_resolution_days": round(avg_days.total_seconds() / 86400, 1) if avg_days else None,
            }
        )
    return stats


def crime_distribution():
    from django.db.models import Count

    return (
        Case.objects.values("station__county", "crime_category")
        .annotate(count=Count("id"))
        .order_by("station__county", "crime_category")
    )
