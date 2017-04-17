from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from spectrum_backend.feed_fetcher.management.commands._add_new_associations import add
# from spectrum_backend.feed_fetcher.management.commands._rss_fetcher import RSSFetcher
from celery.task import task
from celery import Celery

logger = get_task_logger(__name__)
app = Celery ()

# MINUTES_BETWEEN_FETCHES = int(os.environ['MINUTES_BETWEEN_FETCHES']) or 1

# @on_after_configure.connect()
#   def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(60*MINUTES_BETWEEN_FETCHES, task_fetch_rss)

# MINUTES_BETWEEN_FETCHES = int(os.environ['MINUTES_BETWEEN_FETCHES']) or 1

# @on_after_configure.connect()
#   def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(60*MINUTES_BETWEEN_FETCHES, task_fetch_rss)

@task()
def task_add_new_associations():
    add()

# @task()
# def task_fetch_rss():
#   RSSFetcher.fetch()
