from spectrum_backend.feed_fetcher.models import Publication
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag

def articles_by_publication(limit = None):
  pub_hash = {}
  for publication in Publication.objects.all():
    pub_hash[publication.name] = [__return_item(feed_item) for feed_item in publication.feed_items()[0:limit]]

  return pub_hash

def articles_by_publication_date():
  return [__return_item(feed_item) for feed_item in FeedItem.objects.all()]

def __return_item(item):
  return {
    "publication_name": item.publication_name(),
    "publication_bias": item.publication_bias(),
    "feed_category": item.feed_category(),
    "title": item.title,
    "author": item.author,
    "description": item.description,
    "tags": item.tags(),
    "url": item.url,
    "publication_date": item.publication_date,
  }