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

class Topic(models.Model):
  base_tag_string = models.CharField(max_length=500)

class TopicWord(models.Model):
  stem = models.CharField(max_length=500, unique=True) # uniqueness OK here? What if stems work for other topic words?
  tag = models.ForeignKey(Topic)
  pos_tag = models.CharField(max_length=10)


