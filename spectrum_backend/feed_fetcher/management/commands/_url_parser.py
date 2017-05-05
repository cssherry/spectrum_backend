import re
from urllib.parse import urlparse
from raven.contrib.django.raven_compat.models import client
from spectrum_backend.feed_fetcher.models import FeedItem
from django.db.utils import IntegrityError
from ._batch_query_set import batch_query_set

class URLParser:
    def batch_shorten_urls(self): # TODO - deprecate after fixing in scraper
        all_feed_items = FeedItem.objects.all()
        count = 0
        for start, end, total, batched_feed_items in batch_query_set(all_feed_items):
            for feed_item in batched_feed_items:
                feed_item.lookup_url = self.shorten_url(feed_item.redirected_url)
                try:
                    feed_item.save()
                except IntegrityError:
                    feed_item.delete()
                    count += 1

            print("%s items processed out of %s" % (end, total))

        print("%s items deleted" % count)

    def clean_url(self, raw_url):
        url_parameter_delimiter = "?"
        path = raw_url.split(url_parameter_delimiter)[0]
        return path

    def shorten_url(self, raw_url):
        p = urlparse(raw_url)
        try:
            return p.hostname + p.path
        except TypeError:
            client.captureException()

    def is_base_url(self, raw_url):
        p = urlparse(raw_url)
        if not p.hostname:
            client.captureMessage('Invalid URL for is_base_url: %s' % raw_url)
        return p.path == "" or p.path == "/"