from django.contrib import admin

from .models import PoliceStation


@admin.register(PoliceStation)
class PoliceStationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "region", "county", "sub_county", "is_active")
    list_filter = ("region", "county", "is_active")
    search_fields = ("code", "name", "county", "sub_county")
