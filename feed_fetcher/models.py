from django.db import models

class Publication(models.Model):
  BIASES = (
    ('L', 'Left'),
    ('LC', 'Left-Center'),
    ('C', 'Center'),
    ('RC', 'Right-Center'),
    ('R', 'Right'),
  )
  name = models.CharField(max_length=100)
  base_url = models.CharField(max_length=100)
  bias = models.CharField(max_length=2, choices=BIASES)
  #timestamps?

  def __str__(self):
    return u'%s (%s)' % (self.name, self.bias)

  class Meta:
    ordering = ['name']

class Feed(models.Model):
  publication = models.ForeignKey(Publication)
  category = models.CharField(max_length=50)
  rss_url = models.CharField(max_length=200)

  def __str__(self):
    return u'%s - %s (%s)' % (self.publication.name, self.category, self.rss_url)

  class Meta:
    ordering = ['category'] # any way to do this by publication name + category?

class FeedItem(models.Model):
  feed = models.ForeignKey(Feed)
  title = models.CharField(max_length=200)
  author = models.CharField(max_length=50)
  description = models.CharField(max_length=500)
  publication_date = models.DateField()
  url = models.CharField(max_length=300)

  def __str__(self):
    return u'%s (%s - %s) %s (%s)' % (self.title, self.feed.publication.name, self.feed.category, self.description, self.url)

  class Meta:
    ordering = ['publication_date']

