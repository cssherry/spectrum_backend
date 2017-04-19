from spectrum_backend.feed_fetcher.models import FeedItem
from ._url_parser import URLParser
import os

try:
  ASSOCIATION_MEMORY_THRESHOLD = int(os.environ['ASSOCIATION_MEMORY_THRESHOLD']) or 1000
except KeyError:
  ASSOCIATION_MEMORY_THRESHOLD = 1000

class URLShortener:
  def shorten(self):
    d
    feed_items = FeedItem.objects.all()
    upper_limit = feed_items / ASSOCIATION_MEMORY_THRESHOLD + 1
    for num in range(1, upper_limit):
      low = ASSOCIATION_MEMORY_THRESHOLD*num
      high = ASSOCIATION_MEMORY_THRESHOLD*(num+1)
      feed_item_part = feed_items[low:high]
      for feed_item in feed_item_part:
        feed_item.lookup_url = URLParser.shorten_url(feed_item.redirected_url)
        feed_item.save()