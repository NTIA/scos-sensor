import os
import sys
from multiprocessing import cpu_count


bind = ":8000"
workers = 1
worker_class = "gthread"
threads = cpu_count()

loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")


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
    from scheduler import scheduler

    scheduler.thread.start()


def worker_exit(server, worker):
    """Notify worker process's scheduler thread that it needs to shut down."""
    _modify_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")

    import django

    django.setup()

    from scheduler import scheduler

    scheduler.thread.stop()
