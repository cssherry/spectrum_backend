import mock
from mock import patch, Mock
from django.test import TestCase
from django.conf import settings
from spectrum_backend.feed_fetcher.models import Publication, Feed, FeedItem, Tag, Association, ScrapyLogItem, CorpusWordFrequency
from spectrum_backend.feed_fetcher.management.commands import tfidf

class TFIDFTestCase(TestCase):
    fixtures = ['publications', 'feeds', 'ten_random_feed_items'] # Just 10 random feed_items
    # fixtures = ['publications', 'feeds', 'feed_items_to_associate_data_set'] # ~100 articles with common associations
    
    def setUp(self):
        pass

    def testTestTest(self):
        # print(FeedItem.objects.count())

    