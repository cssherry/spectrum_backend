import sys, os
from mock import patch, Mock
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase, RequestFactory
from . import factories
from spectrum_backend.feed_fetcher import views
from spectrum_backend.feed_fetcher.views import get_associated_articles, test_api, all_publications, track_click, track_feedback, pub_stats
from spectrum_backend.feed_fetcher.models import Publication, Feed, FeedItem, Tag, Association, ScrapyLogItem, CorpusWordFrequency, URLLookUpRecord, UserClick, UserFeedback
from io import StringIO
from django.http import JsonResponse
from django.core import serializers
import urllib, json
from spectrum_backend.feed_fetcher.models import Publication


def suppress_printed_output():
    return patch('sys.stdout', new=StringIO())

class TestPubStatsTestCase(TestCase):
    def setUp(self):
        Publication.pub_stats = Mock()

    def test_pub_stats_returns_pub_numbers(self):
        request_url = '/feeds/pub_stats'
        request = RequestFactory().get(request_url)
        response = pub_stats(request)
        self.assertEquals(response.status_code, 200)
        Publication.pub_stats.assert_called_once()

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
        self.url_for_lookup_url = "http://planetnews.com/2/example.html"
        self.lookup_url = "planetnews.com/2/example.html"
        self.factory = RequestFactory()
        self.feed_item = factories.GenericFeedItemFactory(url=self.url,
                                                          redirected_url=self.redirected_url,
                                                          lookup_url=self.lookup_url)
        self.association = factories.GenericAssociationFactory(base_feed_item=self.feed_item,
                                                               similarity_score=0.5)

    def _shared_assertion_response_contains_feed_item(self, url_to_find, code):
        request_url = '/feeds/associations?url=%s' % urllib.parse.quote(url_to_find)
        request = self.factory.get(request_url, format='json')
        response = get_associated_articles(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content.decode())[0], self.association.associated_feed_item.base_object(similarity_score=0.5, association_id=self.association.id))
        self.assertEquals(self.feed_item.urllookuprecord_set.count(), 1)
        self.assertEquals(self.feed_item.urllookuprecord_set.last().code, code)
        self.assertEquals(self.feed_item.urllookuprecord_set.last().feed_item, self.feed_item)
        self.assertEquals(self.feed_item.urllookuprecord_set.last().associations_found, 1)
        self.assertEquals(self.feed_item.urllookuprecord_set.last().url, url_to_find)

    def test_finds_article_associations_with_lookup_url(self):
        self._shared_assertion_response_contains_feed_item(self.url_for_lookup_url, "1")

    def test_finds_article_associations_with_redirected_url(self):
        self._shared_assertion_response_contains_feed_item(self.redirected_url, "2")

    def test_finds_article_associations_with_regular_url(self):
        self._shared_assertion_response_contains_feed_item(self.url, "3")

    def test_works_with_post(self):
        request_url = '/feeds/associations?url=%s' % urllib.parse.quote(self.url_for_lookup_url)
        request = self.factory.post(request_url, format='json')
        response = get_associated_articles(request)
        self.assertEquals(response.status_code, 200)

    def test_returns_message_if_url_not_found(self):
        request_url = '/feeds/associations?url=%s' % 'https://blahblahblah.com/thing'
        request = self.factory.get(request_url, format='json')
        response = get_associated_articles(request)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(json.loads(response.content.decode())["message"], "URL not found")
        self.assertEquals(URLLookUpRecord.objects.count(), 1)
        self.assertEquals(URLLookUpRecord.objects.last().code, "N/A")
        self.assertEquals(URLLookUpRecord.objects.last().associations_found, None)
        self.assertEquals(URLLookUpRecord.objects.last().feed_item, None)
        self.assertEquals(URLLookUpRecord.objects.last().url, 'https://blahblahblah.com/thing')

    def test_returns_message_if_base_url(self):
        request_url = '/feeds/associations?url=%s' % 'https://planetnews.com'
        request = self.factory.get(request_url, format='json')
        response = get_associated_articles(request)
        self.assertEquals(response.status_code, 422)
        self.assertEquals(json.loads(response.content.decode())["message"], "Base URL, Spectrum modal skipped")
        self.assertEquals(URLLookUpRecord.objects.count(), 1)
        self.assertEquals(URLLookUpRecord.objects.last().code, "Base")
        self.assertEquals(URLLookUpRecord.objects.last().associations_found, None)
        self.assertEquals(URLLookUpRecord.objects.last().feed_item, None)
        self.assertEquals(URLLookUpRecord.objects.last().url, 'https://planetnews.com')

class GetTrackClickTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request_url = '/feeds/click'

    def test_tracks_click_finds_association(self):
        association = factories.GenericAssociationFactory()
        request = self.factory.post(self.request_url, {'association_id': association.id}, format='json')
        response = track_click(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(UserClick.objects.count(), 1)

    def test_tracks_click_returns_correct_status_if_association_not_found(self):
        association = factories.GenericAssociationFactory()
        request = self.factory.post(self.request_url, {'association_id': 400000}, format='json')
        response = track_click(request)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(UserClick.objects.count(), 0)

    def test_tracks_feedback_returns_missing_status_if_fields_missing(self):
        request = self.factory.post(self.request_url, {}, format='json')
        response = track_click(request)
        self.assertEquals(response.status_code, 422)
        self.assertEquals(UserFeedback.objects.count(), 0)

class GetTrackUserFeedbackTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        views.client.captureException = Mock()
        association = factories.GenericAssociationFactory()
        self.request_object = {
            "association_id": association.id,
            "is_negative": True,
            "feedback_version": 2,
            "feedback_dict": json.dumps({
                "something": "arbitrary",
                "more": "fields"
            }),
        }
        self.request_url = '/feeds/feedback'

    def test_tracks_feedback_finds_association(self):
        request = self.factory.post(self.request_url, self.request_object, format='json')
        response = track_feedback(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(UserFeedback.objects.count(), 1)
        self.assertEquals(UserFeedback.objects.last().association_id, self.request_object["association_id"])
        self.assertEquals(UserFeedback.objects.last().is_negative, self.request_object["is_negative"])
        self.assertEquals(UserFeedback.objects.last().feedback_version, self.request_object["feedback_version"])
        self.assertEquals(UserFeedback.objects.last().feedback_dict, self.request_object["feedback_dict"])

    def test_tracks_internal_user(self):
        self.request_object["is_internal_user"] = True
        request = self.factory.post(self.request_url, self.request_object, format='json')
        response = track_feedback(request)
        self.assertEquals(UserFeedback.objects.last().is_internal_user, True)

    def test_tracks_feedback_returns_correct_status_if_not_found(self):
        self.request_object["association_id"] = 10000000
        request = self.factory.post(self.request_url, self.request_object, format='json')
        response = track_feedback(request)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(UserFeedback.objects.count(), 0)
        views.client.captureException.assert_called_once()

    def test_tracks_feedback_returns_missing_status_if_fields_missing(self):
        self.request_object["association_id"] = ""
        request = self.factory.post(self.request_url, self.request_object, format='json')
        response = track_feedback(request)
        self.assertEquals(response.status_code, 422)
        self.assertEquals(UserFeedback.objects.count(), 0)

