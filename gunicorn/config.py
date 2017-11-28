import os
from multithreading import cpu_count


def max_threads():
    return (cpu_count() * 2) - 1


bind = '127.0.0.1:8000'
workers = 1
worker_class = 'gthread'
threads = max_threads()

loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')


def worker_exit(server, worker):
    pass
