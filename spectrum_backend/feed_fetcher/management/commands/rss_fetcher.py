from django.core.management.base import BaseCommand, CommandError
from ._rss_fetcher import RSSFetcher

class Command(BaseCommand):
  def handle(self, *args, **options):
    RSSFetcher().fetch(self.stdout, self.style)