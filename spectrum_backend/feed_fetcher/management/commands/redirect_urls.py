from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
import urllib

class Command(BaseCommand):
  def handle(self, *args, **options):
    query_param_delimiter = "?"
    feed_items = FeedItem.objects.all()[:10000]

    for feed_item in feed_items:
      try:
        url = urllib.request.urlopen(feed_item.url).geturl()
        print(url)
        feed_item.url = url.split(query_param_delimiter)[0]
        feed_item.save()
      except:
        pass