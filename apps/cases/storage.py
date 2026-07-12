from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils.text import slugify


@dataclass(frozen=True)
class SupabaseStorageConfig:
    url: str
    service_role_key: str
    bucket: str
    public: bool = True

    @property
    def upload_base(self) -> str:
        return f"{self.url.rstrip('/')}/storage/v1/object"

    @property
    def public_base(self) -> str:
        return f"{self.url.rstrip('/')}/storage/v1/object/public"


def get_storage_config() -> SupabaseStorageConfig | None:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        return None
    return SupabaseStorageConfig(
        url=settings.SUPABASE_URL,
        service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY,
        bucket=settings.SUPABASE_STORAGE_BUCKET,
        public=settings.SUPABASE_STORAGE_PUBLIC,
    )


def _safe_filename(filename: str) -> str:
    path = Path(filename)
    stem = slugify(path.stem) or "attachment"
    suffix = path.suffix.lower()
    return f"{stem}{suffix}"


def build_evidence_object_key(case, original_filename: str) -> str:
    safe_name = _safe_filename(original_filename)
    return f"cases/{case.station.code}/{case.case_number}/{safe_name}"


def upload_evidence_file(case, upload) -> str:
    config = get_storage_config()
    if not config:
        raise RuntimeError("Supabase storage is not configured.")

    object_key = build_evidence_object_key(case, upload.name)
    content_type = getattr(upload, "content_type", None) or mimetypes.guess_type(upload.name)[0] or "application/octet-stream"
    upload_url = f"{config.upload_base}/{config.bucket}/{quote(object_key, safe='/')}"

    request = Request(
        upload_url,
        data=upload.read(),
        method="POST",
        headers={
            "apikey": config.service_role_key,
            "Authorization": f"Bearer {config.service_role_key}",
            "Content-Type": content_type,
            "x-upsert": "false",
        },
    )

    try:
        with urlopen(request, timeout=60) as response:
            response.read()
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
        raise RuntimeError(f"Supabase upload failed: {message}") from exc
    except URLError as exc:
        raise RuntimeError(f"Supabase upload failed: {exc.reason}") from exc

    if config.public:
        return f"{config.public_base}/{config.bucket}/{quote(object_key, safe='/')}"
    return object_key


def is_public_storage_path(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")
