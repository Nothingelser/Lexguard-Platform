from django.core.exceptions import PermissionDenied


def require_station_officer(user):
    if not user.is_authenticated:
        return False
    return user.is_station_officer and user.station_id is not None


def require_commander(user):
    if not user.is_authenticated:
        return False
    return user.is_commander


def can_add_case(user):
    if not user.is_authenticated:
        return False
    return bool(
        user.is_super_admin
        or user.is_station_officer
        or user.has_perm("cases.add_case")
    )


class TenantQuerySetMixin:
    """Restrict queryset to the officer's home station unless commander (read-only all)."""

    station_field = "station"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_commander:
            return qs
        if user.station_id:
            return qs.filter(**{self.station_field: user.station})
        return qs.none()


def enforce_write_access(request):
    if request.tenant_read_only:
        raise PermissionDenied("Command accounts have read-only access to station records.")
