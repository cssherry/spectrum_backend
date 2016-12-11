import nltk
import dateutil.parser
from django.utils import timezone
import re

class TagWrapper:

  def __init__(self, name):
    self.name = name
    self.words = self.__parsed_words()

  def has_tags(self):
    return self.words

  def __parsed_words(self):
    words = []

    named_units = self.__categorize_and_separate_tag()

    for chunk in named_units:
      words.append(TagWordWrapper(chunk))

    return words

  def __categorize_and_separate_tag(self):
    if self.__proper_name_matches():
      return self.__proper_name_matches()

    return []

  def __proper_name_matches(self):
    matches = re.search("^[A-Za-z]+, [A-Za-z ]+$", self.name)
    not_a_list = not re.search(" and ", self.name)
    if matches and not_a_list:
      name_array = self.name.split(', ')
      last_name = name_array[0]
      full_name = name_array[1] + " " + last_name
      full_name_with_initial = name_array[1] + ". " + last_name
      if last_name.lower() in set(nltk.corpus.words.words()):
        return [full_name, full_name_with_initial]
      else:
        return [full_name, last_name]
    else:
      return None

class TagWordWrapper:
  UNCATEGORIZED_TYPE = 'XX'
  def __init__(self, name):
    self.stem = name
    self.pos_type = self.UNCATEGORIZED_TYPE

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


