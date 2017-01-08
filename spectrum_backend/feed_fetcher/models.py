from django.db import models
import nltk

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
  html_content_tag = models.CharField(max_length=500)
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

  def feed_items(self, include_ignored=True):
    feed_items = []
    [feed_items.extend(feed.feeditem_set.all()) for feed in Feed.all(include_ignored).filter(publication=self)]
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

  def __str__(self):
    return u'%s - %s (%s)' % (self.publication.name, self.category, self.rss_url)

  class Meta:
    ordering = ['category'] # any way to do this by publication name + category?

  def tags(self):
    tags = set()
    [tags.update(feed_item.tags()) for feed_item in self.feeditem_set.all()]
    return tags

class FeedItem(models.Model): # TODO: figure out how to order this earlier so Topic doesn't through error
  feed = models.ForeignKey('Feed')
  title = models.CharField(max_length=500)
  author = models.CharField(max_length=500, default="")
  summary = models.CharField(max_length=500, default="") # 1-2 lines from RSS feed description
  description = models.CharField(max_length=500, default="") # 8-10 sentences from RSS feed or scraper
  content = models.TextField(default="") # content of article, pulled either from RSS feed or scraping
  raw_description = models.TextField(default="") # raw description from RSS feed
  raw_content = models.TextField(default="") # raw contents of web scrape
  publication_date = models.DateTimeField()
  url = models.CharField(max_length=500, unique=True)
  image_url = models.CharField(max_length=500, default="")
  topics = models.ManyToManyField('Topic')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def tags(self):
    return set([tag.name for tag in self.tag_set.all()])

  def publication_name(self):
    return self.feed.publication.name

  def publication_bias(self):
    return self.feed.publication.bias

  def feed_category(self):
    return self.feed.category

  def short_description(self):
    if len(self.raw_description) > 30:
      return "%s..." % self.raw_description[0:30]
    else:
      return self.raw_description

  def friendly_publication_date(self):
    return self.publication_date.strftime("%Y-%m-%d %H:%M:%S")

  def __str__(self):
    return u'%s (%s - %s) %s (%s) %s' % (self.title, self.publication_name(), self.feed_category(), self.short_description(), self.url, self.friendly_publication_date())

  class Meta:
    ordering = ['-publication_date']

  def identify_topics(self):
    for topic in Topic.objects.all():
      for topic_word in topic.topicword_set.all():
        in_title = self.title.lower().find(topic_word.stem.lower()) != -1
        in_description = self.description and self.description.find(topic_word.stem) != -1
        if in_title or in_description:
          self.topics.add(topic)
          break

  def identify_associations(self):
    print("TITLE: %s" % self.title)
    for topic in self.topics.all():
      print("TOPIC: %s" % topic)
      for feed_item in topic.feeditem_set.all():
        if feed_item.id != self.id:
          a1 = Association.objects.get_or_create(base_feed_item=self, associated_feed_item=feed_item)[0]
          a2 = Association.objects.get_or_create(base_feed_item=self, associated_feed_item=feed_item)[0]
          a1.topics.add(topic)
          a2.topics.add(topic)

  def best_associations(self):
    return sorted((self.base_associations.all()), key=lambda association: len(association.topics.all()), reverse=True)

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

class Topic(models.Model): # last seen?
  base_tag_string = models.CharField(max_length=500)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    words = "; ".join([topic.stem for topic in self.topicword_set.all()])
    return u'%s (%s)' % (words, self.base_tag_string)

class TopicWord(models.Model):
  TYPES = (
    ('CD', 'numeral, cardinal'),
    ('FW', 'foreign word'),
    ('LOC', 'proper noun, location'),
    ('NAME', 'proper noun, person\'s name'),
    ('NOUN', 'common noun'),
    ('ORG', 'proper noun, organization\'s name'),
    ('VERB', 'verb'),
    ('XX', 'uncategorized')
  )
  stem = models.CharField(max_length=500, unique=True) # uniqueness OK here? What if stems work for other topic words?
  topic = models.ForeignKey('Topic')
  pos_type = models.CharField(max_length=5, choices=TYPES)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return u'%s (%s)' % (self.stem, self.pos_type)

class Association(models.Model):
  base_feed_item = models.ForeignKey('FeedItem', related_name='base_associations')
  associated_feed_item = models.ForeignKey('FeedItem', related_name='associated_associations')
  topics = models.ManyToManyField('Topic')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return u'%s = %s (%s)' % (self.base_feed_item.title, self.associated_feed_item.title, len(self.topics.all()))
