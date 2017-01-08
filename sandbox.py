from spectrum_backend.feed_fetcher.models import Publication
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag
from django.core import serializers
from datetime import datetime, timedelta
import pprint
from spectrum_backend.feed_fetcher.management.commands._html_parser import HTMLParser
# from spectrum_backend.feed_fetcher.management.commands import ArticleCrawler

def articles_by_publication(limit = 5, include_extra_metadata = True, include_debug = False, include_ignored = False):
  """ Returns articles grouped by publication. See __return_item for specific fields
    `include_extra_metadata`: includes non-content fields like Author and image URL
    `include_debug`: includes raw content/description fields for parsing debugging
    `include_ignored`: includes feeds with non-supported feed content (e.g. business feeds)

  """
  pub_hash = {}
  for publication in Publication.objects.all():
    pub_hash[publication.name] = [__return_item(feed_item, include_extra_metadata, include_debug) for feed_item in publication.feed_items(include_ignored)[0:limit]]

  return pub_hash

def articles_by_feed(limit = 5, include_extra_metadata = True, include_debug = False, include_ignored = False):
  """ Returns articles grouped by publication and feed
    *Parameters are the same as articles_by_publication
  """
  feed_hash = {}
  for feed in Feed.all(include_ignored):
    name = "%s - %s" % (feed.publication.name, feed.category)
    feed_hash[name] = [__return_item(feed_item, include_extra_metadata, include_debug) for feed_item in feed.feeditem_set.all()[0:limit]]

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

def articles_within_timeframe_in_hours(hours):
  """ Returns selected fields for all objects of a class
    `cls`: The class you want to JSON
    `fields`: The fields you want to pluck, in list format (e.g. `('name', 'created_at')`)
  """
  time_threshold = datetime.now() - timedelta(hours=hours)
  return FeedItem.objects.filter(created_at__gt=time_threshold)

def delete_last_fetch():
  """ Deletes most recent fetch within past hour. Be careful!"""
  return articles_within_timeframe_in_hours(1).delete()

def articles_by_publication_date():
  """ Returns all articles sorted by publication date, most recent first"""
  return [__return_item(feed_item) for feed_item in FeedItem.objects.all()]

def pp(object):
  """ Pretty prints an object or set of objects"""
  return pprint.PrettyPrinter(indent=2, width=200).pprint(object)

def __return_item(item, include_extra_metadata, include_debug):
  base_object = {
    "      publication_name": item.publication_name(),
    "     feed_category": item.feed_category(),
    "    title": item.title,
    "   summary": item.summary,
    "  description": item.description,
    " url": item.url
  }
  rest_of_object = {
    "author": item.author,
    "image_url": item.image_url,
    "publication_bias": item.publication_bias(),
    "publication_date": item.publication_date,
    "publication_date_friendly": item.friendly_publication_date(),
    "tags": item.tags(),
  }

  debug = {
    "  description (raw)": item.raw_description,
  }
  if include_extra_metadata:
    base_object.update(rest_of_object)

  if include_debug:
    base_object.update(debug) 

  return base_object

