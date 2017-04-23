import factory
import random
from . import models
from django.utils import timezone

class GenericPublicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Publication

    name = factory.Sequence(lambda n: 'News From The Planet %s' % n)
    base_url = factory.Sequence(lambda n: 'planet%snews.com' % n)
    bias = u'C'
    html_content_tag = u'.article-body'
    logo_url = u'planetnews.com/logo.png'
    skip_scraping = 0
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

class ModerateProfileFactory(GenericPublicationFactory):
    bias = u'C'

class RightWingProfileFactory(GenericPublicationFactory):
    bias = u'R'

class LeftWingProfileFactory(GenericPublicationFactory):
    bias = u'L'

class GenericFeedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Feed

    publication = factory.SubFactory(GenericPublicationFactory)
    category = u'News'
    rss_url = factory.Sequence(lambda n: 'planet%snews.com/rss' % n)
    should_ignore = 0
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

class GenericFeedItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FeedItem

    feed = factory.SubFactory(GenericFeedFactory)
    title = u'5 Secrets To Managing Your Assets In An Offshore Bank'
    author = u'John Jangle Jingleheimer Schmidt'
    description = u'The IRS Hates Him!'
    content = u'<p>Hi Mom</p>'
    raw_description = u'The IRS Hates Him!'
    raw_content = u'<p>Hi Mom</p>'
    publication_date = factory.LazyFunction(timezone.now)
    url = factory.Sequence(lambda n: 'https://rss.planetnews.com/article%s' % n)
    redirected_url = factory.Sequence(lambda n: 'https://www.planetnews.com/article%s' % n)
    lookup_url = factory.Sequence(lambda n: 'planetnews.com/article%s' % n)
    image_url = factory.Sequence(lambda n: 'planetnews.com/article-image%s.png' % n)
    self_score = 0
    checked_for_associations = 0
    frequency_dictionary = {}
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

class FeedItemWithRawLookupUrlsFactory(GenericFeedItemFactory):
    lookup_url = factory.Sequence(lambda n: 'https://www.planetnews.com/article%s' % n)

class GenericAssociationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Association

    base_feed_item = factory.SubFactory(GenericFeedItemFactory)
    associated_feed_item = factory.SubFactory(GenericFeedItemFactory)
    similarity_score = factory.Sequence(lambda n: '%s' % n)
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

class CorpusWordFrequencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.CorpusWordFrequency

    dictionary = {}
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

class GenericScrapyLogItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ScrapyLogItem

    feed_item = factory.SubFactory(GenericFeedItemFactory)
    status_code = 200
    content_tag_found = True
    other_error = ""
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
