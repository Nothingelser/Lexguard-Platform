from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.cases.models import AuditLog
from apps.stations.models import PoliceStation


User = get_user_model()


class AuditTrailAccessTests(TestCase):
    def setUp(self):
        self.station = PoliceStation.objects.create(
            code="MSA-MVT",
            name="Mvita",
            region="Coast",
            county="Mombasa",
            sub_county="Mvita",
        )
        self.commander = User.objects.create_user(
            username="commander",
            password="demo1234",
            badge_number="CMD-001",
            role=User.Role.COMMANDER,
        )
        self.officer = User.objects.create_user(
            username="officer",
            password="demo1234",
            badge_number="OFF-001",
            role=User.Role.OFFICER,
            station=self.station,
        )
        AuditLog.objects.create(
            station=self.station,
            user=self.officer,
            action="create",
            entity="case",
            entity_id="1",
            detail="Created case",
        )

    def test_station_officer_cannot_open_audit_trail(self):
        self.client.force_login(self.officer)

        response = self.client.get(reverse("cases:audit"))

        self.assertEqual(response.status_code, 403)

    def test_commander_can_open_audit_trail(self):
        self.client.force_login(self.commander)

        response = self.client.get(reverse("cases:audit"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audit Trail")