from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseMediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("access_key", settings.SUPABASE_SERVICE_ROLE_KEY)
        kwargs.setdefault("secret_key", settings.SUPABASE_SERVICE_ROLE_KEY)
        kwargs.setdefault("bucket_name", settings.SUPABASE_STORAGE_BUCKET)
        kwargs.setdefault("endpoint_url", f"{settings.SUPABASE_URL}/storage/v1/s3")
        kwargs.setdefault("region_name", "auto")
        kwargs.setdefault("file_overwrite", False)
        kwargs.setdefault("default_acl", "public-read" if settings.SUPABASE_STORAGE_PUBLIC else "private")
        kwargs.setdefault("querystring_auth", not settings.SUPABASE_STORAGE_PUBLIC)
        super().__init__(*args, **kwargs)

    def url(self, name):
        if settings.SUPABASE_STORAGE_PUBLIC:
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{name}"
        return super().url(name)
