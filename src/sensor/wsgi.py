"""WSGI config for scos_sensor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

from __future__ import absolute_import

import logging
import os

import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")
django.setup()  # this is necessary because we need to handle our own thread

from scheduler import scheduler  # noqa

application = get_wsgi_application()
logger = logging.getLogger(__name__)


# When exec'd inside Docker, Gunicorn's master process inherits pid 1, worker
# process, which we want to run the scheduler, gets pid > 1
if os.getpid() != 1:
    scheduler.thread.start()
