from datetime import datetime
import re
import dateutil.parser

class RSSEntryWrapper:
  FOX_NEWS_PUBLICATION = "Fox News"

  def __init__(self, entry):
    self.entry = entry
    self.title = self.__parsed_title()
    self.description = self.__parsed_description()
    self.url = self.__parsed_url()
    self.author = self.__parsed_author()
    self.image_url = self.__parsed_image_url()
    self.publication_date = self.__parsed_publication_date()
    self.tags = self.__parsed_tags()

  def __parsed_title(self):
    if hasattr(self.entry, 'title'):
      return self.entry.title
    else:
      return None

  def __parsed_description(self):
    if hasattr(self.entry, 'description'):
      return self.entry.description
    elif feed.publication.name == self.FOX_NEWS_PUBLICATION:
      return self.__fox_news_description(self.entry.link)
    else:
      return None

  def __parsed_author(self):
    if hasattr(self.entry, 'author'):
      return self.entry.author
    else:
      return None

  def __parsed_url(self):
    query_param_delimiter = "?"
    if hasattr(self.entry, 'link'):
      return self.entry.link.split(query_param_delimiter)[0]
    else:
      return None

  def __parsed_image_url(self):
    if hasattr(self.entry, 'media_content') and self.entry.media_content[0]:
      return self.entry.media_content[0]["url"]
    else:
      return None

  def __parsed_publication_date(self):
    if hasattr(self.entry, 'published'):
      return dateutil.parser.parse(self.entry.published)
    else:
      return datetime.datetime.now() # TODO: find a better solution to this - maybe URL matching for date? Washington Post is culprit

  def __parsed_tags(self):
    tags = []
    if hasattr(self.entry, 'tags'):
      for tag in self.entry.tags:
        tags.append(tag.term)

    return tags

  def __fox_news_description(self, url):
    matches = re.search("^.+\/([a-zA-Z0-9\-]+).html$", url)
    if matches:
      return matches.group(1).replace("-", " ")
    else:
      return None
