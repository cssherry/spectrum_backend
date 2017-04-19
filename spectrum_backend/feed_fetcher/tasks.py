from celery.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from spectrum_backend.feed_fetcher.management.commands._shorten_urls import URLShortener
from celery.task import task
from celery import Celery
from spectrum_backend.celery import app
from celery.task.control import inspect
import time

logger = get_task_logger(__name__)

@app.task
def task_fetch_rss(debug=False):
  i = inspect()
  for host_name, workers in i.active().iteritems():
    if len(workers) < 2:
      print "starting rss_fetcher job"
      call_command('rss_fetcher', debug=debug)
    else:
      print "fetcher job already active, suppressing new job"

@app.task
def task_shorten_urls():
  URLShortener().shorten()
