from django.shortcuts import render
import json, re
from django.http import HttpResponse
from django.core import serializers
from spectrum_backend.feed_fetcher.models import FeedItem, Publication

# Test API
def test_api(request=None):
  first_articles = get_articles(get_three())
  return HttpResponse(json.dumps(first_articles), content_type='application/json')

# Just a dummy function for now
def get_three(current_article_url=None):
  return FeedItem.objects.all()[:3][::-1]

def get_articles(article_objects, include_related=False):
  result = []
  articles_json = json.loads(serializers.serialize('json', article_objects))
  for i, article in enumerate(articles_json):
    article = article['fields']
    article['description'] = strip_img(article['description'])
    article_mod = article_objects[i]
    article['feed'] = {
      'category': article_mod.feed.category,
      'publication_name': article_mod.feed.publication.name,
      'publication_url': article_mod.feed.publication.base_url,
      'publication_bias': article_mod.feed.publication.bias
    }
    if include_related:
      article['related_articles'] = get_articles(get_three(article['url']))
    result.append(article)
  return result

def strip_img(text_string):
  p = re.compile(r'<img.*?/>')
  return p.sub('', text_string)

# List publication_bias
def all_publications(request):
  publications = Publication.objects.all()
  publication_json = serializers.serialize('json', publications)
  return HttpResponse(publication_json, content_type='application/json')

# return first 100 articles
def return_recent_articles(request):
  article_string = json.dumps(recent_articles(request))
  return HttpResponse(article_string, content_type='application/json')

def recent_articles(request):
  articles = get_articles(FeedItem.objects.all()[:100][::-1], True)
  return articles
