from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OFFICER = "officer", "Station Officer"
        COMMANDER = "commander", "Regional Commander"
        ADMIN = "admin", "System Administrator"

    badge_number = models.CharField(max_length=32, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OFFICER)
    must_change_password = models.BooleanField(default=False)
    station = models.ForeignKey(
        "stations.PoliceStation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="officers",
    )

    REQUIRED_FIELDS = ["email", "badge_number"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.badge_number})"

    @property
    def is_commander(self):
        return self.role in {self.Role.COMMANDER, self.Role.ADMIN}

    @property
    def is_station_officer(self):
        return self.role == self.Role.OFFICER

    @property
    def is_super_admin(self):
        return self.role == self.Role.ADMIN
