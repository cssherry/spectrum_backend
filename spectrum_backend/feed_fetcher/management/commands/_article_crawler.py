import scrapy

class ArticleCrawler(scrapy.Spider):
  def start_requests(self, url, content_tag):
    print('Crawling %s' % url)
    self.content_tag = content_tag
    scrapy.Request(url=url, callback=self.__parse)

  def __parse(self, response):
    return response.css(self.content_tag)