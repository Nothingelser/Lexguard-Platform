from django.contrib import admin

from .models import Suspect


@admin.register(Suspect)
class SuspectAdmin(admin.ModelAdmin):
    list_display = ("national_id", "full_name", "date_of_birth", "updated_at")
    search_fields = ("national_id", "full_name", "aliases")
