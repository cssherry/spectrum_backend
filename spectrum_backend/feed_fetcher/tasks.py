from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from django.core.management import call_command
from celery.decorators import task

logger = get_task_logger(__name__)

@periodic_task(
    run_every=(crontab(minutes=10)),
    name="task_add_associations",
    ignore_result=True
)

def task_fetch_rss_feeds():
    call_command('add_new_associations')

