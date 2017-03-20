from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from .tfidf import main

DAYS_TO_CHECK_FOR = 21

# Adds new associations
class Command(BaseCommand):
  def handle(self, *args, **options):
    all_relevant_feed_items = FeedItem.recent_items_eligible_for_association(DAYS_TO_CHECK_FOR)
    already_checked = all_relevant_feed_items.filter(checked_for_associations=True)
    new_feed_items = all_relevant_feed_items.filter(checked_for_associations=False)

    if new_feed_items.count() > 0:
      main(already_checked, new_feed_items)
    else:
      print("No new associations")