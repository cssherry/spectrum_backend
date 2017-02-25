import scrapy
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Publication
import re
from bs4 import BeautifulSoup

class ArticleSpider(scrapy.Spider):
  name = "articles"

  def start_requests(self):
    feed_items = self.__feed_items()
    counter = 0
    for feed_item in feed_items:
      counter += 1
      self.log(counter)
      url = feed_item.url
      request = scrapy.Request(url=feed_item.url, callback=self.parse)
      request.meta['feed_item'] = feed_item
      yield request

  def parse(self, response):
    feed_item = response.meta['feed_item']
    feed_item.raw_content = " ".join(response.css(feed_item.feed.publication.html_content_tag).extract())
    parsed_content = BeautifulSoup(feed_item.raw_content, 'html.parser').get_text(separator=u' ')
    feed_item.content = parsed_content.strip().replace(u'\xa0', u' ')
    self.log("%s %s" % (feed_item.id, feed_item.feed.publication))

    feed_item.save()
    yield None

  def __feed_items(self):
    urls = []
    for publication in Publication.objects.all():
      if publication.html_content_tag != "" and not publication.skip_scraping:
        print("Processing %s, %s items" % (publication.name, len(publication.feed_items())))
        for feed_item in publication.feed_items():
          if feed_item.raw_content == "":
            urls.append(feed_item)

    return urls