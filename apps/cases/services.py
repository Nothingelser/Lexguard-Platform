from apps.cases.models import AuditLog

from django.utils import timezone

from apps.cases.models import Case


def next_case_number(station):
    """
    Generate a station-scoped case number for the current year.

    Format: CR-<STATION>-YYYY-0001
    """
    year = timezone.now().year
    prefix = f"CR-{station.code}-{year}-"
    counter = (
        Case.objects.filter(station=station, case_number__startswith=prefix)
        .count()
        + 1
    )
    while True:
        case_number = f"{prefix}{counter:04d}"
        if not Case.objects.filter(station=station, case_number=case_number).exists():
            return case_number
        counter += 1


def log_audit(user, action, entity, entity_id, detail=""):
    AuditLog.objects.create(
        station=user.station,
        user=user,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        detail=detail,
    )
