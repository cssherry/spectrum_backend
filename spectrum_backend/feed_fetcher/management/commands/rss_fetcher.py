from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag
from ._rss_entry_wrapper import RSSEntryWrapper
import feedparser

class Command(BaseCommand):
  def handle(self, *args, **options):
    for feed in Feed.objects.all():
      feed_result = feedparser.parse(feed.rss_url)
      self.stdout.write(self.style.SUCCESS(self.__parse_message(feed)))

      for entry in feed_result.entries:
        self.__parse_entry(feed, entry)

  def __parse_entry(self, feed, entry):
    entry_wrapper = RSSEntryWrapper(feed, entry)
    feed_item = FeedItem.objects.get_or_create(url=entry_wrapper.url, defaults={'feed': feed, 'title': entry_wrapper.title, 'description': entry_wrapper.description, 'author': entry_wrapper.author, 'image_url': entry_wrapper.image_url, 'publication_date': entry_wrapper.publication_date})[0]
    for tag in entry_wrapper.tags:
      Tag.objects.get_or_create(name=tag, feed_item=feed_item)

  def __parse_message(self, feed):
    return 'Parsing items from %s (%s) - %s' % (feed.publication.name, feed.category, feed.rss_url)