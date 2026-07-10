from django.db import models


class PoliceStation(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=128)
    region = models.CharField(max_length=64)
    county = models.CharField(max_length=64)
    sub_county = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["region", "county", "name"]

    def __str__(self):
        return f"{self.code} — {self.name}"
