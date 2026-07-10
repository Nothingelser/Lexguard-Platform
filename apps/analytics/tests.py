from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.cases.models import Case
from apps.stations.models import PoliceStation


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

    def test_commander_dashboard_is_separate_from_command_console(self):
        self.client.force_login(self.commander)

        home_response = self.client.get(reverse("dashboard"))
        command_response = self.client.get(reverse("command_dashboard"))

        self.assertEqual(home_response.status_code, 200)
        self.assertContains(home_response, "Commander Dashboard")
        self.assertContains(home_response, "Commander Home")
        self.assertNotContains(home_response, "Regional Command Console")

        self.assertEqual(command_response.status_code, 200)
        self.assertContains(command_response, "Regional Command Console")
        self.assertNotContains(command_response, "Commander Home")
