import json, re
from django.http import HttpResponse
from django.core import serializers
from spectrum_backend.feed_fetcher.models import FeedItem, Publication
from urllib.parse import urlparse

# Test API
def test_api(request=None):
    first_articles = FeedItem.get_fields(FeedItem.objects.all()[:3])
    return HttpResponse(json.dumps(first_articles), content_type='application/json')

def get_associated_articles(request):
    request_url = clean_url(request.GET.get('url', None))
    current_article = FeedItem.objects.filter(redirected_url__icontains=request_url)

    # TODO - fix empty redirected_url and just use those
    if not current_article:
        current_article = FeedItem.objects.filter(url__icontains=request_url)

    # Return "False" if article doesn't exist
    if len(current_article) == 0:
        return HttpResponse(json.dumps(False), content_type='application/json')

    # Otherwise, return top associations
    top_associations = current_article.first().top_associations(count=3, check_bias=True)

    return HttpResponse(json.dumps(top_associations), content_type='application/json')

def clean_url(url_string):
    p = urlparse(url_string)

    # don't include subdomains, code similar to cleanUrl in spectrum_chrome_app
    return '.'.join(p.hostname.split('.')[-2:]) + p.path

def all_publications(request):
    publications = Publication.objects.all()
    publication_json = json.loads(serializers.serialize('json', publications))
    results = {
        'publications': publication_json,
        'media_bias': dict((k, v) for k, v in Publication.BIASES),
    }
    return HttpResponse(json.dumps(results), content_type='application/json')

# # return first 100 articles
# def return_recent_articles(request):
#   recent_articles = get_articles(FeedItem.objects.order_by('publication_date').all()[:30], True)
#   article_string = json.dumps(_recent_articles(request))
#   return HttpResponse(article_string, content_type='application/json')
