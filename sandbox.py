from spectrum_backend.feed_fetcher.models import Publication
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag
from spectrum_backend.feed_fetcher.models import Association
from spectrum_backend.feed_fetcher.models import ScrapyLogItem
from django.core import serializers
from datetime import datetime, timedelta
import random
import pprint
import json
import os
import codecs
import sys
from spectrum_backend.feed_fetcher.management.commands._html_parser import HTMLParser
from spectrum_backend.feed_fetcher.management.commands import _batch_query_set
from spectrum_backend.feed_fetcher.management.commands import tfidf

def single_article_association(url):
  tfidf.main(FeedItem.recent_items_eligible_for_association(), FeedItem.objects.filter(redirected_url=url))

def articles_by_publication(limit = 5, include_extra_metadata = True, include_debug = False, include_ignored = False, include_empty = False):
  """ Returns articles grouped by publication. See __return_item for specific fields
    `include_extra_metadata`: includes non-content fields like Author and image URL
    `include_debug`: includes raw content/description fields for parsing debugging
    `include_ignored`: includes feeds with non-supported feed content (e.g. business feeds)
    `include_empty`: includes feeds with empty content (e.g. podcast articles, items that were unsuccessfully pulled)
  """
  pub_hash = {}
  for publication in Publication.objects.all():
    pub_hash[publication.name] = [__return_item(feed_item, include_extra_metadata, include_debug) for feed_item in publication.feed_items(include_ignored, include_empty)[0:limit]]

  return pub_hash

def articles_by_feed(limit = 5, include_extra_metadata = True, include_debug = False, include_ignored = False, include_empty = False):
  """ Returns articles grouped by publication and feed
    *Parameters are the same as articles_by_publication
  """
  feed_hash = {}
  for feed in Feed.all(include_ignored):
    name = "%s - %s" % (feed.publication.name, feed.category)
    feed_hash[name] = [__return_item(feed_item, include_extra_metadata, include_debug) for feed_item in feed.feed_items(include_empty)[0:limit]]

  return feed_hash

def one_of_each():
  """ Returns one article example from each feed. My favorite debugging method"""
  return articles_by_feed(limit = 1, include_extra_metadata = False)

def articles_with_content():
  return FeedItem.objects.exclude(content__isnull=True).exclude(content__exact='')

def empty_content_report():
  for feed in Feed.objects.all():
    feed.display_empty_content_report()

def debug_publication_content_tags(show_failures=False):
  success = set()
  content_failure = set()
  http_failure = set()
  other_error = set()

  for start, end, total, log_items in batch_query_set(ScrapyLogItem.objects.all()):
    for scrapyLogItem in log_items:
      feed_item = scrapyLogItem.feed_item
      if scrapyLogItem.status_code != 200:
        http_failure.add(feed_item)
      elif not scrapyLogItem.content_tag_found:
        content_failure.add(feed_item)
      elif scrapyLogItem.other_error:
        other_error.add(feed_item)
      else:
        success.add(feed_item)

  pub_dict = {}
  for publication in Publication.objects.all():
    pub_dict[publication.name] = {"success": 0, "content_failure": 0, "http_failure": 0, "other_error": 0}

  for feed_item in content_failure:
    pub_dict[feed_item.publication_name()]["content_failure"] += 1

  for feed_item in success:
    pub_dict[feed_item.publication_name()]["success"] += 1

  for feed_item in http_failure:
    pub_dict[feed_item.publication_name()]["http_failure"] += 1

  for feed_item in other_error:
    pub_dict[feed_item.publication_name()]["other_error"] += 1

  pprint.PrettyPrinter(indent=2, width=200).pprint(pub_dict)

  if show_failures:
    for feed_item in content_failure:
      print("%s %s" % (feed_item.publication_name(), feed_item.url))

def download_bias_json():
  """ Downloads bias JSON by bias """
  bias_hash = {"L": [], "C": [], "R": []}
  for feed_item in FeedItem.objects.exclude(content__isnull=True).exclude(content__exact='')[:500]:
    bias = feed_item.feed.publication.bias
    item = __return_item(feed_item, include_extra_metadata=True, include_debug=False)
    if bias == "L" or bias == "LC":
      bias_hash["L"].append(item)
    elif bias == "C":
      bias_hash["C"].append(item)
    else:
      bias_hash["R"].append(item)

  download_json('data.json', bias_hash)

def download_json(file_name, input_dict):
  fileSystemEncoding = sys.getfilesystemencoding()
  output_file = os.path.expanduser(u'./' + file_name)
  with codecs.open(output_file,
                   encoding=fileSystemEncoding,
                   mode="w") as f:
    j = json.dumps(input_dict, indent=1, sort_keys=True, separators=(',', ': '))
    f.write(j)

def serialize_for_fixture(file_name, query_set):
  data = json.loads(serializers.serialize("json", query_set))
  download_json(file_name, data)

def seed_associations():
  items = FeedItem.objects.all()[:10]
  other_items = FeedItem.objects.all()[11:21]
  for item in items:
    for other_item in other_items:
      Association.objects.create(base_feed_item=item, associated_feed_item=other_item, similarity_score=random.uniform(0, 1))

def to_json(cls):
  """ Returns all fields for all objects of a class
    `cls`: The class you want to JSON 
  """
  return serializers.serialize('json', cls.objects.all())

def pluck(cls, fields):
  """ Returns selected fields for all objects of a class
    `cls`: The class you want to JSON
    `fields`: The fields you want to pluck, in list format (e.g. `('name', 'created_at')`)
  """
  return serializers.serialize('json', cls.objects.all(), fields=fields)

# def fox_news_urls_to_scrape():

def articles_within_timeframe_in_hours(hours):
  """ Returns selected fields for all objects of a class
    `cls`: The class you want to JSON
    `fields`: The fields you want to pluck, in list format (e.g. `('name', 'created_at')`)
  """
  time_threshold = datetime.now() - timedelta(hours=hours)
  return FeedItem.objects.filter(created_at__gt=time_threshold)

def delete_last_fetch():
  """ Deletes most recent fetch within past hour. Be very careful in production!"""
  return articles_within_timeframe_in_hours(1).delete()

def articles_by_publication_date():
  """ Returns all articles sorted by publication date, most recent first"""
  return [__return_item(feed_item) for feed_item in FeedItem.objects.all()]

def pp(object):
  """ Pretty prints an object or set of objects"""
  return pprint.PrettyPrinter(indent=2, width=200).pprint(object)

def __return_item(item, include_extra_metadata, include_debug):
  base_object = item.base_object()

  debug = {
    "description (raw)": item.raw_description,
    "content (raw)": item.raw_content,
  }

  if include_debug:
    base_object.update(debug)

  return base_object

