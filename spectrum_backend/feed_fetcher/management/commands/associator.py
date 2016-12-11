from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem

class Command(BaseCommand):
  def handle(self, *args, **options):
    for feed_item in FeedItem.objects.all():
        feed_item.identify_associations()

    