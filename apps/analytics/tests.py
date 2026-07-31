from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.cases.models import Case
from apps.stations.models import PoliceStation
from apps.suspects.models import Suspect


User = get_user_model()


class CommanderDashboardTests(TestCase):
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
        Case.objects.create(
            station=self.station,
            case_number="CASE-001",
            title="Test case",
            crime_category="theft",
            location="Mvita",
            narrative="Test narrative",
            created_by=self.officer,
        )
        Suspect.objects.create(
            national_id="12345678",
            full_name="Asha Mwinyi",
            aliases="AM",
        )

    def test_commander_dashboard_is_separate_from_command_console(self):
        self.client.force_login(self.commander)

        home_response = self.client.get(reverse("dashboard"))
        command_response = self.client.get(reverse("command_dashboard"))

        self.assertEqual(home_response.status_code, 200)
        self.assertContains(home_response, "Commander Dashboard")
        self.assertContains(home_response, "Regional Oversight Surface")
        self.assertNotContains(home_response, "Cross-County MO Linkage Alerts")

        self.assertEqual(command_response.status_code, 200)
        self.assertContains(command_response, "Regional Command Console")
        self.assertContains(command_response, "Regional Geospatial Hotspots")
        self.assertContains(command_response, "Recent Suspect Spotlight")
        self.assertContains(command_response, "Full Suspect Directory")
        self.assertContains(command_response, "Asha Mwinyi")
