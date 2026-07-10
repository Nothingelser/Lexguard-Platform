from django.db import models


class Suspect(models.Model):
    national_id = models.CharField(max_length=32, unique=True, db_index=True)
    full_name = models.CharField(max_length=128)
    aliases = models.CharField(max_length=256, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.national_id})"
