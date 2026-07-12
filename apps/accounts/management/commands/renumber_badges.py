from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Preview or rebuild existing badge numbers so they follow the current LexGuard rules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually update users. Without this flag the command only shows the planned changes.",
        )

    def _planned_badges(self):
        plans = []

        officer_qs = User.objects.filter(role=User.Role.OFFICER).select_related("station").order_by("station__code", "pk")
        counters = defaultdict(int)
        for user in officer_qs:
            if not user.station_id:
                raise CommandError(f"Officer {user.username} has no station assigned.")
            counters[user.station_id] += 1
            badge = f"CST-{user.station.code}-{counters[user.station_id]:04d}"
            plans.append((user, badge))

        commander_qs = User.objects.filter(role=User.Role.COMMANDER).order_by("pk")
        for index, user in enumerate(commander_qs, start=1):
            badge = f"CST-CMD-{index:04d}"
            plans.append((user, badge))

        return plans

    def handle(self, *args, **options):
        plans = self._planned_badges()
        if not plans:
            self.stdout.write(self.style.WARNING("No officers or commanders found to renumber."))
            return

        self.stdout.write("Planned badge changes:")
        for user, badge in plans:
            current = user.badge_number
            if current == badge:
                self.stdout.write(f"  = {user.username} -> {badge}")
            else:
                self.stdout.write(f"  {current} -> {badge}")

        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Dry run only. Re-run with --apply to save changes."))
            return

        with transaction.atomic():
            temp_prefix = "__renumber__"
            for index, (user, _badge) in enumerate(plans, start=1):
                user.username = f"{temp_prefix}{user.pk}_{index}"
                user.badge_number = f"{temp_prefix}{user.pk}_{index}"
                user.save(update_fields=["username", "badge_number"])

            for user, badge in plans:
                user.username = badge
                user.badge_number = badge
                user.save(update_fields=["username", "badge_number"])

        self.stdout.write(self.style.SUCCESS(f"Updated {len(plans)} badge numbers."))
