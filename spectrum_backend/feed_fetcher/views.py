from django.shortcuts import render
import json, re
from django.http import HttpResponse
from django.core import serializers
from spectrum_backend.feed_fetcher.models import FeedItem, Publication
from urllib.parse import urlparse

# Test API
def test_api(request=None):
  first_articles = get_articles(get_associated_articles())
  return HttpResponse(json.dumps(first_articles), content_type='application/json')

# Get Related Articles
def get_related(request):
  if request.method == "POST":
    data = request.POST
  elif request.method == "GET":
    data = request.GET
  else:
    return HttpResponse("GET or POST only", status=500)

  first_articles = get_articles(get_associated_articles(title=data.get('title', None), url=data.get('url', None)))
  return HttpResponse(json.dumps(first_articles), content_type='application/json')

# Just a dummy function for now
def get_associated_articles(url=None, title=None):
  current_article = None

  if url:
    current_article = FeedItem.objects.filter(url__icontains=clean_url(url))

  if title and ((current_article and current_article.exists()) or not url):
    current_article = FeedItem.objects.filter(title=title)

  if not current_article:
    current_article = FeedItem.objects.first()
  else:
    current_article = current_article[0]

  associations = current_article.best_associations()[:3]
  result = []
  for ass in associations:
    result.append(ass.associated_feed_item)
  return result

def clean_url(url_string):
    p = urlparse(url_string)
    return p.hostname + p.path

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
      article['related_articles'] = get_articles(get_associated_articles(url=article['url'], title=article['title']))
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
  articles = get_articles(FeedItem.objects.order_by('-publication_date').all()[:24], True)
  return articles
