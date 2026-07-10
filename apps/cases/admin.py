from django.contrib import admin

from .models import AuditLog, Case, CaseSuspect, EvidenceItem, MOTagOption, Witness


class CaseSuspectInline(admin.TabularInline):
    model = CaseSuspect
    extra = 0


class WitnessInline(admin.TabularInline):
    model = Witness
    extra = 0


class EvidenceInline(admin.TabularInline):
    model = EvidenceItem
    extra = 0


@admin.register(MOTagOption)
class MOTagOptionAdmin(admin.ModelAdmin):
    list_display = ("category", "label", "value", "weight", "is_active")
    list_filter = ("category", "is_active")


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "title", "station", "crime_category", "status", "opened_at")
    list_filter = ("station", "crime_category", "status")
    search_fields = ("case_number", "title", "location")
    inlines = [CaseSuspectInline, WitnessInline, EvidenceInline]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity", "station", "user", "created_at")
    list_filter = ("action", "station")
