#!/usr/bin/env python3

import os
import sys

import django
from django.contrib.auth import get_user_model  # noqa

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")

sys.path.append(PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")
django.setup()

UserModel = get_user_model()


def add_user(username, password, email=None):
    try:
        admin_user = UserModel._default_manager.get(username=username)
        if email:
            admin_user.email = email
        admin_user.set_password(password)
        print("Reset admin account password and email from environment")
    except UserModel.DoesNotExist:
        UserModel._default_manager.create_superuser(username, email, password)
        print("Created admin account with password and email from environment")


try:
    password = os.environ["ADMIN_PASSWORD"]
    print("Retreived admin password from environment variable ADMIN_PASSWORD")
    email = os.environ["ADMIN_EMAIL"]
    print("Retreived admin email from environment variable ADMIN_EMAIL")
    username = os.environ["ADMIN_NAME"]
    print("Retreived admin name from environment variable ADMIN_NAME")
    add_user(username, password, email)
except KeyError:
    print("Not on a managed sensor, so not auto-generating admin account.")
    print("You can add an admin later with `./manage.py createsuperuser`")
    sys.exit(0)

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
        additional_user_password = os.environ["ADDITIONAL_USER_PASSWORD"]
    else:
        # user will have unusable password
        # https://docs.djangoproject.com/en/3.2/ref/contrib/auth/#django.contrib.auth.models.UserManager.create_user
        additional_user_password = None
    print(
        "Retreived additional user password from environment variable ADDITIONAL_USER_PASSWORD"
    )
except KeyError:
    print("Not creating any additonal users.")


if additional_user_names != "" and additional_user_password != "":
    if "," in additional_user_names:
        for additional_user_name in additional_user_names.split(","):
            add_user(additional_user_name.strip(), additional_user_password)
    else:
        add_user(additional_user_names, additional_user_password)
