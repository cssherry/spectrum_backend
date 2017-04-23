import sys, os
from mock import patch, Mock
from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase
from . import factories
from spectrum_backend.feed_fetcher.models import Publication, Feed, FeedItem, Tag, Association, ScrapyLogItem, CorpusWordFrequency
from StringIO import StringIO

def suppress_printed_output():
    return patch('sys.stdout', new=StringIO())

class GlobalTestCase(TestCase):
    def setUp(self):
        self.publication = factories.GenericPublicationFactory()
        self.feed = factories.GenericFeedFactory(publication=self.publication)
        self.feed_item = factories.GenericFeedItemFactory(feed=self.feed)

class PublicationTestCase(GlobalTestCase):
    def test_feeds_convenience_method(self):
        feed2 = factories.GenericFeedFactory(publication=self.publication)
        feeds = self.publication.feeds()
        self.assertIn(self.feed, feeds)
        self.assertIn(feed2, feeds)

    def test_feed_items_convenience_method(self):
        feed_items = self.publication.feed_items()
        feed_item2 = factories.GenericFeedItemFactory(feed=self.feed)
        self.assertIn(self.feed_item, feed_items)
        self.assertIn(feed_item2, feed_items)

class FeedTestCase(GlobalTestCase):
    def test_feed_items_convenience_method(self):
        feed_items = self.feed.feed_items()
        feed_item1, feed_item2 = factories.GenericFeedItemFactory.create_batch(2, feed=self.feed)
        self.assertIn(feed_item1, feed_items)
        self.assertIn(feed_item2, feed_items)

    def test_empty_content_report(self):
        factories.GenericFeedItemFactory.create_batch(2, feed=self.feed)
        with suppress_printed_output():
            self.feed.display_empty_content_report()

