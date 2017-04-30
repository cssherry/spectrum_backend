import sys, os, mock, dateutil, feedparser
from mock import patch, Mock
from datetime import datetime, timedelta
from StringIO import StringIO
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

WORKING_NYTIMES_RSS_URL = 'http://www.nytimes.com/services/xml/rss/nyt/Politics.xml'

def suppress_printed_output():
    return patch('sys.stdout', new=StringIO())

class BatchQuerySetTestCase(TestCase):
    def setUp(self):
        self.batch_query_set = _batch_query_set.batch_query_set
        factories.GenericFeedItemFactory.create_batch(100)

    def test_should_return_in_batches(self):
        all_feed_items = FeedItem.objects.all()
        for start, end, total, feed_items in self.batch_query_set(all_feed_items, batch_size=10):
            self.assertEquals(end - start, 10)
            self.assertEquals(feed_items.count(), 10)
            self.assertEqual(list(feed_items), list(all_feed_items[start:end]))

    def test_should_default_to_association_memory_threshold(self):
        factories.GenericFeedItemFactory.create_batch(settings.ASSOCIATION_MEMORY_THRESHOLD + 10)
        for start, end, total, feed_items in self.batch_query_set(FeedItem.objects.all()):
            self.assertEquals(end - start, settings.ASSOCIATION_MEMORY_THRESHOLD)
            break

class URLParserTestCase(TestCase):
    def setUp(self):
        self.url_parser = _url_parser.URLParser()
        self.base_url = "https://www.nytimes.com/"
        self.short_url = "www.nytimes.com/hello.html"
        self.full_url = "https://%s" % self.short_url
        self.raw_url = "%s?abcd" % self.full_url

    def test_clean_url_removes_query_params(self):
        self.assertEquals(self.url_parser.clean_url(self.raw_url), self.full_url)

    def test_shorten_url_leaves_domain_and_route(self):
        self.assertEquals(self.url_parser.shorten_url(self.raw_url), self.short_url)

    def test_is_base_url_checks_if_no_route(self):
        _url_parser.client.captureMessage = Mock()
        self.url_parser = _url_parser.URLParser()
        self.assertTrue(self.url_parser.is_base_url(self.base_url))
        self.assertFalse(self.url_parser.is_base_url(self.short_url))
        self.assertFalse(self.url_parser.is_base_url(self.full_url))
        self.assertFalse(self.url_parser.is_base_url(self.raw_url))

    def test_expect_shorten_url_to_call_sentry_if_error(self):
        unparsable_url = "nytimes.com/"
        _url_parser.client.captureException = Mock()
        _url_parser.URLParser().shorten_url(unparsable_url)
        _url_parser.client.captureException.assert_called_once()

    def test_is_base_url_error_is_handled_by_sentry_but_returns_false(self):
        unparsable_url = "nytimes.com/"
        _url_parser.client.captureMessage = Mock()
        self.assertFalse(_url_parser.URLParser().is_base_url(unparsable_url))
        _url_parser.client.captureException.assert_called_once()

    def test_batch_shorten_url(self):
        factories.FeedItemWithRawLookupUrlsFactory.create_batch(100)
        with suppress_printed_output():
            self.url_parser.batch_shorten_urls()
        feed_item = FeedItem.objects.last()
        self.assertEquals(feed_item.lookup_url, self.url_parser.shorten_url(feed_item.redirected_url))

    def test_shorten_urls_job_works(TestCase):
        factories.GenericFeedItemFactory.create_batch(100)
        with suppress_printed_output():
            call_command('shorten_urls')

class HTMLParserTestCase(TestCase):
    def setUp(self):
        self.html_parser = _html_parser.HTMLParser()
        self.base_content = "This is a story about crime."
        self.tagged_content = "<p>%s</p><script>var javascriptMethod = function(){console.log('sup')};</script><style>.content {abc: def}</style>" % self.base_content

    def test_pull_text_should_remove_html_css_and_js(self):
        self.assertEquals(self.html_parser.pull_text_from_html(self.tagged_content), self.base_content)

