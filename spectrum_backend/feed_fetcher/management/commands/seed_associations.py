from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from .tfidf import main

class Command(BaseCommand):
  def handle(self, *args, **options):
    feed_items = FeedItem.items_eligible_for_similarity_score()
    main(feed_items)