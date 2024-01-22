import logging
import os
import sys

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model  # noqa

logger = logging.getLogger(__name__)


class UsersConfig(AppConfig):
    name = "users"

    def add_user(self, user_model, username, password, email=None):
        try:
            admin_user = user_model._default_manager.get(username=username)
            if email:
                admin_user.email = email
            admin_user.set_password(password)
            admin_user.save()
            logger.debug("Reset admin account password and email from environment")
        except user_model.DoesNotExist:
            user_model._default_manager.create_superuser(username, email, password)
            print("Created admin account with password and email from environment")

    def ready(self):
        if not settings.RUNNING_MIGRATIONS:
            UserModel = get_user_model()
            try:
                password = os.environ["ADMIN_PASSWORD"]
                logger.debug(
                    "Retreived admin password from environment variable ADMIN_PASSWORD"
                )
                email = os.environ["ADMIN_EMAIL"]
                logger.debug(
                    "Retreived admin email from environment variable ADMIN_EMAIL"
                )
                username = os.environ["ADMIN_NAME"]
                logger.debug(
                    "Retreived admin name from environment variable ADMIN_NAME"
                )
                self.add_user(
                    UserModel, username.strip(), password.strip(), email.strip()
                )
            except KeyError:
                logger.warning(
                    "Not on a managed sensor, so not auto-generating admin account."
                )
                logger.warning(
                    "You can add an admin later with `./manage.py createsuperuser`"
                )

            additional_user_names = ""
            additional_user_password = ""
            try:
                additional_user_names = os.environ["ADDITIONAL_USER_NAMES"]
                print(
                    "Retreived additional user names from environment variable ADDITIONAL_USER_NAMES"
                )
                if (
                    "ADDITIONAL_USER_PASSWORD" in os.environ
                    and os.environ["ADDITIONAL_USER_PASSWORD"]
                ):
                    logger.debug(
                        "Retreived additional user password from environment variable ADDITIONAL_USER_PASSWORD"
                    )
                    additional_user_password = os.environ[
                        "ADDITIONAL_USER_PASSWORD"
                    ].strip()
                else:
                    # user will have unusable password
                    # https://docs.djangoproject.com/en/3.2/ref/contrib/auth/#django.contrib.auth.models.UserManager.create_user
                    additional_user_password = None

            except KeyError:
                logger.warning("Not creating any additonal users.")

            if additional_user_names != "" and additional_user_password != "":
                if "," in additional_user_names:
                    for additional_user_name in additional_user_names.split(","):
                        self.add_user(
                            UserModel,
                            additional_user_name.strip(),
                            additional_user_password,
                        )
                else:
                    self.add_user(
                        UserModel,
                        additional_user_names.strip(),
                        additional_user_password,
                    )
