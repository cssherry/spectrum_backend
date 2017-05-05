from celery.utils.log import get_task_logger
from django.core.management import call_command
from spectrum_backend.feed_fetcher.management.commands._url_parser import URLParser
from spectrum_backend.feed_fetcher.management.commands._seed_base_associations import SeedBaseAssociations
from celery.task import task
from spectrum_backend.celery import app
from celery.task.control import inspect
import time

logger = get_task_logger(__name__)

@app.task
def task_fetch_rss(debug=False):
  _task_rate_limiter('rss_fetcher', lambda: call_command('rss_fetcher', debug=debug))

@app.task
def task_seed_base_associations():
  _task_rate_limiter('seed_base_associations', lambda: SeedBaseAssociations().seed())

@app.task
def task_shorten_urls():
  _task_rate_limiter('batch_shorten_urls', lambda: URLParser().batch_shorten_urls())

def _task_rate_limiter(name, function):
  i = inspect()
  for host_name, workers in i.active().iteritems():
    if len(workers) < 2:
      print("starting %s job" % name)
      function()
    else:
      print("another job already active, suppressing new job")