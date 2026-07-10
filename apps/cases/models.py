from django.conf import settings
from django.db import models


class CrimeCategory(models.TextChoices):
    THEFT = "theft", "Theft"
    ASSAULT = "assault", "Assault"
    ROBBERY = "robbery", "Robbery"
    FRAUD = "fraud", "Fraud"
    CYBER = "cyber", "Cybercrime"
    OTHER = "other", "Other"


class CaseStatus(models.TextChoices):
    OPEN = "open", "Open"
    INVESTIGATING = "investigating", "Under Investigation"
    CLOSED = "closed", "Closed"


class MOTagOption(models.Model):
    """Predefined modus operandi tags with deterministic match weights."""

    class Category(models.TextChoices):
        TARGET = "target", "Target Type"
        ENTRY = "entry", "Entry Method"
        WEAPON = "weapon", "Weapon Class"
        TIMEFRAME = "timeframe", "Timeframe"
        ESCAPE = "escape", "Escape Method"

    category = models.CharField(max_length=32, choices=Category.choices)
    value = models.CharField(max_length=64)
    label = models.CharField(max_length=128)
    weight = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("category", "value")]
        ordering = ["category", "label"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.label}"


class Case(models.Model):
    station = models.ForeignKey("stations.PoliceStation", on_delete=models.PROTECT, related_name="cases")
    case_number = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    crime_category = models.CharField(max_length=32, choices=CrimeCategory.choices)
    location = models.CharField(max_length=256)
    narrative = models.TextField()
    status = models.CharField(max_length=20, choices=CaseStatus.choices, default=CaseStatus.OPEN)
    modus_operandi = models.JSONField(default=dict, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cases_created",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("station", "case_number")]
        ordering = ["-opened_at"]

    def __str__(self):
        return f"{self.case_number} — {self.title}"


class CaseSuspect(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="case_suspects")
    suspect = models.ForeignKey("suspects.Suspect", on_delete=models.PROTECT, related_name="case_links")
    role = models.CharField(max_length=64, default="suspect")
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [("case", "suspect")]


class Witness(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="witnesses")
    full_name = models.CharField(max_length=128)
    contact = models.CharField(max_length=128, blank=True)
    statement = models.TextField(blank=True)


class EvidenceItem(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="evidence_items")
    label = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    storage_path = models.CharField(max_length=512, blank=True)


class AuditLog(models.Model):
    station = models.ForeignKey("stations.PoliceStation", on_delete=models.CASCADE, related_name="audit_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=64)
    entity = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=64)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
