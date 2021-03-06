from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.db.models import Count
from .management.commands._batch_query_set import batch_query_set
from django.contrib.auth.models import User

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

    @classmethod
    def bias_dict(cls):
        return dict((k, v) for k, v in Publication.BIASES)

    def __str__(self):
        return u'%s (%s)' % (self.name, self.bias)

    @classmethod
    def pub_stats(cls):
        string = "<body>"
        for publication in Publication.objects.all():
            entry = "<p>%s (%s) - %s items</p>" % (publication.name, publication.base_url, publication.feed_items().count())
            string += entry

        string += "</body>"
        return string

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
    def see_associations_by_url(cls, url):
        feed_item = FeedItem.objects.filter(redirected_url__icontains=url)
        if not feed_item:
            feed_item = FeedItem.objects.filter(url__icontains=url)

        if feed_item:
            if len(feed_item) > 1:
                print("More than one URL found")
            else:
                feed_item.first().pretty_print_associations()
        else:
            print("URL not found")

    @classmethod
    def recent_items(cls, hours):
        time_threshold = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(created_at__gt=time_threshold)
        
    @classmethod
    def pluck(cls, field_name):
        ids = FeedItem.objects.values_list(field_name, flat=True)
        my_models = FeedItem.objects.filter(pk__in=set(ids))

    @classmethod
    def recent_items_eligible_for_association(cls, days=7):
        return cls.recent_items(days * 24).exclude(content__exact="")

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
        if self.publication_date:
            return self.publication_date.strftime("%Y-%m-%d %H:%M:%S")

    def under_max_scraping_cap(self):
        return self.scrapylogitem_set.count() < self.MAX_SCRAPING_ATTEMPTS

    def should_scrape(self, ignore_scraping_cap = False):
        return self.raw_content == "" and (ignore_scraping_cap or self.under_max_scraping_cap())

    def base_object(self, similarity_score=None, association_id=None):
        base_object = {
            "id": self.id,
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

        if association_id:
            base_object["association_id"] = association_id

        return base_object

    def opposing_biases(self):
        if self.publication_bias() == "L" or self.publication_bias() == "LC":
            return ["R", "RC", "C"]
        elif self.publication_bias() == "R" or self.publication_bias() == "RC":
            return ["L", "LC", "C"]
        else:
            return ["L", "LC", "C", "RC", "R"]

    def all_associated_feed_items(self):
        ids = self.base_associations.values_list('associated_feed_item', flat=True)
        return FeedItem.objects.filter(pk__in=set(ids))

    def top_associations(self, count, check_bias=True, similarity_floor=0.2, similarity_ceiling=0.9):
        associated_articles = []
        for association in self.base_associations.all():
            associated_feed_item = association.associated_feed_item
            if check_bias:
                if not associated_feed_item.publication_bias() in self.opposing_biases():
                    continue
            if association.similarity_score >= similarity_floor and association.similarity_score <= similarity_ceiling:
                associated_articles.append(
                    associated_feed_item.base_object(
                        similarity_score=association.similarity_score, association_id=association.id))

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

class URLLookUpRecord(models.Model):
    CODES = (
        ('1', 'Found with lookup URL'),
        ('2', 'Found with redirect URL'),
        ('3', 'Found with normal URL'),
        ('N/A', 'Not found'),
        ('Base', 'Base URL'),
    )
    url = models.CharField(max_length=1000)
    code = models.CharField(max_length=10, choices=CODES)
    feed_item = models.ForeignKey('FeedItem', null=True)
    associations_found = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    spectrum_user = models.ForeignKey('SpectrumUser', null=True, blank=True)

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

    @classmethod
    def recent_items(cls, hours):
        time_threshold = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(created_at__gt=time_threshold)

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

    @classmethod
    def recent_items(cls, hours):
        time_threshold = timezone.now() - timedelta(hours=hours)
        return cls.objects.filter(created_at__gt=time_threshold)


# Click and feedback recording models
"""
Unique id linked to user
"""
class SpectrumUser(models.Model):
    user = models.ForeignKey(User)
    unique_id = models.TextField(default="", unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    """
    Creates new spectrum user instance or None if no username or is_internal_use
    """
    @classmethod
    def _try_create(cls, **kwargs):
        unique_id = kwargs.get('unique_id', None)
        username = kwargs.get('username', None)
        is_internal_user = kwargs.get('is_internal_user', None)

        if unique_id and username != None:
            user = User.objects.filter(username=username)

            if user.exists():
                user = user.first()
                is_new = False
            else:
                user = User.objects.create(username=username)
                is_new = True

            # Assume previous is_internal_use
            if is_internal_user is None:
                previous_spectrum_user = user.spectrumuser_set.last()
                if previous_spectrum_user:
                    is_internal_user = previous_spectrum_user.is_internal_use
                else:
                    return {
                        'message': 'No is_internal_user for new user'
                    }

            spectrum_user = cls.objects.create(unique_id=unique_id,
                                               user=user)

            return {
                'spectrum_user': spectrum_user,
                'is_internal_user': is_internal_user,
                'is_new': is_new
            }
        else:
            return {
                'message': 'No username and unique_id'
            }

    """
    Returns spectrum user instance or None if no unique_id
    expects unique_id, username, is_internal_user
    """
    @classmethod
    def get_spectrum_user(cls, **kwargs):
        unique_id = kwargs.get('unique_id', None)
        username = kwargs.get('username', None)
        is_internal_user = kwargs.get('is_internal_user', None) == 'true'

        if unique_id:
            spectrum_users = SpectrumUser.objects.filter(unique_id=unique_id)

            if spectrum_users.exists():
                return {
                    'spectrum_user': spectrum_users.last(),
                    'is_new': False,
                    'is_internal_user': is_internal_user
                }
            else:
                return cls._try_create(unique_id=unique_id,
                                       username=username,
                                       is_internal_user=is_internal_user)

        else:
            return {
                'message': 'No unique_id specified'
            }

class UserFeedback(models.Model):
    # Can be either be on associated article or publication (feed_item)
    association = models.ForeignKey('Association', null=True, blank=True)
    feed_item = models.ForeignKey('FeedItem', null=True, blank=True)

    # Only allow null/blank because of old created before SpectrumUser
    spectrum_user = models.ForeignKey('SpectrumUser', null=True, blank=True)

    is_negative = models.BooleanField()
    feedback_version = models.FloatField(default=0.2)
    feedback_dict = JSONField(default={})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserClick(models.Model):
    association = models.ForeignKey('Association', null=True, blank=True)
    element_selector = models.CharField(max_length=1000, null=True, blank=True)

    # Only allow null/blank because of old created before SpectrumUser
    spectrum_user = models.ForeignKey('SpectrumUser', null=True, blank=True)

    clicked_version = models.FloatField(default=0.2)
    clicked_item_dict = JSONField(default={})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)