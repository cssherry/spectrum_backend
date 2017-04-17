from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

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
app.conf.beat_schedule = {
    'fetch-every-x-minutes': {
        'task': 'spectrum_backend.feed_fetcher.tasks.task_fetch_rss',
        'schedule': MINUTES_BETWEEN_FETCHES * 60.0
    },
}

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))