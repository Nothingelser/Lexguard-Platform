from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.stations.models import PoliceStation
from apps.suspects.models import Suspect


User = get_user_model()


class SuspectRegistrationTests(TestCase):
    def setUp(self):
        self.station = PoliceStation.objects.create(
            code="MSA-MVT",
            name="Mvita",
            region="Coast",
            county="Mombasa",
            sub_county="Mvita",
        )
        self.officer = User.objects.create_user(
            username="officer",
            password="demo1234",
            badge_number="OFF-001",
            role=User.Role.OFFICER,
            station=self.station,
        )
        self.commander = User.objects.create_user(
            username="commander",
            password="demo1234",
            badge_number="CMD-001",
            role=User.Role.COMMANDER,
        )

    def test_no_results_offers_registration_to_station_officer(self):
        self.client.force_login(self.officer)

        response = self.client.get(reverse("suspects:search"), {"q": "12345678"})

        self.assertContains(response, "No records found")
        self.assertContains(response, "Register New Suspect")
        self.assertContains(response, "national_id=12345678")

    def test_station_officer_can_register_global_suspect(self):
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse("suspects:create"),
            {
                "national_id": "12345678",
                "full_name": "Asha Mwinyi",
                "aliases": "AM",
                "date_of_birth": "",
                "notes": "Known identity record.",
            },
        )

        suspect = Suspect.objects.get(national_id="12345678")
        self.assertRedirects(response, reverse("suspects:profile", args=[suspect.pk]))
        self.assertEqual(suspect.full_name, "Asha Mwinyi")

    def test_commander_cannot_register_suspect(self):
        self.client.force_login(self.commander)

        response = self.client.get(reverse("suspects:create"))

        self.assertEqual(response.status_code, 403)
