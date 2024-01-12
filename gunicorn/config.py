import importlib
import logging
import os
import sys
from environs import Env
from multiprocessing import cpu_count
from scos_actions.signals import register_component_with_status

bind = ":8000"
workers = 1
worker_class = "gthread"
threads = cpu_count()

loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
logger = logging.getLogger(__name__)

def _modify_path():
    """Ensure Django project is on sys.path."""
    from os import path

    project_path = path.join(path.dirname(path.abspath(__file__)), "../src")
    if project_path not in sys.path:
        sys.path.append(project_path)


def post_worker_init(worker):
    """Start scheduler in worker."""
    _modify_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")

    import django

    django.setup()
    env = Env()
    from scheduler import scheduler
    sigan_module_setting = env("SIGAN_MODULE")
    sigan_module = importlib.import_module(sigan_module_setting)
    logger.info("Creating " + env("SIGAN_CLASS") + " from " + env("SIGAN_MODULE"))
    sigan_constructor = getattr(sigan_module, env("SIGAN_CLASS"))
    sigan = sigan_constructor()
    register_component_with_status.send(sigan, component=sigan)
    scheduler.signal_analyzer = sigan
    scheduler.thread.start()


def worker_exit(server, worker):
    """Notify worker process's scheduler thread that it needs to shut down."""
    _modify_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")

    import django

    django.setup()

    from scheduler import scheduler

    scheduler.thread.stop()
