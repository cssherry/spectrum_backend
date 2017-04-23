from spectrum_backend.feed_fetcher.models import FeedItem
from django.conf import settings
from .tfidf import main
import os

class AddNewAssociations:
    def add(debug=False):
        all_relevant_feed_items = FeedItem.recent_items_eligible_for_association(settings.DAYS_TO_CHECK_FOR)
        already_checked = all_relevant_feed_items.filter(checked_for_associations=True)
        new_feed_items = all_relevant_feed_items.filter(checked_for_associations=False)

        if debug:
            already_checked = already_checked[:100]
            new_feed_items = new_feed_items[:10]

        if new_feed_items.count() > 0:
            main(already_checked, new_feed_items, memory_threshold=settings.ASSOCIATION_MEMORY_THRESHOLD)
        else:
            print("No new associations")