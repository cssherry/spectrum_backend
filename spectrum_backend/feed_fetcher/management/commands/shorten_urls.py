from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.tasks import task_shorten_urls

class Command(BaseCommand):
  def handle(self, *args, **options):
    task_shorten_urls.delay()