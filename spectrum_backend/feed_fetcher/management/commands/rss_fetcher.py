from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag
from ._rss_entry_wrapper import RSSEntryWrapper
from ._feed_item_processor import FeedItemProcessor
from ._add_new_associations import add
import feedparser
import scrapy
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ._rss_fetcher import RSSFetcher

try:
  ASSOCIATION_MEMORY_THRESHOLD = int(os.environ['ASSOCIATION_MEMORY_THRESHOLD']) or 2000
except KeyError:
  ASSOCIATION_MEMORY_THRESHOLD = 2000

class Command(BaseCommand):
  def handle(self, *args, **options):
    sd
    for feed in Feed.objects.all():
      feed_result = feedparser.parse(feed.rss_url)
      self.stdout.write(self.style.SUCCESS(self.__parse_message(feed)))

      for entry in feed_result.entries:
        self.__parse_entry(feed, entry)

    process = CrawlerProcess(get_project_settings())
    process.crawl('articles', memory_threshold=ASSOCIATION_MEMORY_THRESHOLD)
    process.start()
    add()

  def __parse_entry(self, feed, entry):
    entry_wrapper = RSSEntryWrapper(feed, entry)
    url_parameter_delimiter = "?"
    url = entry_wrapper.url.split(url_parameter_delimiter)[0]

    feed_item = FeedItem.objects.get_or_create(url=url, defaults={'feed': feed, 'redirected_url': url, 'title': entry_wrapper.title, 'raw_description': entry_wrapper.raw_description, 'author': entry_wrapper.author, 'image_url': entry_wrapper.image_url, 'publication_date': entry_wrapper.publication_date})[0]
    feed_item = FeedItemProcessor().process(feed_item)
    feed_item.save()
    for tag in entry_wrapper.tags:
      Tag.objects.get_or_create(name=tag, feed_item=feed_item)

  def __parse_message(self, feed):
    return 'Parsing items from %s (%s) - %s' % (feed.publication.name, feed.category, feed.rss_url)
