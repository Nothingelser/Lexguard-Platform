from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services import provision_commander_account


class Command(BaseCommand):
    help = "Provision a regional commander account with a temporary password."

    def add_arguments(self, parser):
        parser.add_argument("--first-name", required=True)
        parser.add_argument("--last-name", required=True)
        parser.add_argument("--password")
        parser.add_argument("--email")

    def handle(self, *args, **options):
        password = options["password"] or getpass("Temporary commander password: ")
        if not password:
            raise CommandError("A temporary password is required.")

        user = provision_commander_account(
            first_name=options["first_name"],
            last_name=options["last_name"],
            password=password,
            email=options["email"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Provisioned commander {user.get_full_name() or user.username} with login {user.badge_number}"
            )
        )
