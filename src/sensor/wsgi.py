"""
WSGI config for scos_sensor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import logging
import os

from django.core.wsgi import get_wsgi_application

from scheduler import scheduler


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scos_sensor.settings")

application = get_wsgi_application()

logger = logging.getLogger(__name__)

logger.info("Starting scheduler")
scheduler.thread.start()
