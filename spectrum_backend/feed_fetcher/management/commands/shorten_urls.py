from django.core.management.base import BaseCommand, CommandError
# from spectrum_backend.feed_fetcher.tasks import task_shorten_urls
from ._shorten_urls import URLShortener

class Command(BaseCommand):
  def handle(self, *args, **options):
    URLShortener().shorten()