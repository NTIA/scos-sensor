import os
import sys
from multiprocessing import cpu_count


def max_threads():
    return (cpu_count() * 2) - 1


bind = ':8000'
workers = 1
worker_class = 'gthread'
threads = max_threads()

loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')


def worker_exit(server, worker):
    """Notify worker process's scheduler thread that it needs to shut down."""
    from os import path

    PATH = path.join(path.dirname(path.abspath(__file__)), '..', '/src')
    sys.path.append(PATH)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")

    import django
    django.setup()

    from scheduler import scheduler
    scheduler.thread.stop()
