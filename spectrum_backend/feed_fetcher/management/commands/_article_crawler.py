import scrapy

class ArticleCrawler(scrapy.Spider):
  name = "fred"

  def start_requests(self, url, content_tag, feed_item):
    print('Crawling %s' % url)
    self.content_tag = content_tag
    self.feed_item = feed_item
    yield scrapy.Request(url=url, callback=self.__parse)

  def __parse(self, response):
    content = response.css(self.content_tag)
    self.feed_item.raw_content = raw_content
    parsed_content = HTMLParser.pull_description_from_html(raw_content)
    self.feed_item.content = parsed_content
    self.feed_item.save()