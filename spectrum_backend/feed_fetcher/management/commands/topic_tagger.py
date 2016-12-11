from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem

class Command(BaseCommand):
  def handle(self, *args, **options):
    # NEW_YORK_TIMES_STRING = "New York Times"
    for feed_item in FeedItem.objects.all():
      # if feed_item.feed.publication.name == NEW_YORK_TIMES_STRING:
        feed_item.identify_topics()

    for feed_item in FeedItem.objects.all():
        feed_item.identify_associations()