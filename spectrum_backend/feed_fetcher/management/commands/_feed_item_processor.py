import re
import dateutil.parser
from django.utils import timezone
from ._html_parser import HTMLParser
from ._url_parser import URLParser
from nltk.tokenize import sent_tokenize
import nltk

class FeedItemProcessor:
  DESCRIPTION_MAX_SENTENCES = 5

  def process(self, feed_item):
    self.feed_item = feed_item
    self._process_title()
    self._process_raw_description()
    self._process_content_fields()
    self._process_author()
    self._process_image_url()
    self._process_url()
    self._process_publication_date()

    return self.feed_item

  def _process_title(self):
    self.feed_item.title = HTMLParser().pull_text_from_html(self.feed_item.title)

  def _process_raw_description(self):
    pass

  def _process_content_fields(self):
    description_text = HTMLParser().pull_text_from_html(self.feed_item.raw_description)
    description_sentences = sent_tokenize(description_text)
    self.feed_item.description = " ".join(description_sentences[0:self.DESCRIPTION_MAX_SENTENCES])

  def _process_author(self):
    pass

  def _process_url(self):
    # redirected_url and lookup_url are processed during scraping. TODO come up with alternative manual method for the same
    pass

  def _process_image_url(self):
    pass

  def _process_publication_date(self):
    pass
