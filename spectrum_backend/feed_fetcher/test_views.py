import sys, os
from mock import patch, Mock
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase
from . import factories
from spectrum_backend.feed_fetcher.models import Publication, Feed, FeedItem, Tag, Association, ScrapyLogItem, CorpusWordFrequency
from StringIO import StringIO
from rest_framework.test import APIRequestFactory
import urllib

def suppress_printed_output():
    return patch('sys.stdout', new=StringIO())

class GetAssociationsTestCase(TestCase):
    def setUp(self):
        self.url = "https://www.planetnews.com/rss/1/example.html"
        self.redirected_url = "https://planetnews.com/1/example.html"
        self.lookup_url = "planetnews.com/1/example.html"
        self.factory = APIRequestFactory()
        self.feed_item = factories.GenericFeedItemFactory(url=self.url,
                                                          redirected_url=self.redirected_url,
                                                          lookup_url=self.lookup_url)
        self.association = factories.GenericAssociationFactory(base_feed_item=self.feed_item,
                                                                similarity_score=0.5)

    def test_finds_article_with_(self):
        request_url = '/feeds/publications/%s' % urllib.quote_plus(self.redirected_url)
        request = self.factory.get(request_url, format='json')
        response = view(request)
        self.assertEquals(self.association.associated_feed_item.base_object(similarity_score=0.5), response)


