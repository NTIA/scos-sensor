"""
WSGI config for scos_sensor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import atexit
import logging
import os

from django.core.wsgi import get_wsgi_application

from scheduler import scheduler


logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scos_sensor.settings")

application = get_wsgi_application()

# MUST use a single-process server to ensure a single scheduler instance
scheduler_thread = scheduler.Scheduler()


def stop_scheduler(*args):
    if scheduler_thread.is_alive():
        logger.info("Stopping scheduler")
        scheduler_thread.stop()


logger.info("Starting scheduler")
atexit.register(stop_scheduler)

scheduler_thread.start()
