from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import Feed, FeedItem, Tag
from ._rss_entry_wrapper import RSSEntryWrapper
from ._feed_item_processor import FeedItemProcessor
from ._add_new_associations import AddNewAssociations
from ._url_parser import URLParser
import feedparser
import scrapy
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from django.conf import settings
from django.db.utils import IntegrityError
from raven.contrib.django.raven_compat.models import client

class RSSFetcher:
    def __init__(self, stdout=None, style=None, debug=False):
        self.debug = debug
        self.stdout = stdout
        self.style = style
        if self.debug:
            self.feeds = Feed.objects.all()[:3]
        else:
            self.feeds = Feed.objects.all()

    def fetch(self):    
        for feed in self.feeds:
            self.__fetch_rss_and_parse(feed)
    
            if self.stdout and self.style:
                self.stdout.write(self.style.SUCCESS(self.__parse_message(feed)))
    
        self.__crawl_articles()
        self.__add_new_associations()

    def __fetch_rss_and_parse(self, feed):
        feed_result = feedparser.parse(feed.rss_url)
    
        for entry in feed_result.entries:
            self.__parse_entry(feed, entry)

    def __crawl_articles(self):
        process = CrawlerProcess(get_project_settings())
        process.crawl('articles', debug=self.debug)
        process.start()

    def __add_new_associations(self):
        AddNewAssociations().add(debug=self.debug)

    def __parse_entry(self, feed, entry):
        entry_wrapper = RSSEntryWrapper(feed, entry)
        url = URLParser().clean_url(entry_wrapper.url)
    
        try:
            feed_item = FeedItem.objects.get_or_create(url=url, defaults={'feed': feed, 'redirected_url': url, 'lookup_url': url, 'title': entry_wrapper.title, 'raw_description': entry_wrapper.raw_description, 'author': entry_wrapper.author, 'image_url': entry_wrapper.image_url, 'publication_date': entry_wrapper.publication_date})[0]
            feed_item = FeedItemProcessor().process(feed_item)
            feed_item.save()
            for tag in entry_wrapper.tags:
                Tag.objects.get_or_create(name=tag, feed_item=feed_item)
        except IntegrityError:
            client.captureException()

    def __parse_message(self, feed):
         return 'Parsing items from %s (%s) - %s' % (feed.publication.name, feed.category, feed.rss_url)
