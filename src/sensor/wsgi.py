"""
WSGI config for scos_sensor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

from __future__ import absolute_import

import logging
import os
import signal

import django
from django.core.wsgi import get_wsgi_application

# django's dev server seems to ignore this but it gets picked up by gunicorn
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.production_settings")
django.setup()  # this is necessary because we need to handle our own thread

# import of django app must happen after setup call
from scheduler import scheduler  # noqa


application = get_wsgi_application()

logger = logging.getLogger(__name__)

logger.info("Starting scheduler")
scheduler.thread.start()


def stop_scheduler(*args):
    if scheduler.thread.is_alive():
        logger.info("Stopping scheduler")
        scheduler.thread.stop()


try:
    signal.signal(signal.SIGINT, stop_scheduler)
except:
    # django's dev server owns main thread
    pass
