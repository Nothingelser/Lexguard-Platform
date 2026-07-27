from django import template

register = template.Library()


def _humanize_codename(codename):
    parts = codename.split("_")
    if not parts:
        return codename
    if parts[0] in {"add", "change", "delete", "view"} and len(parts) > 1:
        action = parts[0].capitalize()
        target = " ".join(piece.capitalize() for piece in parts[1:])
        return f"{action} {target}"
    return " ".join(piece.capitalize() for piece in parts)


@register.filter
def permission_label(permission):
    """
    Turn Django permission objects or permission strings into readable labels.

    Examples:
    - cases.add_case -> Add Case
    - analytics.view_alert -> View Alert
    """
    if not permission:
        return ""

    if isinstance(permission, str):
        if "." in permission:
            _app_label, codename = permission.split(".", 1)
            return _humanize_codename(codename)
        return _humanize_codename(permission)

    codename = getattr(permission, "codename", "")
    if codename:
        return _humanize_codename(codename)

    name = getattr(permission, "name", "")
    if name:
        return name
    return str(permission)


@register.filter
def permission_scope(permission):
    """
    Show a friendly permission scope from the app label.
    """
    if not permission:
        return ""
    content_type = getattr(permission, "content_type", None)
    if content_type is None:
        return ""
    app_label = getattr(content_type, "app_label", "")
    return app_label.replace("_", " ").title()


@register.filter
def permission_family(value):
    """
    Turn an app label or permission object into a command-friendly permission area.
    """
    if not value:
        return "Other access"

    if hasattr(value, "content_type"):
        content_type = getattr(value, "content_type", None)
        app_label = getattr(content_type, "app_label", "") if content_type else ""
    else:
        app_label = str(value)

    family_map = {
        "cases": "Case actions",
        "stations": "Registry access",
        "suspects": "Suspect access",
        "analytics": "Analytics access",
        "auth": "Authentication access",
        "admin": "Admin access",
        "contenttypes": "System access",
        "sessions": "System access",
        "accounts": "Account access",
    }
    return family_map.get(app_label, f"{app_label.replace('_', ' ').title()} access" if app_label else "Other access")
