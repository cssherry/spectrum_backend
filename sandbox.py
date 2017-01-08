from spectrum_backend.feed_fetcher.models import Publication
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag
from spectrum_backend.feed_fetcher.management.commands._html_parser import HTMLParser
# from spectrum_backend.feed_fetcher.management.commands import ArticleCrawler

def articles_by_publication(limit = 5, include_extra_metadata = False, include_debug = False, include_ignored = False):
  pub_hash = {}
  for publication in Publication.objects.all():
    pub_hash[publication.name] = [__return_item(feed_item, include_extra_metadata, include_debug) for feed_item in publication.feed_items(include_ignored)[0:limit]]

  return pub_hash

def articles_by_feed(limit = 5, include_extra_metadata = True, include_debug = False, include_ignored = False):
  feed_hash = {}
  for feed in Feed.all(include_ignored):
    name = "%s - %s" % (feed.publication.name, feed.category)
    feed_hash[name] = [__return_item(feed_item, include_extra_metadata, include_debug) for feed_item in feed.feeditem_set.all()[0:limit]]

  return feed_hash

def articles_by_publication_date():
  return [__return_item(feed_item) for feed_item in FeedItem.objects.all()]

def __return_item(item, include_extra_metadata, include_debug):
  base_object = {
    "     publication_name": item.publication_name(),
    "    feed_category": item.feed_category(),
    "   title": HTMLParser().pull_text_from_html(item.title),
    "  description": HTMLParser().pull_description_from_html(item.raw_description),
    " url": item.url,
    
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
    "   title (raw)": item.title,
    "  description (raw)": item.raw_description,
  }
  if include_extra_metadata:
    base_object.update(rest_of_object)

  if include_debug:
    base_object.update(debug) 

  return base_object
