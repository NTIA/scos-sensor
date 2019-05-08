import os
import sys
import django

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')

sys.path.append(PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa

try:
    password = os.environ['ADMIN_PASSWORD']
    email = os.environ['ADMIN_EMAIL']
except KeyError:
    print("Not on a managed sensor, so not auto-generating admin account.")
    print("You can add an admin later with `./manage.py createsuperuser`")
    sys.exit(0)

UserModel = get_user_model()

try:
    admin_user = UserModel._default_manager.get(username='admin')
except UserModel.DoesNotExist:
    UserModel._default_manager.create_superuser('admin', email, password)
