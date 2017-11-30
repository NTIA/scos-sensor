from __future__ import absolute_import

import os
import sys
import django

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')

sys.path.append(PATH)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")
django.setup()

from django.contrib.auth import get_user_model

UserModel = get_user_model()

try:
    admin_user = UserModel._default_manager.get(username='admin')
except UserModel.DoesNotExist:
    UserModel._default_manager.create_superuser(
        'admin', 'admin@example.com', 'password')
