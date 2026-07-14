from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.cases.models import Case


@dataclass(frozen=True)
class LegacyOfficerRule:
    legacy_username: str
    station_code: str


LEGACY_OFFICERS = (
    LegacyOfficerRule("officer1", "MSA-MVT"),
    LegacyOfficerRule("officer2", "MSA-NYL"),
    LegacyOfficerRule("officer3", "KLF-KIL"),
    LegacyOfficerRule("officer4", "KWL-DNA"),
    LegacyOfficerRule("officer5", "LAM-LAM"),
    LegacyOfficerRule("officer6", "TTV-VOI"),
    LegacyOfficerRule("officer7", "TNR-HOL"),
)

LEGACY_COMMANDER_USERNAME = "commander"


class Command(BaseCommand):
    help = (
        "Reassign demo cases from legacy seed users to the badge-based accounts, "
        "then remove the legacy users."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually update the database. Without this flag the command only previews the changes.",
        )

    def _canonical_officer_for_station(self, station_code):
        officer_qs = User.objects.filter(role=User.Role.OFFICER, station__code=station_code).order_by("badge_number", "pk")
        exact = officer_qs.filter(badge_number=f"CST-{station_code}-0001").first()
        return exact or officer_qs.first()

    def _build_plan(self):
        plans = []

        for rule in LEGACY_OFFICERS:
            legacy_user = User.objects.filter(username=rule.legacy_username).select_related("station").first()
            if not legacy_user:
                continue

            canonical_user = self._canonical_officer_for_station(rule.station_code)
            if not canonical_user:
                raise CommandError(
                    f"No canonical officer found for station {rule.station_code}. "
                    f"Create or restore the badge-based account first."
                )

            case_qs = Case.objects.filter(created_by=legacy_user)
            plans.append(
                {
                    "legacy_user": legacy_user,
                    "canonical_user": canonical_user,
                    "case_count": case_qs.count(),
                    "legacy_type": "officer",
                }
            )

        legacy_commander = User.objects.filter(username=LEGACY_COMMANDER_USERNAME).first()
        if legacy_commander:
            canonical_commander = (
                User.objects.filter(role=User.Role.COMMANDER, username__startswith="CST-CMD-")
                .order_by("badge_number", "pk")
                .first()
            )
            if canonical_commander:
                plans.append(
                    {
                        "legacy_user": legacy_commander,
                        "canonical_user": canonical_commander,
                        "case_count": 0,
                        "legacy_type": "commander",
                    }
                )

        return plans

    def handle(self, *args, **options):
        plans = self._build_plan()
        if not plans:
            self.stdout.write(self.style.WARNING("No legacy demo accounts found to clean up."))
            return

        self.stdout.write("Planned cleanup:")
        for plan in plans:
            legacy_user = plan["legacy_user"]
            canonical_user = plan["canonical_user"]
            case_count = plan["case_count"]
            self.stdout.write(
                f"  {legacy_user.username} ({legacy_user.badge_number}) -> "
                f"{canonical_user.username} ({canonical_user.badge_number}); "
                f"{case_count} case(s) to reassign"
            )

        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to make changes."))
            return

        with transaction.atomic():
            for plan in plans:
                legacy_user = plan["legacy_user"]
                canonical_user = plan["canonical_user"]

                if plan["legacy_type"] == "officer":
                    Case.objects.filter(created_by=legacy_user).update(created_by=canonical_user)

                legacy_user.delete()

        self.stdout.write(self.style.SUCCESS(f"Cleaned up {len(plans)} legacy demo account(s)."))
