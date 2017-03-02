from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
# import nltk


class Publication(models.Model):
    BIASES = (
        ('L', 'Left'),
        ('LC', 'Left-Center'),
        ('C', 'Center'),
        ('RC', 'Right-Center'),
        ('R', 'Right'),
    )
    name = models.CharField(max_length=500, unique=True)
    base_url = models.CharField(max_length=500, unique=True)
    bias = models.CharField(max_length=2, choices=BIASES)
    html_content_tag = models.CharField(max_length=500, default="")
    skip_scraping = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'%s (%s)' % (self.name, self.bias)

    class Meta:
        ordering = ['name']

    def tags(self):
        tags = set()
        [tags.update(feed.tags()) for feed in self.feed_set.all()]
        return tags

    def feeds(self, include_ignored=True):
        if include_ignored:
            return self.feed_set.all()
        else:
            return self.feed_set.filter(should_ignore=0)

    def feed_items(self, include_ignored=True, include_empty=True):
        feed_items = []
        [feed_items.extend(feed.feed_items(include_empty))
         for feed in Feed.all(include_ignored).filter(publication=self)]
        return feed_items


class Feed(models.Model):
    publication = models.ForeignKey('Publication')
    category = models.CharField(max_length=500)
    rss_url = models.CharField(max_length=500, unique=True)
    should_ignore = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def all(cls, include_ignored=True):
        if include_ignored:
            return cls.objects.all()
        else:
            return cls.objects.filter(should_ignore=0)

    def feed_items(self, include_empty=True):
        if include_empty:
            return self.feeditem_set.all()
        else:
            return self.feeditem_set.exclude(summary="")

    def display_empty_content_report(self):
        empty_feed_items = self.feed_items().filter(content='')
        percentage = empty_feed_items.count()/(self.feed_items().count() or 1)
        if percentage > 0.5:
            broken_string = "BROKEN"
        else:
            broken_string = ""

        print("For %s (%s) there are %s empty articles out of %s %s" % (
            self.publication.name, self.category, empty_feed_items.count(),
            self.feed_items().count(), broken_string))

    def __str__(self):
        return u'%s - %s (%s)' % (self.publication.name, self.category,
                                  self.rss_url)

    class Meta:
        ordering = ['publication__name']

    def tags(self):
        tags = set()
        [tags.update(feed_item.tags()) for feed_item in
         self.feeditem_set.all()]
        return tags


class FeedItem(models.Model):
    feed = models.ForeignKey('Feed')
    title = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000, default="")
    summary = models.TextField(default="") # 1-2 lines from RSS feed description
    description = models.TextField(default="") # 8-10 sentences from RSS feed or scraper
    content = models.TextField(default="") # content of article, pulled either from RSS feed or scraping
    raw_description = models.TextField(default="") # raw description from RSS feed
    raw_content = models.TextField(default="") # raw contents of web scrape
    publication_date = models.DateTimeField()
    url = models.CharField(max_length=1000, unique=True)
    image_url = models.CharField(max_length=1000, default="")
    self_score = models.FloatField(default=0)
    frequency_dictionary = JSONField(default={})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def items_eligible_for_similarity_score(cls):
        return cls.objects.exclude(content__exact="")

    @classmethod
    def get_fields(cls, list):
        items = []
        for item in list:
            items.append(item.base_object())
        return items

    def tags(self):
        return set([tag.name for tag in self.tag_set.all()])

    def publication_name(self):
        return self.feed.publication.name

    def publication_bias(self):
        return self.feed.publication.bias

    def not_created_recently(self):
        return self.created_at < timezone.now() - timedelta(days=2)

    def content_missing_from_scrape(self):
        if self.not_created_recently():
            return self.content == ""
        else:
            return False

    def feed_category(self):
        return self.feed.category

    def short_description(self):
        if len(self.raw_description) > 30:
            return "%s..." % self.raw_description[0:30]
        else:
            return self.raw_description

    def friendly_publication_date(self):
        return self.publication_date.strftime("%Y-%m-%d %H:%M:%S")

    def base_object(self, similarity_score=None):
        base_object = {
            "publication_name": self.publication_name(),
            "publication_bias": self.publication_bias(),
            "feed_category": self.feed_category(),
            "title": self.title,
            "summary": self.summary,
            "description": self.description,
            "content": self.content,
            "url": self.url,
            "author": self.author,
            "image_url": self.image_url,
            "publication_date": self.friendly_publication_date(),
            "tags": list(self.tags()),
        }
        if similarity_score:
            base_object["similarity_score"] = similarity_score

        return base_object

    def top_associations(self, count=3):
        associated_articles = []
        for association in self.base_associations.all():
            associated_articles.append(
                association.associated_feed_item.base_object(
                    association.similarity_score))

        return associated_articles[:3]

    def __str__(self):
        return u'%s (%s - %s) %s (%s) %s' % (
            self.title, self.publication_name(), self.feed_category(),
            self.short_description(), self.url,
            self.friendly_publication_date())

    class Meta:
        ordering = ['-publication_date']


class Tag(models.Model):
    name = models.CharField(max_length=500)
    feed_item = models.ForeignKey('FeedItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'%s' % (self.name)

    class Meta:
        unique_together = ('name', 'feed_item')

    def publication_name(self):
        return self.feed_item.feed.publication.name


class Association(models.Model):
    base_feed_item = models.ForeignKey('FeedItem',
                                       related_name='base_associations')
    associated_feed_item = models.ForeignKey('FeedItem',
                                             related_name='associated_associations')
    similarity_score = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'*BASE* %s *ASSOCIATION* %s (%s)' % (
            self.base_feed_item.title,
            self.associated_feed_item.title,
            self.similarity_score)

    class Meta:
        ordering = ['-similarity_score']


class CorpusWordFrequency(models.Model):
    dictionary = JSONField()
