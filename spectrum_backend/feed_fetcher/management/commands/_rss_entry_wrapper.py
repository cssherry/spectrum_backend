import re
import dateutil.parser
from django.utils import timezone

class RSSEntryWrapper:
  def __init__(self, feed, entry):
    self.entry = entry
    self.feed = feed
    self.title = self.__parsed_title()
    self.url = self.__parsed_url()
    self.raw_description = self.__parsed_description()
    self.author = self.__parsed_author()
    self.image_url = self.__parsed_image_url()
    self.publication_date = self.__parsed_publication_date()
    self.tags = self.__parsed_tags()

  def __matches_element_format(self, element_name):
    return hasattr(self.entry, element_name)

  def __parsed_title(self):
    if self.__matches_element_format('title'):
      return self.entry.title
    else:
      return None

  def __parsed_description(self):
    if self.__matches_element_format('description'):
      return self.entry.description
    else:
      return None

  def __parsed_author(self):
    if self.__matches_element_format('author'):
      return self.entry.author
    else:
      return None

  def __parsed_url(self):
    if self.__matches_element_format('link'):
      return self.entry.link
    else:
      return None

  def __parsed_image_url(self):
    if self.__matches_element_format('media_content') and self.entry.media_content[0]:
      return self.entry.media_content[0]["url"]
    else:
      return None

  def __parsed_publication_date(self):
    if self.__matches_element_format('published'):
      return dateutil.parser.parse(self.entry.published)
    else:
      return timezone.now() # TODO: find a better solution to this - maybe URL matching for date? Washington Post is culprit

  def __parsed_tags(self):
    tags = []
    if self.__matches_element_format('tags'):
      for tag in self.entry.tags:
        tags.append(tag.term)

    return tags
