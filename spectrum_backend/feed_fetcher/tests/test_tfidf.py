import sys, os, mock, dateutil, feedparser
from mock import patch, Mock
from datetime import datetime, timedelta
from io import StringIO
from django.utils import timezone
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from django.db.utils import IntegrityError
from . import factories
from spectrum_backend.feed_fetcher.models import Publication, Feed, FeedItem, Tag, Association, ScrapyLogItem, CorpusWordFrequency
from spectrum_backend.feed_fetcher.management.commands import _url_parser, _batch_query_set, _rss_fetcher, _clean_entries, _feed_item_processor, _html_parser, _add_new_associations, seed_base_associations, _rss_entry_wrapper
from article_scraper.spiders import article_spider
import article_scraper.settings
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging
import json

class TFIDFTestCase(TestCase):
    fixtures = ['publications', 'feeds', 'ten_random_feed_items'] # Just 10 random feed_items
    # fixtures = ['publications', 'feeds', 'feed_items_to_associate_data_set'] # ~100 articles with common associations
    
    def setUp(self):
        pass

    def testTestTest(self):
        print(FeedItem.objects.count())

    