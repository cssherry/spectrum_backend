from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery
from django.conf import settings
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal

# Sentry
client = Client(os.environ['SPECTRUM_SENTRY_KEY'])

# register a custom filter to filter out duplicate logs
register_logger_signal(client)

# The register_logger_signal function can also take an optional argument
# `loglevel` which is the level used for the handler created.
# Defaults to `logging.ERROR`
register_logger_signal(client, loglevel=logging.WARNING)

# hook into the Celery error handler
register_signal(client)

# The register_signal function can also take an optional argument
# `ignore_expected` which causes exception classes specified in Task.throws
# to be ignored
register_signal(client)# , ignore_expected=True)

try:
  MINUTES_BETWEEN_FETCHES = int(os.environ['MINUTES_BETWEEN_FETCHES']) or 20
except KeyError:
  MINUTES_BETWEEN_FETCHES = 20

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spectrum_backend.settings')

app = Celery('spectrum_backend', include=['spectrum_backend.feed_fetcher.tasks'])

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.broker_url = os.environ['SPECTRUM_REDIS_URL']
app.conf.celery_result_backend = os.environ['SPECTRUM_REDIS_URL']
app.conf.worker_max_memory_per_child = 512000
app.conf.update(
    result_expires=3600,
)
app.conf.celery_redis_max_connections = 10
app.conf.broker_pool_limit = 0
app.conf.beat_schedule = {
    'fetch-every-x-minutes': {
        'task': 'spectrum_backend.feed_fetcher.tasks.task_fetch_rss',
        'schedule': MINUTES_BETWEEN_FETCHES * 60.0
    },
}

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))