class FeedItemTestCase(GlobalTestCase):
    def test_publication_convenience_methods(self):
        feed_item = factories.GenericFeedItemFactory(raw_description='a' * 40)
        self.assertEqual(feed_item.feed.publication.name, feed_item.publication_name())
        self.assertEqual(feed_item.feed.publication.bias, feed_item.publication_bias())
        self.assertEqual(feed_item.feed.publication.logo_url, feed_item.publication_logo())
        self.assertEqual(feed_item.feed.category, feed_item.feed_category())

    def test_short_description(self):
        feed_item = factories.GenericFeedItemFactory(raw_description='a' * 40)
        self.assertLessEqual(len(feed_item.short_description()), 35)

    def test_friendly_publication_date(self):
        now = timezone.now()
        feed_item = factories.GenericFeedItemFactory(publication_date=now)
        self.assertEqual(feed_item.friendly_publication_date(), now.strftime("%Y-%m-%d %H:%M:%S"))

    def test_under_scrapy_cap(self):
        feed_item = self.feed_item
        factories.GenericScrapyLogItemFactory.create_batch(1, feed_item=feed_item)
        self.assertTrue(feed_item.under_max_scraping_cap())
        factories.GenericScrapyLogItemFactory(feed_item=feed_item)
        self.assertFalse(feed_item.under_max_scraping_cap())

    def test_base_object_has_basic_keys(self):
        feed_item = self.feed_item
        base_object = feed_item.base_object()
        self.assertEqual(feed_item.publication_name(), base_object["publication_name"])
        self.assertEqual(feed_item.publication_bias(), base_object["publication_bias"])
        self.assertEqual(feed_item.publication_logo(), base_object["publication_logo"])
        self.assertEqual(feed_item.feed_category(), base_object["feed_category"])
        self.assertEqual(feed_item.title, base_object["title"])
        self.assertEqual(feed_item.description, base_object["description"])
        self.assertEqual(feed_item.content, base_object["content"])
        self.assertEqual(feed_item.url, base_object["url"])
        self.assertEqual(feed_item.author, base_object["author"])
        self.assertEqual(feed_item.image_url, base_object["image_url"])
        self.assertEqual(feed_item.friendly_publication_date(), base_object["publication_date"])

    def test_base_object_can_have_association_similarity_score_passed(self):
        feed_item = self.feed_item
        base_object = feed_item.base_object(similarity_score=3.3)
        self.assertEqual(3.3, base_object["similarity_score"])

    def test_should_scrape_if_under_max_scraping_cap_and_no_raw_content(self):
        feed_item = factories.GenericFeedItemFactory(raw_content="")
        feed_item.under_max_scraping_cap = Mock(return_value = True)
        self.assertTrue(feed_item.should_scrape())
        feed_item.raw_content = "lalala"
        self.assertFalse(feed_item.should_scrape())

    def test_should_scrape_if_ignore_scraping_cap_and_no_raw_content(self):
        feed_item = factories.GenericFeedItemFactory(raw_content="")
        feed_item.under_max_scraping_cap = Mock(return_value = False)
        self.assertFalse(feed_item.should_scrape())
        self.assertTrue(feed_item.should_scrape(ignore_scraping_cap=True))
        feed_item = factories.GenericFeedItemFactory(raw_content="lalala")
        self.assertFalse(feed_item.should_scrape(ignore_scraping_cap=True))

    def test_opposing_biases_returns_expected_biases(self):
        feed_item = self.feed_item
        feed_item.publication_bias = Mock(return_value = "L")
        self.assertEqual(["R", "RC", "C"], feed_item.opposing_biases())
        feed_item.publication_bias = Mock(return_value = "LC")
        self.assertEqual(["R", "RC", "C"], feed_item.opposing_biases())
        feed_item.publication_bias = Mock(return_value = "C")
        self.assertEqual(["L", "LC", "C", "RC", "R"], feed_item.opposing_biases())
        feed_item.publication_bias = Mock(return_value = "RC")
        self.assertEqual(["L", "LC", "C"], feed_item.opposing_biases())
        feed_item.publication_bias = Mock(return_value = "R")
        self.assertEqual(["L", "LC", "C"], feed_item.opposing_biases())

    def test_pretty_print_associations_works(self):
        feed_item = self.feed_item
        factories.GenericAssociationFactory.create_batch(5, base_feed_item=feed_item)
        sys.stdout = open(os.devnull, 'w')
        feed_item.pretty_print_associations()
        sys.stdout = sys.__stdout__

    def test_top_associations_should_order_by_similarity_score(self):
        feed_item = self.feed_item
        factories.GenericAssociationFactory.create_batch(5, base_feed_item=feed_item)
        top_associations = feed_item.top_associations(5)
        max_similarity = max(top_associations, key=lambda assoc:assoc["similarity_score"])
        min_similarity = min(top_associations, key=lambda assoc:assoc["similarity_score"])
        first_association = top_associations[0]
        last_association = top_associations[-1]
        self.assertEquals(max_similarity["url"], first_association["url"])
        self.assertEquals(min_similarity["url"], last_association["url"])

    def test_top_associations_should_use_new_publications_first(self):
        feed_item = self.feed_item
        same_publications_with_high_score = factories.GenericAssociationFactory.create_batch(5, base_feed_item=feed_item, associated_feed_item__feed=self.feed, similarity_score=9.0)
        different_association_with_low_score = factories.GenericAssociationFactory(base_feed_item=feed_item, similarity_score=5.0).associated_feed_item.base_object(5.0)
        another_association_with_low_score = factories.GenericAssociationFactory(base_feed_item=feed_item, similarity_score=4.0).associated_feed_item.base_object(4.0)
        another_association_with_score_below_threshold = factories.GenericAssociationFactory(base_feed_item=feed_item, similarity_score=1.5).associated_feed_item.base_object(1.5)
        first_five_associations = feed_item.top_associations(5)
        self.assertIn(different_association_with_low_score, first_five_associations)
        self.assertIn(another_association_with_low_score, first_five_associations)
        self.assertNotIn(another_association_with_score_below_threshold, first_five_associations)

    def test_get_fields_class_method_returns_serialized_version_of_object(self):
        feed_items = []
        feed_items.extend(factories.GenericFeedItemFactory.create_batch(3))
        fields = FeedItem.get_fields(feed_items)
        self.assertIn(feed_items[0].base_object(), fields)
        self.assertEquals(len(fields), 3)

    def test_duplicate_items_class_method_returns_record_for_each_duplicate(self):
        feed_item = self.feed_item
        factories.GenericFeedItemFactory.create_batch(3, title=feed_item.title)
        dups = FeedItem.duplicate_items('title')
        self.assertEquals(len(dups), 1)

    def test_recent_items_eligible_for_association_class_method_includes_only_items_with_content(self):
        feed_item = self.feed_item
        self.assertIn(feed_item, FeedItem.recent_items_eligible_for_association())
        self.assertEquals(1, len(FeedItem.recent_items_eligible_for_association()))
        feed_item.content = ""
        feed_item.save()
        self.assertEquals(0, len(FeedItem.recent_items_eligible_for_association()))

    def test_recent_items_eligible_for_association_class_method_includes_only_items_within_time_threshold(self):
        feed_item = self.feed_item
        three_days_ago = timezone.now() - timedelta(days=3)
        feed_item.created_at = three_days_ago
        feed_item.save()
        self.assertEquals(1, len(FeedItem.recent_items_eligible_for_association(days=4)))
        self.assertEquals(0, len(FeedItem.recent_items_eligible_for_association(days=1)))

    def test_feed_item_urls_to_scrape_should_return_all_relevant_urls(self):
        factories.GenericFeedItemFactory.create_batch(3, raw_content="")
        self.assertEquals(len(FeedItem.feed_items_urls_to_scrape()), 3)

    def test_feed_item_urls_to_scrape_should_not_return_articles_with_content_already(self):
        factories.GenericFeedItemFactory.create_batch(2, raw_content="")
        factories.GenericFeedItemFactory.create_batch(3, raw_content="abc")
        self.assertEquals(len(FeedItem.feed_items_urls_to_scrape()), 2)

    def test_feed_item_urls_to_scrape_should_not_return_skipped_publications(self):
        factories.GenericFeedItemFactory.create_batch(2, raw_content="", feed__publication__skip_scraping=True)
        factories.GenericFeedItemFactory.create_batch(4, raw_content="")
        self.assertEquals(len(FeedItem.feed_items_urls_to_scrape()), 4)

    def test_feed_item_urls_to_scrape_should_not_publications_without_html_tags(self):
        factories.GenericFeedItemFactory.create_batch(6, raw_content="", feed__publication__html_content_tag="")
        factories.GenericFeedItemFactory.create_batch(5, raw_content="")
        self.assertEquals(len(FeedItem.feed_items_urls_to_scrape()), 5)

class CorpusWordFrequencyTestCase(GlobalTestCase):
    def test_get_and_set_corpus_word_dictionary(self):
        corpus_word_frequency = factories.CorpusWordFrequencyFactory(dictionary={"a": 3})
        self.assertEquals(CorpusWordFrequency.get_corpus_dictionary(), corpus_word_frequency.dictionary)
        new_dict = {"h": 20}
        CorpusWordFrequency.set_corpus_dictionary(new_dict)
        self.assertEquals(CorpusWordFrequency.get_corpus_dictionary(), new_dict)

