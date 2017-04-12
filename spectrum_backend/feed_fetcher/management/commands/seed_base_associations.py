from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from .tfidf import main
import os

DAYS_TO_CHECK_FOR = int(os.environ['DAYS_TO_CHECK_FOR']) or 14

# Initial seed for all associations
class Command(BaseCommand):
  def handle(self, *args, **options):
    feed_items = FeedItem.recent_items_eligible_for_association(DAYS_TO_CHECK_FOR)
    main(feed_items)
    # TODO - delete associations with itself