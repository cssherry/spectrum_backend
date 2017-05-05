import json, re
from django.http import HttpResponse
from django.core import serializers
from spectrum_backend.feed_fetcher.models import FeedItem, Publication
from spectrum_backend.feed_fetcher.management.commands._url_parser import URLParser

def get_associated_articles(request):
    url = _clean_url(request.GET.get('url', None))
    if _is_not_base_url(url):
        lookup_url = _shorten_url(url)

        current_article = None

        try:
            current_article = FeedItem.objects.get(lookup_url=lookup_url)
        except FeedItem.DoesNotExist:
            pass

        if not current_article:
            try:
                current_article = FeedItem.objects.filter(redirected_url__icontains=url)[0]
            except IndexError:
                pass

        if not current_article:
            try:
                current_article = FeedItem.objects.filter(url__icontains=url)[0]
            except IndexError:
                pass

        if current_article:
            top_associations = current_article.top_associations(count=12, check_bias=True)

            return HttpResponse(json.dumps(top_associations), content_type='application/json') # TODO: JsonResponse({'foo':'bar'})
        else:
            return HttpResponse(json.dumps({"message": "URL not found"}), content_type='application/json')
    else:
        return HttpResponse(json.dumps({"message": "Base URL, Spectrum modal skipped"}), content_type='application/json')

def all_publications(request):
    publications = Publication.objects.all()
    publication_json = json.loads(serializers.serialize('json', publications))
    results = {
        'publications': publication_json,
        'media_bias': dict((k, v) for k, v in Publication.BIASES),
    }
    return HttpResponse(json.dumps(results), content_type='application/json')

def test_api(request=None):
    recent_articles = []
    for feed_item in FeedItem.objects.all()[:3]:
        recent_articles.append(feed_item.base_object())

    return HttpResponse(json.dumps(recent_articles), content_type='application/json')

def _clean_url(url_string):
    return URLParser().clean_url(url_string)

def _shorten_url(url_string):
    return URLParser().shorten_url(url_string)

def _is_not_base_url(url_string):
    return not URLParser().is_base_url(url_string)

# # return first 100 articles
# def return_recent_articles(request):
#   recent_articles = get_articles(FeedItem.objects.order_by('publication_date').all()[:30], True)
#   article_string = json.dumps(_recent_articles(request))
#   return HttpResponse(article_string, content_type='application/json')
