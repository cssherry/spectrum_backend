from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from django.core.paginator import Paginator
from urllib import parse
import urllib

class Command(BaseCommand):
  def handle(self, *args, **options):
    paginator = Paginator(feed_items, 10000)
    for page in range(1, paginator.num_pages + 1):
      print("Parsing next 10000 URLs")
      for feed_item in paginator.page(page).object_list:
        try:
          url = urllib.request.urlopen(feed_item.url).geturl()
          url_parts = parse.urlparse(raw_url)
          feed_item.redirected_url = "".join([url_parts.netloc, url_parts.path])
          feed_item.save()
        except:
          pass