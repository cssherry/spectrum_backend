from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from .tfidf import main

# Initial seed for all associations
class Command(BaseCommand):
  def handle(self, *args, **options):
    feed_items = FeedItem.recent_items_eligible_for_association(4)
    main(feed_items)