class FeedItemProcessorTestCase(TestCase):
    def setUp(self):
        self.html_parser = _html_parser.HTMLParser()

    def test_fields_properly_processed(self):
        shortened_description = "This is sentence 1. This is sentence 2. This is sentence 3 which is about Donald J. Trump. This is sentence 4. This is sentence 5."
        raw_description = "%s This is sentence 6. This is sentence 7." % shortened_description
        feed_item = factories.GenericFeedItemFactory(title="<p>title</p>", raw_description=raw_description)
        processed_feed_item = _feed_item_processor.FeedItemProcessor().process(feed_item)
        self.assertEquals(processed_feed_item.title, self.html_parser.pull_text_from_html(feed_item.title))
        self.assertEquals(processed_feed_item.raw_description, feed_item.raw_description)
        self.assertEquals(processed_feed_item.description, shortened_description)
        self.assertEquals(processed_feed_item.author, feed_item.author)
        self.assertEquals(processed_feed_item.url, feed_item.url)
        self.assertEquals(processed_feed_item.image_url, feed_item.image_url)
        self.assertEquals(processed_feed_item.publication_date, feed_item.publication_date)

class RSSEntryWrapperTestCase(TestCase):
    def setUp(self):
        self.feed = factories.GenericFeedFactory()
        self.rss_feed = feedparser.parse(WORKING_NYTIMES_RSS_URL)

    def test_pulls_correct_feeds(self):
        for entry in self.rss_feed.entries: # TODO: get a mock here
            wrapper = _rss_entry_wrapper.RSSEntryWrapper(self.feed, entry)
            self.assertEquals(wrapper.feed, self.feed)
            if hasattr(entry, 'description'):
                self.assertEquals(wrapper.raw_description, entry.description)
            if hasattr(entry, 'author'):
                self.assertEquals(wrapper.author, entry.author)
            if hasattr(entry, 'link'):
                self.assertEquals(wrapper.url, entry.link)
            if hasattr(entry, 'media_content'):
                self.assertEquals(wrapper.image_url, entry.media_content[0]["url"])
            if hasattr(entry, 'published'):
                self.assertEquals(wrapper.publication_date, dateutil.parser.parse(entry.published))
            if hasattr(entry, 'tags'):
                self.assertEquals(wrapper.tags, [tag.term for tag in entry.tags])

    def tests_key_error_in_job(TestCase):
        pass #TODO - test for media_content key error

class RSSFetcherTestCase(TestCase):
    def setUp(self):
        self.feed = factories.GenericFeedFactory(rss_url=WORKING_NYTIMES_RSS_URL)
        self.rss_feed = feedparser.parse(WORKING_NYTIMES_RSS_URL)
        
        crawler_mock = Mock()
        crawler_mock.return_value.crawl = None
        crawler_mock.return_value.start = None
        _rss_fetcher.CrawlerProcess = Mock(return_value=crawler_mock)
        self.crawler_mock = crawler_mock

        association_method_mock = Mock()
        association_method_mock.return_value.add = None
        _rss_fetcher.AddNewAssociations = Mock(return_value=association_method_mock)
        self.association_method_mock = association_method_mock

        self.rss_fetcher = _rss_fetcher.RSSFetcher()

    def test_debug_flags(self):
        factories.GenericFeedItemFactory.create_batch(10)
        rss_fetcher = _rss_fetcher.RSSFetcher(debug=True)
        self.assertEquals(rss_fetcher.feeds.count(), 3)
        rss_fetcher = _rss_fetcher.RSSFetcher(debug=False)
        self.assertEquals(rss_fetcher.feeds.count(), 11)

    def test_mocked_module_calls(self):
        self.rss_fetcher.fetch()
        _rss_fetcher.CrawlerProcess.assert_called_once()
        self.crawler_mock.crawl.assert_called_once()
        self.crawler_mock.start.assert_called_once()
        self.association_method_mock.add.assert_called_once()

    def test_database_persistence(self):
        self.rss_fetcher.fetch()
        for entry in self.rss_feed.entries:
            wrapper = _rss_entry_wrapper.RSSEntryWrapper(self.feed, entry)
            url = _url_parser.URLParser().clean_url(wrapper.url)
            feed_item = FeedItem.objects.get(url=url)
            self.assertIsInstance(feed_item, FeedItem)
            for tag_name in wrapper.tags:
                tag = Tag.objects.get(name=tag_name, feed_item=feed_item)
                self.assertIsInstance(tag, Tag)

    def test_works_if_duplicate_redirect_url(self):
        self.rss_fetcher.fetch()
        for entry in self.rss_feed.entries:
            wrapper = _rss_entry_wrapper.RSSEntryWrapper(self.feed, entry)
        feed_item = FeedItem.objects.last()
        url = feed_item.url
        feed_item.redirected_url = feed_item.url
        feed_item.url = "http://fake.com"
        self.rss_fetcher.fetch()
        self.assertEquals(feed_item.redirected_url, url)

    def test_call_command(self):
        with suppress_printed_output():
            call_command('rss_fetcher')

