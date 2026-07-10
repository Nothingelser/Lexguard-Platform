"""Inject tenant boundary (station) into each authenticated request."""

from django.shortcuts import redirect


class TenantIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.station = None
        request.tenant_read_only = False
        request.is_super_admin = False

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            if user.is_super_admin:
                request.is_super_admin = True
            elif user.is_commander:
                request.tenant_read_only = True
            elif user.station_id:
                request.station = user.station

        return self.get_response(request)


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user
            and user.is_authenticated
            and not user.is_super_admin
            and getattr(user, "must_change_password", False)
            and not request.path.startswith("/accounts/password-change/")
            and not request.path.startswith("/accounts/logout/")
        ):
            return redirect("accounts:password_change")
        return self.get_response(request)
