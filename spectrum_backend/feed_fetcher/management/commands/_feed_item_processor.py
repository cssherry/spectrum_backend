import re
import dateutil.parser
from django.utils import timezone
from ._html_parser import HTMLParser
from ._url_parser import URLParser

class FeedItemProcessor:
  SUMMARY_MAX_SENTENCES = 3
  DESCRIPTION_MAX_SENTENCES = 10

  def process(self, feed_item):
    self.feed_item = feed_item
    self.__process_title()
    self.__process_raw_description()
    self.__process_content_fields()
    self.__process_author()
    self.__process_image_url()
    self.__process_url()
    self.__process_publication_date()

    return self.feed_item

  def __process_title(self):
    self.feed_item.title = HTMLParser().pull_text_from_html(self.feed_item.title)

  def __process_raw_description(self):
    if self.feed_item.description == "":
      self.feed_item.raw_description = URLParser().pull_description_from_url(self.feed_item.url)

  def __process_content_fields(self):
    sentence_delimiter = '. '
    sentence_divider_reg_exp = '(?<=[a-z0-9])\. (?=[A-Z0-9])'
    description_text = HTMLParser().pull_description_from_html(self.feed_item.raw_description)
    sentences = re.split(sentence_divider_reg_exp, str)
    self.summary = sentences[0:self.SUMMARY_MAX_SENTENCES].join(sentence_delimiter)

    if len(sentences) > self.SUMMARY_MAX_SENTENCES:
      self.description = sentences[0:self.DESCRIPTION_MAX_SENTENCES].join(sentence_delimiter)

    if len(sentences) > self.DESCRIPTION_MAX_SENTENCES:
      self.content = sentences.join(sentence_delimiter)

  def __process_author(self):
    pass

  def __process_url(self):
    query_param_delimiter = "?"
    return url.split(query_param_delimiter)[0]

  def __process_image_url(self):
    pass

  def __process_publication_date(self):
    pass
