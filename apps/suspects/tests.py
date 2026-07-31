from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
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

    def test_station_officer_can_register_suspect_with_photo(self):
        self.client.force_login(self.officer)

        png_bytes = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01"
            b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        photo = SimpleUploadedFile("suspect.png", png_bytes, content_type="image/png")

        response = self.client.post(
            reverse("suspects:create"),
            {
                "national_id": "87654321",
                "full_name": "Juma Ali",
                "aliases": "JA",
                "date_of_birth": "",
                "notes": "Has a mugshot on record.",
                "photo": photo,
            },
        )

        suspect = Suspect.objects.get(national_id="87654321")
        self.assertRedirects(response, reverse("suspects:profile", args=[suspect.pk]))
        self.assertTrue(suspect.photo.name.startswith("suspects/photos/"))
        profile_response = self.client.get(reverse("suspects:profile", args=[suspect.pk]))
        self.assertContains(profile_response, "Identity board")
        self.assertContains(profile_response, suspect.full_name)

    def test_commander_cannot_register_suspect(self):
        self.client.force_login(self.commander)

        response = self.client.get(reverse("suspects:create"))

        self.assertEqual(response.status_code, 403)