class CleanEntriesTestCase(TestCase):
    def setUp(self):
        factories.GenericFeedItemFactory.create_batch(1)
        feed_item_mock = Mock()
        feed_item_mock.return_value.save = None
        processor_method_mock = Mock()
        processor_method_mock.process = Mock(return_value=feed_item_mock)
        _clean_entries.FeedItemProcessor = Mock(return_value=processor_method_mock)

        self.feed_item_mock = feed_item_mock
        self.processor_method_mock = processor_method_mock

    def test_proper_calls(self):
        with suppress_printed_output():
            _clean_entries.CleanEntries().clean()
            _clean_entries.FeedItemProcessor.assert_called()
            self.processor_method_mock.process.assert_called()
            self.feed_item_mock.save.assert_called()

    def test_integrity_error_handling(self):
        with suppress_printed_output():
            self.feed_item_mock.save = Mock(side_effect=IntegrityError)
            _clean_entries.CleanEntries().clean()
            self.feed_item_mock.delete.assert_called()

    def test_call_command(self):
        with suppress_printed_output():
            call_command('clean_entries')

class AssociationsJobsTestCase(TestCase):
    def setUp(self):
        factories.GenericFeedItemFactory.create_batch(20, checked_for_associations=True)
        _add_new_associations.main = Mock()
        seed_base_associations.main = Mock()
        self.add_new_associations = _add_new_associations.AddNewAssociations()

    def test_proper_length_of_inputs(self):
        association_runner = _add_new_associations.AddNewAssociations()
        self.assertEquals(association_runner.old_feed_items.count(), 20)
        self.assertEquals(association_runner.new_feed_items.count(), 0)
        factories.GenericFeedItemFactory.create_batch(10, checked_for_associations=False)
        association_runner = _add_new_associations.AddNewAssociations()
        self.assertEquals(association_runner.new_feed_items.count(), 10)

    def test_tfidf_called_when_new_associations(self):
        with suppress_printed_output():
            self.add_new_associations.add()
            _add_new_associations.main.assert_not_called()
            already_checked = FeedItem.recent_items_eligible_for_association(settings.DAYS_TO_CHECK_FOR).filter(checked_for_associations=True)
            factories.GenericFeedItemFactory.create_batch(20, checked_for_associations=False)
            self.add_new_associations.add()
            _add_new_associations.main.assert_called_once()

    def test_add_associations_call_command(self):
        with suppress_printed_output():
            call_command('add_new_associations') # broken

    def test_seed_base_associations_call_command(self):
        with suppress_printed_output():
            call_command('seed_base_associations')

class TFIDFTestCase(TestCase):
    # TODO
    def setUp(self):
        pass

