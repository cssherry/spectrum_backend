from spectrum_backend.feed_fetcher.models import FeedItem
from django.conf import settings
from .tfidf import main
import os

class AddNewAssociations:
    def __init__(self, debug=False):
        all_relevant_feed_items = FeedItem.recent_items_eligible_for_association(settings.DAYS_TO_CHECK_FOR)
        self.old_feed_items = all_relevant_feed_items.filter(checked_for_associations=True)
        self.new_feed_items = all_relevant_feed_items.filter(checked_for_associations=False)

        if debug:
            self.old_feed_items = self.old_feed_items[:100]
            self.new_feed_items = self.new_feed_items[:10]

    def add(self, debug=False):
        if self.new_feed_items.count() > 0:
            main(old_list=self.old_feed_items, new_list=self.new_feed_items, memory_threshold=settings.ASSOCIATION_MEMORY_THRESHOLD) #TODO - replace with _batch_query_set
        else:
            print("No new associations")