"""WSGI config for scos_sensor project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/

isort:skip_file

"""

import os

import django
import importlib
import logging
from django.core.wsgi import get_wsgi_application
from environs import Env
from scos_actions.signals import register_component_with_status

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
    env = Env()
    sigan_module_setting = env("SIGAN_MODULE")
    sigan_module = importlib.import_module(sigan_module_setting)
    logger = logging.getLogger(__name__)
    logger.info("Creating " + env("SIGAN_CLASS") + " from " + env("SIGAN_MODULE"))
    sigan_constructor = getattr(sigan_module, env("SIGAN_CLASS"))
    sigan = sigan_constructor()
    register_component_with_status.send(sigan, component=sigan)
    scheduler.thread.signal_analyzer = sigan
    scheduler.thread.start()
    scheduler.thread.start()

