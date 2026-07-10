from apps.cases.models import AuditLog


def log_audit(user, action, entity, entity_id, detail=""):
    AuditLog.objects.create(
        station=user.station,
        user=user,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        detail=detail,
    )
