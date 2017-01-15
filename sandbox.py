from spectrum_backend.feed_fetcher.models import Publication
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag
from django.core import serializers
from datetime import datetime, timedelta
import pprint
from spectrum_backend.feed_fetcher.management.commands._html_parser import HTMLParser

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
  base_object = {
    "1. publication_name": item.publication_name(),
    "2. publication_bias": item.publication_bias(),
    "3. feed_category": item.feed_category(),
    "4. title": item.title,
    "5. summary": item.summary,
    "6. description": item.description,
    "7. content": item.content,
    "8. url": item.url,
  }
  rest_of_object = {
    "9. author": item.author,
    "10. image_url": item.image_url,
    "11. publication_date": item.publication_date,
    "12. publication_date_friendly": item.friendly_publication_date(),
    "13. tags": item.tags(),
  }

  debug = {
    "description (raw)": item.raw_description,
    "content (raw)": item.raw_content,
  }
  if include_extra_metadata:
    base_object.update(rest_of_object)

  if include_debug:
    base_object.update(debug) 

  return base_object

