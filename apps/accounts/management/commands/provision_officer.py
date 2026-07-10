from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from apps.stations.models import PoliceStation
from apps.accounts.services import provision_officer_account


class Command(BaseCommand):
    help = "Provision a station officer account with an auto-generated badge/login ID."

    def add_arguments(self, parser):
        parser.add_argument("--station", required=True, help="Station code, e.g. MSA-MVT")
        parser.add_argument("--first-name", required=True)
        parser.add_argument("--last-name", required=True)
        parser.add_argument("--password")
        parser.add_argument("--email")

    def handle(self, *args, **options):
        password = options["password"] or getpass("Temporary officer password: ")
        if not password:
            raise CommandError("A temporary password is required.")

        station = PoliceStation.objects.filter(code=options["station"], is_active=True).first()
        if not station:
            raise CommandError(f"Active station not found for code {options['station']!r}.")

        user = provision_officer_account(
            station=station,
            first_name=options["first_name"],
            last_name=options["last_name"],
            password=password,
            email=options["email"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Provisioned officer {user.get_full_name() or user.username} at {station.code} with login {user.username}"
            )
        )