class ScrapyTestCase(TestCase):
    def setUp(self):
        self.html_content_blocks = ["<p>1234</p>", "<p>4567</p><script>7789</script>"]
        self.feed_item = factories.PreScrapeFeedItemFactory()
        response_mock = Mock()
        response_mock.meta = {'feed_item': self.feed_item}
        response_mock.url = "https://www.nytimes.com/test.html?rss=t"
        css_mock = Mock()
        css_mock.extract = Mock(return_value=self.html_content_blocks)
        response_mock.css = Mock(return_value=css_mock)
        self.spider = article_spider.ArticleSpider()
        article_spider.client.captureException = Mock()
        article_spider.client.captureMessage = Mock()
        response_mock.status = 200

        self.response_mock = response_mock

    def test_article_spider_content_parse(self):
        self.spider.save_content(self.response_mock)
        feed_item = FeedItem.objects.get(id=self.feed_item.id)
        self.assertEquals(feed_item.raw_content, " ".join(self.html_content_blocks))
        self.assertEquals(feed_item.content, "1234   4567")
        self.assertEqual(self.feed_item.redirected_url, _url_parser.URLParser().clean_url(self.response_mock.url))
        self.assertEqual(self.feed_item.lookup_url, _url_parser.URLParser().shorten_url(self.response_mock.url))

        self.assertEquals(self.spider.content_found, 1)

        created_log_item = ScrapyLogItem.objects.last()
        self.assertEquals(ScrapyLogItem.objects.count(), 1)
        self.assertEquals(created_log_item.feed_item, feed_item)
        self.assertTrue(created_log_item.content_tag_found)
        self.assertEquals(created_log_item.status_code, 200)

    def test_article_deleted_if_duplicate_url(self):
        self.feed_item.save = Mock(side_effect=IntegrityError)
        self.feed_item.delete = Mock()
        self.spider.save_content(self.response_mock)
        self.feed_item.delete.assert_called_once()
        article_spider.client.captureException.assert_called_once()

        self.assertEquals(ScrapyLogItem.objects.count(), 0)

    def test_article_spider_content_not_found_but_still_saves_url(self):
        self.html_content_blocks = []
        css_mock = Mock()
        css_mock.extract = Mock(return_value=self.html_content_blocks)
        self.response_mock.css = Mock(return_value=css_mock)
        self.spider.save_content(self.response_mock)
        self.assertEquals(self.spider.content_missing, 1)
        self.assertEqual(self.feed_item.redirected_url, _url_parser.URLParser().clean_url(self.response_mock.url))
        self.assertEqual(self.feed_item.lookup_url, _url_parser.URLParser().shorten_url(self.response_mock.url))

        created_log_item = ScrapyLogItem.objects.last()
        self.assertEquals(ScrapyLogItem.objects.count(), 1)
        self.assertEquals(created_log_item.feed_item, self.feed_item)
        self.assertFalse(created_log_item.content_tag_found)
        self.assertEquals(created_log_item.status_code, 200)

    def test_article_spider_http_error(self):
        self.response_mock.status = 422
        failure_mock = Mock()
        failure_mock.check = Mock(return_value=True)
        failure_mock.value.response = self.response_mock

        self.spider.error(failure_mock)
        self.assertEquals(self.spider.error_code_received, 1)

        created_log_item = ScrapyLogItem.objects.last()
        self.assertEquals(ScrapyLogItem.objects.count(), 1)
        self.assertEquals(created_log_item.feed_item, self.feed_item)
        self.assertFalse(created_log_item.content_tag_found)
        self.assertEquals(created_log_item.status_code, 422)

    def test_article_spider_other_error(self):
        failure_mock = Mock()
        failure_mock.check = Mock(return_value=False)
        failure_mock.request = self.response_mock

        self.spider.error(failure_mock)
        article_spider.client.captureMessage.assert_called_once()
        self.assertEquals(self.spider.other_error, 1)

        created_log_item = ScrapyLogItem.objects.last()
        self.assertEquals(ScrapyLogItem.objects.count(), 1)
        self.assertEquals(created_log_item.feed_item, self.feed_item)
        self.assertFalse(created_log_item.content_tag_found)
        self.assertEquals(created_log_item.status_code, 0)
        self.assertTrue(created_log_item.other_error, repr(failure_mock))

    def test_end_to_end(self):
        FeedItem.objects.all().delete()
        factories.PreScrapeFeedItemFactory(url="http://www.getthespectrum.com")
        with suppress_printed_output():
            article_scraper.settings.LOG_ENABLED=False 
            process = CrawlerProcess(get_project_settings())
            process.crawl('articles')
            process.start()
            self.assertEquals(ScrapyLogItem.objects.count(), 1)




