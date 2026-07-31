import json
import re

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.cases.models import AuditLog, Case, CaseSuspect
from apps.cases.exports import build_case_pdf
from apps.cases.services import next_case_number
from apps.stations.models import PoliceStation
from apps.suspects.models import Suspect


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

    def test_case_list_htmx_status_filter_marks_active_pill(self):
        self.client.force_login(self.officer)

        response = self.client.get(
            reverse("cases:list"),
            {"status": "open"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="lg-filter-pill active"')
        self.assertContains(response, ">Open<")

    def test_case_link_suspect_creates_link_and_returns_updated_partial(self):
        case = Case.objects.create(
            station=self.station,
            case_number=f"CR-{self.station.code}-{timezone.now().year}-0002",
            title="Link suspect test",
            crime_category="theft",
            location="Mvita",
            narrative="Narrative",
            created_by=self.officer,
        )
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse("cases:link_suspect", args=[case.pk]),
            {
                "national_id": "ID-12345678",
                "full_name": "Jane Doe",
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Doe")
        self.assertIn("HX-Trigger", response)
        trigger = json.loads(response["HX-Trigger"])
        self.assertEqual(trigger["lexguard:notify"]["level"], "success")
        self.assertIn("Linked Jane Doe", trigger["lexguard:notify"]["message"])
        self.assertTrue(Suspect.objects.filter(national_id="ID-12345678", full_name="Jane Doe").exists())
        self.assertTrue(CaseSuspect.objects.filter(case=case, suspect__national_id="ID-12345678", role="suspect").exists())

    def test_case_link_suspect_saves_unique_photo_per_suspect(self):
        case = Case.objects.create(
            station=self.station,
            case_number=f"CR-{self.station.code}-{timezone.now().year}-0006",
            title="Photo isolation test",
            crime_category="theft",
            location="Mvita",
            narrative="Narrative",
            created_by=self.officer,
        )
        self.client.force_login(self.officer)

        photo_one = SimpleUploadedFile(
            "suspect-one.png",
            (
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x02\x00\x00\x00\x90wS\xde"
                b"\x00\x00\x00\x0cIDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01"
                b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
            content_type="image/png",
        )
        photo_two = SimpleUploadedFile(
            "suspect-two.png",
            (
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x02\x00\x00\x00\x90wS\xde"
                b"\x00\x00\x00\x0cIDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01"
                b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
            content_type="image/png",
        )

        response_one = self.client.post(
            reverse("cases:link_suspect", args=[case.pk]),
            {
                "national_id": "ID-11111111",
                "full_name": "Alice One",
                "photo": photo_one,
            },
            HTTP_HX_REQUEST="true",
        )
        response_two = self.client.post(
            reverse("cases:link_suspect", args=[case.pk]),
            {
                "national_id": "ID-22222222",
                "full_name": "Bob Two",
                "photo": photo_two,
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response_one.status_code, 200)
        self.assertEqual(response_two.status_code, 200)
        suspect_one = Suspect.objects.get(national_id="ID-11111111")
        suspect_two = Suspect.objects.get(national_id="ID-22222222")
        self.assertTrue(suspect_one.photo.name.startswith("suspects/photos/"))
        self.assertTrue(suspect_two.photo.name.startswith("suspects/photos/"))
        self.assertNotEqual(suspect_one.photo.name, suspect_two.photo.name)
        self.assertTrue(CaseSuspect.objects.filter(case=case, suspect=suspect_one).exists())
        self.assertTrue(CaseSuspect.objects.filter(case=case, suspect=suspect_two).exists())

    def test_case_link_suspect_duplicate_shows_already_linked_notification(self):
        case = Case.objects.create(
            station=self.station,
            case_number=f"CR-{self.station.code}-{timezone.now().year}-0005",
            title="Duplicate suspect test",
            crime_category="theft",
            location="Mvita",
            narrative="Narrative",
            created_by=self.officer,
        )
        suspect = Suspect.objects.create(national_id="ID-99999999", full_name="John Doe")
        CaseSuspect.objects.create(case=case, suspect=suspect, role="suspect")
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse("cases:link_suspect", args=[case.pk]),
            {
                "national_id": "ID-99999999",
                "full_name": "John Doe",
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        trigger = json.loads(response["HX-Trigger"])
        self.assertIn("already linked", trigger["lexguard:notify"]["message"])
        self.assertEqual(CaseSuspect.objects.filter(case=case, suspect=suspect).count(), 1)

    def test_case_add_witness_emits_confirmation_trigger_for_htmx(self):
        case = Case.objects.create(
            station=self.station,
            case_number=f"CR-{self.station.code}-{timezone.now().year}-0003",
            title="Witness confirmation test",
            crime_category="theft",
            location="Mvita",
            narrative="Narrative",
            created_by=self.officer,
        )
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse("cases:add_witness", args=[case.pk]),
            {
                "full_name": "Witness One",
                "contact": "0700000000",
                "statement": "Saw the suspect leave the scene.",
            },
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Trigger", response)
        trigger = json.loads(response["HX-Trigger"])
        self.assertEqual(trigger["lexguard:notify"]["level"], "success")
        self.assertIn("Added witness", trigger["lexguard:notify"]["message"])

    def test_case_export_pdf_compacts_long_evidence_references(self):
        case = Case.objects.create(
            station=self.station,
            case_number=f"CR-{self.station.code}-{timezone.now().year}-0004",
            title="Long evidence reference test",
            crime_category="theft",
            location="Mvita",
            narrative="Narrative",
            created_by=self.officer,
        )
        case.evidence_items.create(
            label="ROBERY FOOTAGE",
            storage_path="https://example.supabase.co/storage/v1/object/public/case-evidence/2026/07/31/this-is-a-very-long-evidence-reference-that-should-not-spill-into-a-second-page.mp4",
        )

        pdf_bytes = build_case_pdf(case)

        self.assertIn(b"this-is-a-very-long-evidence-reference-that-should-not-spill-into-a-s...", pdf_bytes)
        self.assertEqual(len(re.findall(rb"/Type /Page(?!s)", pdf_bytes)), 1)
