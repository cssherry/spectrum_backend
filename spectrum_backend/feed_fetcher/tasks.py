from celery.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from spectrum_backend.feed_fetcher.management.commands._rss_fetcher import RSSFetcher
from celery.task import task
from celery import Celery
from spectrum_backend.celery import app

# app = Celery('spectrum_backend')

logger = get_task_logger(__name__)

@app.task
def task_fetch_rss():
    call_command('rss_fetcher')