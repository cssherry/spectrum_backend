import re
import dateutil.parser
from django.utils import timezone
from ._html_parser import HTMLParser
from ._url_parser import URLParser
from nltk.tokenize import sent_tokenize

class FeedItemProcessor:
  SUMMARY_MAX_SENTENCES = 1
  DESCRIPTION_MAX_SENTENCES = 5

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
    if self.feed_item.raw_description == "":
      self.feed_item.raw_description = URLParser().pull_description_from_url(self.feed_item.url)

  def __process_content_fields(self):
    description_text = HTMLParser().pull_content_from_html(self.feed_item.raw_description)
    description_sentences = sent_tokenize(description_text)
    self.feed_item.summary = " ".join(description_sentences[0:self.SUMMARY_MAX_SENTENCES])

    if len(description_sentences) > self.SUMMARY_MAX_SENTENCES:
      self.feed_item.description = " ".join(description_sentences[0:self.DESCRIPTION_MAX_SENTENCES])

    if len(description_sentences) > self.DESCRIPTION_MAX_SENTENCES:
      self.feed_item.content = " ".join(description_sentences)

    if self.feed_item.raw_content != "":
      content_text = HTMLParser().pull_content_from_html(self.feed_item.raw_content)
      self.feed_item.content = content_text
      content_sentences = sent_tokenize(content_text)

      if self.feed_item.description == "" or len(description_sentences) < self.DESCRIPTION_MAX_SENTENCES:
        self.feed_item.description = " ".join(content_sentences[0:self.DESCRIPTION_MAX_SENTENCES])

  def __process_author(self):
    pass

  def __process_url(self):
    query_param_delimiter = "?"
    return self.feed_item.url.split(query_param_delimiter)[0]

  def __process_image_url(self):
    pass

  def __process_publication_date(self):
    pass
