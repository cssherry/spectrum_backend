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
  #timestamps?

  def __str__(self):
    return u'%s (%s)' % (self.name, self.bias)

  class Meta:
    ordering = ['name']

class Feed(models.Model):
  publication = models.ForeignKey(Publication)
  category = models.CharField(max_length=500)
  rss_url = models.CharField(max_length=500, unique=True)

  def __str__(self):
    return u'%s - %s (%s)' % (self.publication.name, self.category, self.rss_url)

  class Meta:
    ordering = ['category'] # any way to do this by publication name + category?

  def tags(self):
    feed_items = self.feeditem_set.all()
    tags = set()
    for feed_item in feed_items:
      for tag in feed_item.tag_set.all():
        tags.add(tag.name)

    return tags

class FeedItem(models.Model):
  feed = models.ForeignKey(Feed)
  title = models.CharField(max_length=500)
  author = models.CharField(max_length=500, null=True)
  description = models.TextField(null=True)
  publication_date = models.DateTimeField()
  url = models.CharField(max_length=500, unique=True)
  image_url = models.CharField(max_length=500, null=True)

  def __str__(self):
    return u'%s (%s - %s) %s (%s)' % (self.title, self.feed.publication.name, self.feed.category, self.description, self.url)

  class Meta:
    ordering = ['publication_date']

class Tag(models.Model):
  name = models.CharField(max_length=500)
  feed_item = models.ForeignKey(FeedItem)

  def __str__(self):
    return u'%s' % (self.name)

  class Meta:
    unique_together = ('name', 'feed_item')

  def publication_name(self):
    return self.feed_item.feed.publication.name

class Topic(models.Model): # last seen?
  base_tag_string = models.CharField(max_length=500)

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
  topic = models.ForeignKey(Topic)
  pos_type = models.CharField(max_length=5, choices=TYPES)

  def __str__(self):
    return u'%s (%s)' % (self.stem, self.pos_type)
