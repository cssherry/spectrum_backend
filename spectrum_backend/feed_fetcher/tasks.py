from celery.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from spectrum_backend.feed_fetcher.management.commands._rss_fetcher import RSSFetcher
from celery.task import task
from celery import Celery
from spectrum_backend.celery import app
from celery.task.control import inspect
import time

# app = Celery('spectrum_backend')

logger = get_task_logger(__name__)

# @app.task
# def task_fetch_rss():
#   i = inspect()
#   for host_name, workers in i.active().iteritems():
#     if len(workers) < 2:
#       print "starting rss_fetcher job"
#       call_command('rss_fetcher')
#       return
#     else:
#       print "fetcher job already active, suppressing new job"
#       app.control.revoke(task_id)
#       return

@app.task
def test_shit():
  print("hey")
  i = inspect()
  for host_name, workers in i.active().iteritems():
    print len(workers)

  return