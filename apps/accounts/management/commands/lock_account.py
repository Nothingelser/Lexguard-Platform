from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services import lock_account

User = get_user_model()


class Command(BaseCommand):
    help = "Emergency lockout for a compromised account."

    def add_arguments(self, parser):
        parser.add_argument("--username")
        parser.add_argument("--badge-number")

    def handle(self, *args, **options):
        identifier = options["username"] or options["badge_number"]
        if not identifier:
            raise CommandError("Provide --username or --badge-number.")

        user = (
            User.objects.filter(username=identifier).first()
            or User.objects.filter(badge_number=identifier).first()
        )
        if not user:
            raise CommandError(f"Account not found for {identifier!r}.")

        lock_account(user)

        self.stdout.write(self.style.WARNING(f"Locked account {user.username} ({user.badge_number})"))
