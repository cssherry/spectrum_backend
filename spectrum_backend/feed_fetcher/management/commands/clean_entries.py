from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from spectrum_backend.feed_fetcher.models import FeedItem
from ._feed_item_processor import FeedItemProcessor
from django.core.paginator import Paginator


class Command(BaseCommand):
  def handle(self, *args, **options):
    paginator = Paginator(FeedItem.objects.all(), 10000)
    for page in range(1, paginator.num_pages + 1):
      print("Parsing next 10000 items")
      for feed_item in paginator.page(page).object_list:
        feed_item = FeedItemProcessor().process(feed_item)
        try:
          feed_item.save()
        except IntegrityError as e:
          feed_item.delete()
          print(e)