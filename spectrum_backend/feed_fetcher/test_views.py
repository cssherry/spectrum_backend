import sys, os
from mock import patch, Mock
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase, RequestFactory
from . import factories
from .views import get_associated_articles, test_api, all_publications
from spectrum_backend.feed_fetcher.models import Publication, Feed, FeedItem, Tag, Association, ScrapyLogItem, CorpusWordFrequency
from io import StringIO
from django.http import JsonResponse
from django.core import serializers
import urllib, json

def suppress_printed_output():
    return patch('sys.stdout', new=StringIO())

class TestApiTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.feed_item1 = factories.GenericFeedItemFactory()
        self.feed_item2 = factories.GenericFeedItemFactory()

    def test_api_returns_recent_feed_items(self):
        request_url = '/feeds/test_api'
        request = self.factory.get(request_url, format='json')
        response = test_api(request)
        self.assertEquals(response.status_code, 200)
        self.assertIn(self.feed_item1.base_object(), json.loads(response.content.decode()))
        self.assertIn(self.feed_item2.base_object(), json.loads(response.content.decode()))

class AllPublicationsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.publication1 = factories.ModeratePublicationFactory()
        self.publication2 = factories.LeftWingPublicationFactory()
        self.publication2 = factories.RightWingPublicationFactory()

    def test_api_returns_recent_feed_items(self):
        request_url = '/feeds/publications'
        request = self.factory.get(request_url, format='json')
        response = all_publications(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(serializers.serialize('json', Publication.objects.all())), json.loads(response.content.decode())["publications"])
        self.assertEquals(len(json.loads(response.content.decode())["publications"]), 3)
        self.assertEquals(json.loads(response.content.decode())["media_bias"], Publication.bias_dict())

class GetAssociationsTestCase(TestCase):
    def setUp(self):
        self.url = "https://www.planetnews.com/rss/1/example.html"
        self.redirected_url = "https://planetnews.com/1/example.html"
        self.redirected_url_with_different_scheme = "http://planetnews.com/1/example.html"
        self.lookup_url = "planetnews.com/1/example.html"
        self.factory = RequestFactory()
        self.feed_item = factories.GenericFeedItemFactory(url=self.url,
                                                          redirected_url=self.redirected_url,
                                                          lookup_url=self.lookup_url)
        self.association = factories.GenericAssociationFactory(base_feed_item=self.feed_item,
                                                               similarity_score=0.5)

    def _shared_assertion_response_contains_feed_item(self, url_to_find):
        request_url = '/feeds/associations?url=%s' % urllib.parse.quote(url_to_find)
        request = self.factory.get(request_url, format='json')
        response = get_associated_articles(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content.decode())[0], self.association.associated_feed_item.base_object(similarity_score=0.5))

    def test_finds_article_associations_with_lookup_url(self):
        self.feed_item.redirected_url = Mock(return_value="")
        self.feed_item.url = Mock(return_value="")
        self._shared_assertion_response_contains_feed_item(self.redirected_url_with_different_scheme)

    def test_finds_article_associations_with_redirected_url(self):
        self.feed_item.lookup_url = Mock(return_value="")
        self.feed_item.url = Mock(return_value="")
        self._shared_assertion_response_contains_feed_item(self.redirected_url)

    def test_finds_article_associations_with_regular_url(self):
        self.feed_item.lookup_url = Mock(return_value="")
        self.feed_item.redirect_url = Mock(return_value="")
        self._shared_assertion_response_contains_feed_item(self.url)




