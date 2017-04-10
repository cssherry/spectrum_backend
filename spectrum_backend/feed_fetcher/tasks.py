from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from management.commands._add_new_associations import add
from celery.task import task

logger = get_task_logger(__name__)

@task()
def task_add_new_associations():
    add()

