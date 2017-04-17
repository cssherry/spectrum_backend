from spectrum_backend.feed_fetcher.tasks import task_fetch_rss
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
  def handle(self, *args, **options):
    task_fetch_rss.delay()