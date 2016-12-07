from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from spectrum_backend.feed_fetcher.models import Feed
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Tag
from datetime import datetime
import feedparser
import re
from urllib import parse
from dateutil import parser

class Command(BaseCommand):
  def handle(self, *args, **options):
    FOX_NEWS_PUBLICATION = "Fox News"
    total_counter = 0
    for feed in Feed.objects.all():
      d = feedparser.parse(feed.rss_url)
      self.stdout.write(self.style.SUCCESS('Parsing items from %s (%s) - %s' % (feed.publication.name, feed.category, feed.rss_url)))
      feed_counter = 0

      for entry in d.entries:
        feed_counter += 1
        description = self.__fox_news_description(entry.link) if (feed.publication.name == FOX_NEWS_PUBLICATION) else entry.description
        image_url = entry.media_content[0]["url"] if (hasattr(entry, 'media_content') and entry.media_content[0]) else None
        author = entry.author if (hasattr(entry, 'author')) else None
        try:
          feed_item = FeedItem(feed=feed, title=entry.title, description=description, author=author, url=self.__parsed_url(entry.link), image_url=image_url, publication_date=parser.parse(entry.published))
          feed_item.save()
          if hasattr(entry, 'tags'):
            for tag in entry.tags:
              try:
                tag = Tag(name=tag.term, feed_item=feed_item).save()
              except IntegrityError as e:
                pass
        except IntegrityError as e:
          pass


  # TODO: Move all these to model validations/clean
  def __parsed_url(self, url_string):
    query_param_delimiter = "?"
    return url_string.split(query_param_delimiter)[0]

  def __fox_news_description(self, url):
    matches = re.search("^.+\/([a-zA-Z0-9\-]+).html$", url)
    if matches:
      matches.group(1).replace("-", " ")
    else:
      nil
