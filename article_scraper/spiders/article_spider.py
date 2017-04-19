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

class ArticleSpider(scrapy.Spider):
  name = "articles"

  def __init__(self, memory_threshold=2000, debug=False):
    self.debug = debug
    self.memory_threshold = memory_threshold
    self.content_found = 0
    self.content_missing = 0
    self.error_code_received = 0
    self.other_error = 0
    dispatcher.connect(self.spider_closed, signals.spider_closed)

  def spider_closed(self, spider):
    print("Processing complete, %s articles' content found, %s content missing, %s error code received, %s other error" % (self.content_found, self.content_missing, self.error_code_received, self.other_error))

  def start_requests(self):
    feed_items = self.__feed_items()
    for feed_item in feed_items:
      url = feed_item.url
      request = scrapy.Request(url=feed_item.url, callback=self.parse, errback=self.error)
      request.meta['feed_item'] = feed_item
      yield request

  def parse(self, response):
    feed_item = response.meta['feed_item']
    found_content = response.css(feed_item.feed.publication.html_content_tag).extract()

    if len(found_content):
      feed_item.raw_content = " ".join(response.css(feed_item.feed.publication.html_content_tag).extract()) 
       # this does a join since the content tag might have to be a repeating class (e.g. 'body-content-paragraph') as opposed to a single content div - implementations vary
      parsed_content = BeautifulSoup(feed_item.raw_content, 'html.parser').get_text(separator=u' ')
      feed_item.content = parsed_content.strip().replace(u'\xa0', u' ')
      try:
        feed_item.redirected_url = self.__clean_url(response.url)
        feed_item.lookup_url = self.__shorten_url(response.url)
        feed_item.save()
        self.content_found += 1
      except IntegrityError as e:
        client.captureException()
        feed_item.delete()
    else:
      self.content_missing += 1
      client.context.merge({'feed_item': feed_item, 'status': 200})
      client.captureMessage('Scrapy - Content Not Found')
      client.context.clear()


    ScrapyLogItem.objects.create(feed_item=feed_item, status_code=response.status, content_tag_found=len(found_content) > 0)
    yield None

  def error(self, failure):
    if failure.check(HttpError):
      response = failure.value.response
      client.context.merge({'feed_item': response.meta['feed_item'], 'status': response.status})
      ScrapyLogItem.objects.create(feed_item=response.meta['feed_item'], status_code=response.status, content_tag_found=False)
      client.captureMessage('Scrapy - HTTP Error')
      self.error_code_received += 1
    else:
      client.context.merge({'feed_item': failure.request.meta['feed_item'], 'status': 0, 'message': repr(failure)})
      ScrapyLogItem.objects.create(feed_item=failure.request.meta['feed_item'], status_code=0, content_tag_found=False, other_error=repr(failure))
      client.captureMessage('Scrapy - Other Error')
      self.other_error += 1

    client.context.clear()

  def __feed_items(self):
    if self.debug:
      publications = Publication.objects.all()[:3]
    else:
      publications = Publication.objects.all()

    urls = []
    total_items = 0
    for publication in publications:
      html_content_tag_present = publication.html_content_tag != ""
      if html_content_tag_present and not publication.skip_scraping:
        pub_count = 0
        paginator = Paginator(publication.feed_items(), self.memory_threshold)
        for page in range(1, paginator.num_pages + 1):
          publication_feed_items = paginator.page(page).object_list
          for feed_item in publication_feed_items:
            if feed_item.should_scrape():
              urls.append(feed_item)
              pub_count += 1

        print("Processing %s, %s items" % (publication.name, pub_count))
        total_items += pub_count

    print("Processing %s total items" % (total_items))
    return urls

  def __clean_url(self, raw_url):
    return URLParser().clean_url(raw_url)

  def __shorten_url(self, raw_url):
    return URLParser().shorten_url(raw_url)