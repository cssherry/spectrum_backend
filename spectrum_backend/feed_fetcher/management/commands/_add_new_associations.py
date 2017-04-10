from spectrum_backend.feed_fetcher.models import FeedItem
from .tfidf import main
import os

DAYS_TO_CHECK_FOR = int(os.environ['DAYS_TO_CHECK_FOR']) or 14
ASSOCIATION_MEMORY_THRESHOLD = int(os.environ['ASSOCIATION_MEMORY_THRESHOLD']) or 2000

# Adds new associations
def add():
  all_relevant_feed_items = FeedItem.recent_items_eligible_for_association(DAYS_TO_CHECK_FOR)
  already_checked = all_relevant_feed_items.filter(checked_for_associations=True)
  new_feed_items = all_relevant_feed_items.filter(checked_for_associations=False)

  if new_feed_items.count() > 0:
    main(already_checked, new_feed_items, memory_threshold=ASSOCIATION_MEMORY_THRESHOLD)
  else:
    print("No new associations")