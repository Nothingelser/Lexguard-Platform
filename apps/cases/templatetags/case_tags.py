from pathlib import Path
from urllib.parse import urlparse
import mimetypes

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


@register.simple_tag
def evidence_filename(path):
    if not path:
        return "Evidence file"
    parsed = urlparse(path)
    name = Path(parsed.path).name or "Evidence file"
    return name


@register.simple_tag
def evidence_kind(path):
    if not path:
        return "file"
    parsed = urlparse(path)
    filename = Path(parsed.path).name
    content_type, _encoding = mimetypes.guess_type(filename)
    if content_type:
        if content_type.startswith("image/"):
            return "image"
        if content_type.startswith("video/"):
            return "video"
        if content_type.startswith("audio/"):
            return "audio"
    suffix = Path(filename).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}:
        return "image"
    if suffix in {".mp4", ".mov", ".webm", ".mkv", ".avi"}:
        return "video"
    if suffix in {".mp3", ".wav", ".m4a", ".ogg", ".flac"}:
        return "audio"
    return "file"


@register.simple_tag
def evidence_type_label(path):
    kind = evidence_kind(path)
    return {
        "image": "Image",
        "video": "Video",
        "audio": "Audio",
        "file": "File",
    }.get(kind, "File")


@register.simple_tag
def human_size(bytes_value):
    if bytes_value in (None, ""):
        return ""
    try:
        value = float(bytes_value)
    except (TypeError, ValueError):
        return ""
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return ""
