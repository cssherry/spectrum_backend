from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from ._feed_item_processor import FeedItemProcessor

class Command(BaseCommand):
  def handle(self, *args, **options):
    for feed_item in FeedItem.objects.all():
      feed_item = FeedItemProcessor().process(feed_item)
      feed_item.save()