"""WSGI config for scos_sensor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

from __future__ import absolute_import

import os

import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")
django.setup()  # this is necessary because we need to handle our own thread

from sensor import settings  # noqa
from scheduler import scheduler  # noqa

application = get_wsgi_application()


if settings.RUNNING_DEVSERVER:
    # Normally scheduler is started by gunicorn worker process
    scheduler.thread.start()
