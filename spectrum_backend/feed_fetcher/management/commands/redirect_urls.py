from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from django.core.paginator import Paginator
from urllib.error import HTTPError
import urllib

# TODO - delete after migration
class Command(BaseCommand):
  def handle(self, *args, **options):
    paginator = Paginator(FeedItem.objects.all(), 10000)
    for page in range(1, paginator.num_pages + 1):
      print("Parsing next 10000 URLs")
      for feed_item in paginator.page(page).object_list:
        try:
          url = urllib.urlopen(feed_item.url).geturl()
          url_parameter_delimiter = "?"
          feed_item.redirected_url = url.split(url_parameter_delimiter)[0]
          feed_item.save()
        except HTTPError as e:
          feed_item.redirected_url = feed_item.url
          feed_item.save()