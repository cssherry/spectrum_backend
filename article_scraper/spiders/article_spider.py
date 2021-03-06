import scrapy
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Publication
from spectrum_backend.feed_fetcher.models import ScrapyLogItem
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher
from scrapy.spidermiddlewares.httperror import HttpError
from django.db.utils import IntegrityError
from django.core.paginator import Paginator
from raven.contrib.django.raven_compat.models import client
from spectrum_backend.feed_fetcher.management.commands._url_parser import URLParser
from spectrum_backend.feed_fetcher.management.commands._html_parser import HTMLParser

class ArticleSpider(scrapy.Spider):
    name = "articles"

    def __init__(self, debug=False):
        self.debug = debug
        self.content_found = 0
        self.content_missing = 0
        self.error_code_received = 0
        self.other_error = 0
        dispatcher.connect(self.spider_closed, signals.spider_closed)
    
    def spider_closed(self, spider):
        print("Processing complete, %s articles' content found, %s content missing, %s error code received, %s other error" % (self.content_found, self.content_missing, self.error_code_received, self.other_error))
    
    def start_requests(self):
        for feed_item in FeedItem.feed_items_urls_to_scrape(verbose=True, debug=self.debug):
            url = feed_item.url
            request = scrapy.Request(url=feed_item.url, callback=self.parse, errback=self.error)
            request.meta['feed_item'] = feed_item
            yield request
    
    def parse(self, response):
        self.save_content(response)
        yield None
    
    def save_content(self, response):
        feed_item = response.meta['feed_item']
        found_content_blocks = response.css(feed_item.feed.publication.html_content_tag).extract()
        if len(found_content_blocks):
            feed_item.raw_content = " ".join(found_content_blocks)
            feed_item.content = self.__clean_html(feed_item.raw_content)
        else:
            self.content_missing += 1
        try:
            feed_item.redirected_url = self.__clean_url(response.url)
            feed_item.lookup_url = self.__shorten_url(response.url)
            feed_item.save()
            self.content_found += 1
        except IntegrityError as e:
            feed_item.delete()
            return
        
        ScrapyLogItem.objects.create(feed_item=feed_item, status_code=response.status, content_tag_found=len(found_content_blocks) > 0)
    
    
    def error(self, failure):
        if failure.check(HttpError):
            response = failure.value.response
            ScrapyLogItem.objects.create(feed_item=response.meta['feed_item'], status_code=response.status, content_tag_found=False)
            self.error_code_received += 1
        else:
            ScrapyLogItem.objects.create(feed_item=failure.request.meta['feed_item'], status_code=0, content_tag_found=False, other_error=repr(failure))
            self.other_error += 1
        
        # client.context.clear()
    
    def __clean_html(self, raw_html):
        return HTMLParser().pull_text_from_html(raw_html)
    
    def __clean_url(self, raw_url):
        return URLParser().clean_url(raw_url)
    
    def __shorten_url(self, raw_url):
        return URLParser().shorten_url(raw_url) 