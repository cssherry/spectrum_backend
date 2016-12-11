import nltk
import dateutil.parser
from django.utils import timezone

class TagWrapper:

  def __init__(self, name):
    self.name = name
    self.words = []

  def __parsed_words(self):
    for word in " ".split(self.name):
      self.words << TagWordWrapper(word) # lemmatize

  def __parsed_title(self):
    if hasattr(self.entry, 'title'):
      return self.entry.title
    else:
      return None

  def __parsed_description(self):
    if hasattr(self.entry, 'description'):
      return self.entry.description
    elif self.feed.publication.name == self.FOX_NEWS_PUBLICATION:
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
      return timezone.now() # TODO: find a better solution to this - maybe URL matching for date? Washington Post is culprit

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

class TagWordWrapper:
  def __init__(self, name):
    self.stem = name
    self.pos_type = "CD" # need to parse by speech with NLTK here

  def __get_continuous_chunks(self, text):
    chunked = ne_chunk(pos_tag(word_tokenize(text)))
    prev = None
    continuous_chunk = []
    current_chunk = []
    for i in chunked:
      if type(i) == Tree:
        current_chunk.append(" ".join([token for token, pos in i.leaves()]))
      elif current_chunk:
        named_entity = " ".join(current_chunk)
        if named_entity not in continuous_chunk:
          continuous_chunk.append(named_entity)
          current_chunk = []
      else:
        continue
    return continuous_chunk
