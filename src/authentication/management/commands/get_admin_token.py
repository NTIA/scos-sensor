from django.core.management.base import BaseCommand, CommandError
from authentication.models import User


class Command(BaseCommand):
    help = "Prints the admin API token to stdout."

    def handle(self, *args, **options):
        admin_user = User.objects.get(username="admin")
        if admin_user:
            key = admin_user.auth_token.key
            self.stdout.write(key)
        else:
            self.stdout.write("No admin user found in the database.")
