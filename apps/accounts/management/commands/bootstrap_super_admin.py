from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Create or update the LexGuard super admin account from the command line."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="superadmin")
        parser.add_argument("--badge-number", default="CST-ROOT-0001")
        parser.add_argument("--email", default="superadmin@lexguard.local")
        parser.add_argument("--first-name", default="System")
        parser.add_argument("--last-name", default="Administrator")
        parser.add_argument("--password")

    def handle(self, *args, **options):
        password = options["password"] or getpass("Super admin password: ")
        if not password:
            raise CommandError("A password is required.")

        with transaction.atomic():
            user, created = User.objects.update_or_create(
                username=options["username"],
                defaults={
                    "badge_number": options["badge_number"],
                    "email": options["email"],
                    "first_name": options["first_name"],
                    "last_name": options["last_name"],
                    "role": User.Role.ADMIN,
                    "station": None,
                    "must_change_password": False,
                    "is_staff": True,
                    "is_superuser": True,
                    "is_active": True,
                },
            )
            user.set_password(password)
            user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} super admin {user.username} ({user.badge_number})"))
