"""WSGI config for scos_sensor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/

isort:skip_file

"""

import os

import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")
django.setup()  # this is necessary because we need to handle our own thread

from scheduler import scheduler  # noqa
from sensor import settings  # noqa

if settings.DEBUG:
    # Handle segmentation faults in DEBUG mode
    import faulthandler

    faulthandler.enable()

application = get_wsgi_application()

if not settings.IN_DOCKER:
    # Normally scheduler is started by gunicorn worker process
    scheduler.thread.start()
