import json, re
from django.http import JsonResponse
from django.core import serializers
from spectrum_backend.feed_fetcher.models import FeedItem, Publication, URLLookUpRecord, UserFeedback, Association, UserClick
from spectrum_backend.feed_fetcher.management.commands._url_parser import URLParser
from raven.contrib.django.raven_compat.models import client

def get_associated_articles(request):
    url = _clean_url(request.GET.get('url', None))

    if _is_not_base_url(url):
        lookup_url = _shorten_url(url)

        current_article = None

        try:
            current_article = FeedItem.objects.get(lookup_url=lookup_url)
            lookup_code = "1"
        except FeedItem.DoesNotExist:
            pass

        if not current_article:
            try:
                current_article = FeedItem.objects.filter(redirected_url__icontains=url)[0]
                lookup_code = "2"
            except IndexError:
                pass

        if not current_article:
            try:
                current_article = FeedItem.objects.filter(url__icontains=url)[0]
                lookup_code = "3"
            except IndexError:
                pass

        if current_article:
            top_associations = current_article.top_associations(count=12, check_bias=True)
            URLLookUpRecord.objects.create(code=lookup_code, url=url, feed_item=current_article, associations_found=len(top_associations))
            return JsonResponse(top_associations, safe=False)
        else:
            URLLookUpRecord.objects.create(code="N/A", url=url)
            return JsonResponse({"message": "URL not found"}, status=404, safe=False)
    else:
        URLLookUpRecord.objects.create(code="Base", url=url)
        return JsonResponse({"message": "Base URL, Spectrum modal skipped"}, status=422, safe=False)

def all_publications(request):
    publications = Publication.objects.all()
    publication_json = json.loads(serializers.serialize('json', publications))
    results = {
        'publications': publication_json,
        'media_bias': Publication.bias_dict(),
    }
    return JsonResponse(results, safe=False)

def track_click(request):
    association_id = request.POST.get('association_id', None)

    try:
        association = Association.objects.filter(pk=association_id)[0]
        UserClick.objects.create(association=association)
        return JsonResponse({"message": "success"}, status=200, safe=False)
    except IndexError:
        client.captureException()
        return JsonResponse({"message": "association not found"}, status=404, safe=False)

def track_feedback(request):
    association_id = request.POST.get('association_id', None) # Integer
    is_negative = request.POST.get('is_negative', None) # Boolean - will parse correctly?
    feedback_version = request.POST.get('feedback_version', None) # Integer
    feedback_dict = request.POST.get('feedback_dict', None) # Dictionary - pop right into feedback_dict?
    is_internal_user = request.POST.get('is_internal_user', False)

    if association_id and feedback_version and feedback_dict and is_negative is not None:
        try:
            association = Association.objects.filter(pk=association_id)[0]
            UserFeedback.objects.create(association=association, is_negative=is_negative, feedback_version=feedback_version, feedback_dict=feedback_dict)
            return JsonResponse({"message": "success"}, status=200, safe=False)
        except IndexError:
            client.captureException()
            return JsonResponse({"message": "association not found"}, status=404, safe=False)
    else:
        return JsonResponse({"message": "invalid request"}, status=422, safe=False)

def test_api(request=None):
    recent_articles = []
    for feed_item in FeedItem.objects.all()[:3]:
        recent_articles.append(feed_item.base_object())

    return JsonResponse(recent_articles, safe=False)

def _clean_url(url_string):
    return URLParser().clean_url(url_string)

def _shorten_url(url_string):
    return URLParser().shorten_url(url_string)

def _is_not_base_url(url_string):
    return not URLParser().is_base_url(url_string)
