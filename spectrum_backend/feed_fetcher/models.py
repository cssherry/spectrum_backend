from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.db.models import Count
from management.commands._batch_query_set import batch_query_set

class Publication(models.Model):
    BIASES = (
        ('L', 'Left-Wing'),
        ('LC', 'Left-Leaning'),
        ('C', 'Moderate'),
        ('RC', 'Right-Leaning'),
        ('R', 'Right-Wing'),
    )
    name = models.CharField(max_length=500, unique=True)
    base_url = models.CharField(max_length=500, unique=True)
    bias = models.CharField(max_length=2, choices=BIASES)
    html_content_tag = models.CharField(max_length=500, default="")
    logo_url = models.CharField(max_length=500, default="")
    skip_scraping = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'%s (%s)' % (self.name, self.bias)

    class Meta:
        ordering = ['name']

    def feeds(self, include_ignored=True):
        if include_ignored:
            return self.feed_set.all()
        else:
            return self.feed_set.filter(should_ignore=0)

    def feed_items(self, include_ignored=True, include_empty=True):
        return FeedItem.objects.filter(feed__publication=self)


class Feed(models.Model):
    publication = models.ForeignKey('Publication')
    category = models.CharField(max_length=500)
    rss_url = models.CharField(max_length=500, unique=True)
    should_ignore = models.BooleanField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'%s - %s (%s)' % (self.publication.name, self.category,
                                  self.rss_url)

    class Meta:
        ordering = ['publication__name']

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

