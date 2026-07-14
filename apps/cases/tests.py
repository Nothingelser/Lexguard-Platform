from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.cases.models import AuditLog
from apps.cases.services import next_case_number
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


class CaseRegistrationAndExportTests(TestCase):
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
            badge_number="CST-MSA-MVT-0001",
            role=User.Role.OFFICER,
            station=self.station,
        )

    def test_next_case_number_uses_station_and_year(self):
        case_number = next_case_number(self.station)
        self.assertTrue(case_number.startswith(f"CR-{self.station.code}-{timezone.now().year}-"))

    def test_case_create_assigns_case_number_automatically(self):
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse("cases:create"),
            {
                "title": "Test burglary",
                "crime_category": "theft",
                "location": "Mvita",
                "narrative": "Sample narrative",
                "status": "open",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        from apps.cases.models import Case

        created = Case.objects.get(title="Test burglary")
        self.assertTrue(created.case_number.startswith(f"CR-{self.station.code}-{timezone.now().year}-"))

    def test_case_export_pdf_returns_pdf_bytes(self):
        from apps.cases.models import Case

        case = Case.objects.create(
            station=self.station,
            case_number=f"CR-{self.station.code}-{timezone.now().year}-0001",
            title="Unicode test — export",
            crime_category="theft",
            location="Mvita",
            narrative="Narrative with em dash — and other text.",
            created_by=self.officer,
        )
        self.client.force_login(self.officer)

        response = self.client.get(reverse("cases:export_pdf", args=[case.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
