from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from celery.decorators import task

logger = get_task_logger(__name__)

@periodic_task(
    run_every=(crontab()),
    name="task_fetch_rss_feeds",
    ignore_result=True
)

def task_fetch_rss_feeds():
    call_command('rss_fetcher')

