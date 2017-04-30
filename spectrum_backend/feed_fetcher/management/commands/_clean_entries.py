from django.db.utils import IntegrityError
from spectrum_backend.feed_fetcher.models import FeedItem
from ._feed_item_processor import FeedItemProcessor
from ._batch_query_set import batch_query_set

class CleanEntries:
    def clean(self):
        all_feed_items = FeedItem.objects.all()
        for start, end, total, batched_feed_items in batch_query_set(all_feed_items):
            print "Parsing next %s items" % start
            for feed_item in batched_feed_items:
                feed_item = FeedItemProcessor().process(feed_item)
                try:
                    feed_item.save()
                except IntegrityError as e:
                    feed_item.delete()
                    print(e)