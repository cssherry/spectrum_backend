from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from ._feed_entry_wrapper import FeedItemProcessor

class Command(BaseCommand):
  def handle(self, *args, **options):
    for feed_item in FeedItem.objects.all():
      self.__parse_item(feed_item)
      feed_item = FeedItemProcessor(feed_item)
      feed_item.save()