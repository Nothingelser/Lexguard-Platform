from django import template

from apps.cases.models import MOTagOption

register = template.Library()

STATUS_STYLES = {
    "open": "badge-open",
    "investigating": "badge-investigating",
    "closed": "badge-closed",
}

CATEGORY_STYLES = {
    "theft": "badge-theft",
    "assault": "badge-assault",
    "robbery": "badge-robbery",
    "fraud": "badge-fraud",
    "cyber": "badge-cyber",
    "other": "badge-other",
}


@register.simple_tag
def mo_label(category, value):
    option = MOTagOption.objects.filter(category=category, value=value).first()
    return option.label if option else value.replace("_", " ").title()


@register.inclusion_tag("components/status_badge.html")
def status_badge(status, label=None):
    from apps.cases.models import CaseStatus

    if not label:
        label = dict(CaseStatus.choices).get(status, status)
    return {"status": status, "label": label, "style": STATUS_STYLES.get(status, "badge-other")}


@register.inclusion_tag("components/category_badge.html")
def category_badge(category, label=None):
    from apps.cases.models import CrimeCategory

    if not label:
        label = dict(CrimeCategory.choices).get(category, category)
    return {"category": category, "label": label, "style": CATEGORY_STYLES.get(category, "badge-other")}
