from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class SupabaseMediaStorage(S3Boto3Storage):
    """
    Supabase Storage via its S3-compatible API.
    Requires in settings/env:
      SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_STORAGE_BUCKET
    """
    access_key = settings.SUPABASE_SERVICE_ROLE_KEY
    secret_key = settings.SUPABASE_SERVICE_ROLE_KEY  # Supabase uses the same key for both
    bucket_name = settings.SUPABASE_STORAGE_BUCKET
    endpoint_url = f"{settings.SUPABASE_URL}/storage/v1/s3"
    region_name = "auto"
    file_overwrite = False
    default_acl = "public-read" if settings.SUPABASE_STORAGE_PUBLIC else "private"
    custom_domain = None
    querystring_auth = not settings.SUPABASE_STORAGE_PUBLIC

    def url(self, name):
        """Return the public Supabase Storage URL directly."""
        if settings.SUPABASE_STORAGE_PUBLIC:
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket_name}/{name}"
        return super().url(name)
