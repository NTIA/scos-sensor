from django.core.management.base import BaseCommand, CommandError

from authentication.models import User


class Command(BaseCommand):
    help = "Prints the admin API token to stdout."

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", type=str, default="admin")

    def handle(self, *args, **options):
        username = options["username"]
        user = User.objects.get(username=username)
        if user:
            key = user.auth_token.key
            self.stdout.write(key)
        else:
            self.stdout.write(
                "No user with username={} found in the database.".format(username)
            )
