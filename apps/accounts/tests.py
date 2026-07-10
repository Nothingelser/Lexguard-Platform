from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.accounts.services import provision_commander_account
from apps.stations.models import PoliceStation


User = get_user_model()


class SuperAdminLifecycleTests(TestCase):
    def setUp(self):
        self.station = PoliceStation.objects.create(
            code="MSA-MVT",
            name="Mvita",
            region="Coast",
            county="Mombasa",
            sub_county="Mvita",
        )
        self.super_admin = User.objects.create_user(
            username="rootadmin",
            password="RootPass123!",
            badge_number="CST-ROOT-0001",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.super_admin)

    def test_bootstrap_super_admin_command_creates_root_account(self):
        call_command(
            "bootstrap_super_admin",
            username="rootadmin",
            password="RootPass123!",
            badge_number="CST-ROOT-0001",
            email="rootadmin@lexguard.local",
            first_name="Root",
            last_name="Administrator",
        )

        user = User.objects.get(username="rootadmin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_super_admin)
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertFalse(user.must_change_password)

    def test_provision_officer_command_generates_station_badge(self):
        User.objects.create_user(
            username="CST-MSA-MVT-0001",
            password="demo1234",
            badge_number="CST-MSA-MVT-0001",
            role=User.Role.OFFICER,
            station=self.station,
            first_name="Existing",
            last_name="Officer",
        )

        call_command(
            "provision_officer",
            station="MSA-MVT",
            first_name="Amina",
            last_name="Njoroge",
            password="TempPass123!",
        )

        user = User.objects.get(first_name="Amina", last_name="Njoroge")
        self.assertEqual(user.username, "CST-MSA-MVT-0002")
        self.assertEqual(user.badge_number, "CST-MSA-MVT-0002")
        self.assertEqual(user.station, self.station)
        self.assertEqual(user.role, User.Role.OFFICER)
        self.assertTrue(user.must_change_password)

    def test_provision_commander_account_generates_command_badge(self):
        user = provision_commander_account(
            first_name="Muna",
            last_name="Hassan",
            password="TempPass123!",
        )

        self.assertEqual(user.badge_number, "CST-CMD-0001")
        self.assertEqual(user.username, "CST-CMD-0001")
        self.assertEqual(user.role, User.Role.COMMANDER)
        self.assertTrue(user.must_change_password)
        self.assertIsNone(user.station)

    def test_super_admin_routes_to_admin_index(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:index"))

    def test_super_admin_can_open_regional_command_dashboard(self):
        response = self.client.get(reverse("command_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Regional Command Console")

    def test_badge_number_login_works_for_super_admin(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"badge_number": "CST-ROOT-0001", "password": "RootPass123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:index"))

    def test_first_login_forces_password_change_before_app_access(self):
        officer = User.objects.create_user(
            username="CST-MSA-MVT-0002",
            password="TempPass123!",
            badge_number="CST-MSA-MVT-0002",
            role=User.Role.OFFICER,
            station=self.station,
            must_change_password=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"badge_number": officer.badge_number, "password": "TempPass123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:password_change"))

        password_change = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "TempPass123!",
                "new_password1": "NewPass123!",
                "new_password2": "NewPass123!",
            },
        )

        self.assertEqual(password_change.status_code, 302)
        self.assertEqual(password_change.url, reverse("accounts:password_change_done"))

        officer.refresh_from_db()
        self.assertFalse(officer.must_change_password)

        dashboard = self.client.get(reverse("dashboard"))
        self.assertEqual(dashboard.status_code, 200)

    def test_lock_account_command_disables_access(self):
        user = User.objects.create_user(
            username="compromised",
            password="TempPass123!",
            badge_number="CST-MSA-MVT-0099",
            role=User.Role.COMMANDER,
        )

        call_command("lock_account", username="compromised")
        user.refresh_from_db()

        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())

    def test_login_redirects_super_admin_to_admin_site(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"badge_number": "CST-ROOT-0001", "password": "RootPass123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:index"))

    def test_admin_add_user_auto_generates_officer_badge_and_temp_password(self):
        response = self.client.get(reverse("admin:accounts_user_add"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="badge_number"')
        self.assertContains(response, "Temporary password")

        post_response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "first_name": "Amina",
                "last_name": "Njoroge",
                "email": "amina@example.com",
                "role": User.Role.OFFICER,
                "station": self.station.pk,
                "password1": "TempPass123!",
                "password2": "TempPass123!",
                "_save": "Save",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        user = User.objects.get(first_name="Amina", last_name="Njoroge")
        self.assertEqual(user.username, "CST-MSA-MVT-0001")
        self.assertEqual(user.badge_number, "CST-MSA-MVT-0001")
        self.assertEqual(user.station, self.station)
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password("TempPass123!"))

    def test_admin_add_user_auto_generates_commander_badge(self):
        post_response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "first_name": "Muna",
                "last_name": "Hassan",
                "email": "muna@example.com",
                "role": User.Role.COMMANDER,
                "password1": "TempPass123!",
                "password2": "TempPass123!",
                "_save": "Save",
            },
        )

        self.assertEqual(post_response.status_code, 302)
        user = User.objects.get(first_name="Muna", last_name="Hassan")
        self.assertEqual(user.username, "CST-CMD-0001")
        self.assertEqual(user.badge_number, "CST-CMD-0001")
        self.assertIsNone(user.station)
        self.assertTrue(user.must_change_password)
        self.assertTrue(user.check_password("TempPass123!"))