class FeedItem(models.Model):
    MAX_SCRAPING_ATTEMPTS = 2

    feed = models.ForeignKey('Feed')
    title = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000, default="")
    description = models.TextField(default="")
    content = models.TextField(default="")
    raw_description = models.TextField(default="")
    raw_content = models.TextField(default="")
    publication_date = models.DateTimeField()
    redirected_url = models.CharField(max_length=1000, unique=True)
    url = models.CharField(max_length=1000, unique=True)
    lookup_url = models.CharField(max_length=1000, unique=True)
    image_url = models.CharField(max_length=1000, default="")
    self_score = models.FloatField(default=0)
    checked_for_associations = models.BooleanField(default=0)
    frequency_dictionary = JSONField(default={})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def recent_items_eligible_for_association(cls, days=7):
        time_threshold = timezone.now() - timedelta(days=days)
        return cls.objects.exclude(content__exact="").filter(created_at__gt=time_threshold)

    @classmethod
    def get_fields(cls, list):
        items = []
        for item in list:
            items.append(item.base_object())
        return items

    @classmethod
    def duplicate_items(cls, field_name):
        return cls.objects.values(field_name).annotate(count=Count('id')).values(field_name).order_by().filter(count__gt=1)

    @classmethod
    def delete_duplicate_redirect_urls(cls): # TODO: Remove after redirect urls are properly made unique
        for redirected_url in cls.objects.values_list('redirected_url', flat=True).distinct():
            cls.objects.filter(pk__in=cls.objects.filter(redirected_url=redirected_url).values_list('id', flat=True)[1:]).delete()

    @classmethod
    def delete_duplicate_lookup_urls(cls): # TODO: Remove after redirect urls are properly made unique
        for lookup_url in cls.objects.values_list('lookup_url', flat=True).distinct():
            cls.objects.filter(pk__in=cls.objects.filter(lookup_url=lookup_url).values_list('id', flat=True)[1:]).delete()

    @classmethod
    def feed_items_urls_to_scrape(cls, verbose=False, debug=False):
        if debug:
            publications = Publication.objects.all()[:3]
        else:
            publications = Publication.objects.all()

        urls = []
        total_items = 0
        for publication in publications:
            html_content_tag_present = publication.html_content_tag != ""
            if html_content_tag_present and not publication.skip_scraping:
                pub_count = 0
                for start, end, total, publication_feed_items in batch_query_set(publication.feed_items()):
                    for feed_item in publication_feed_items:
                        if feed_item.should_scrape():
                            urls.append(feed_item)
                            pub_count += 1
        
                if verbose:
                    print("Processing %s, %s items" % (publication.name, pub_count))
                total_items += pub_count

        if verbose:
            print("Processing %s total items" % (total_items))
        return urls

    def publication_name(self):
        return self.feed.publication.name

    def publication_bias(self):
        return self.feed.publication.bias

    def publication_logo(self):
        return self.feed.publication.logo_url

    def feed_category(self):
        return self.feed.category

    def short_description(self):
        if len(self.raw_description) > 30:
            return "%s..." % self.raw_description[0:30]
        else:
            return self.raw_description

    def friendly_publication_date(self):
        return self.publication_date.strftime("%Y-%m-%d %H:%M:%S")

    def under_max_scraping_cap(self):
        return self.scrapylogitem_set.count() < self.MAX_SCRAPING_ATTEMPTS

    def should_scrape(self, ignore_scraping_cap = False):
        return self.raw_content == "" and (ignore_scraping_cap or self.under_max_scraping_cap())

    def base_object(self, similarity_score=None):
        base_object = {
            "publication_name": self.publication_name(),
            "publication_bias": self.publication_bias(),
            "publication_logo": self.publication_logo(),
            "feed_category": self.feed_category(),
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "url": self.url,
            "author": self.author,
            "image_url": self.image_url,
            "publication_date": self.friendly_publication_date()
        }
        if similarity_score:
            base_object["similarity_score"] = similarity_score

        return base_object

    def opposing_biases(self):
        if self.publication_bias() == "L" or self.publication_bias() == "LC":
            return ["R", "RC", "C"]
        elif self.publication_bias() == "R" or self.publication_bias() == "RC":
            return ["L", "LC", "C"]
        else:
            return ["L", "LC", "C", "RC", "R"]


    def top_associations(self, count, check_bias=True, similarity_floor=2.0):
        associated_articles = []
        for association in self.base_associations.all():
            associated_feed_item = association.associated_feed_item
            if check_bias:
                if not associated_feed_item.publication_bias() in self.opposing_biases():
                    continue
            if association.similarity_score >= similarity_floor:
                associated_articles.append(
                    associated_feed_item.base_object(
                        association.similarity_score))

        unique_publication_articles = []
        unique_publication_names = []
        extra_articles = []

        for article in associated_articles:
            if not article["publication_name"] in unique_publication_names:
                unique_publication_articles.append(article)
                unique_publication_names.append(article["publication_name"])
            else:
                extra_articles.append(article)

        all_articles = unique_publication_articles + extra_articles
        return all_articles[:count]


    def pretty_print_associations(self):
        print("\t\t%s\t\t%s" % (self.publication_name(), self.title))
        print("\n***************\n")
        for association in self.base_associations.all():
            print("%s\t%s\t%s" % (association.similarity_score, association.associated_feed_item.publication_name(), association.associated_feed_item.title))

    def __str__(self):
        return u'%s (%s - %s) %s (%s) %s' % (
            self.title, self.publication_name(), self.feed_category(),
            self.short_description(), self.url,
            self.friendly_publication_date())

    class Meta:
        ordering = ['-publication_date']


class Tag(models.Model):
    name = models.TextField(default="")
    feed_item = models.ForeignKey('FeedItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'%s' % (self.name)

    class Meta:
        unique_together = ('name', 'feed_item')


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
        unique_together = ('base_feed_item', 'associated_feed_item')

class CorpusWordFrequency(models.Model):
    dictionary = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_corpus_dictionary(cls):
        return cls._corpus_dictionary().dictionary

    @classmethod
    def set_corpus_dictionary(cls, dictionary):
        corpus_dictionary = cls._corpus_dictionary()
        corpus_dictionary.dictionary = dictionary
        return corpus_dictionary.save()

    @classmethod
    def _corpus_dictionary(cls):
        return cls.objects.first() or cls.objects.create(dictionary={})

class ScrapyLogItem(models.Model):
    feed_item = models.ForeignKey('FeedItem')
    status_code = models.IntegerField()
    content_tag_found = models.BooleanField()
    other_error = models.TextField(default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

