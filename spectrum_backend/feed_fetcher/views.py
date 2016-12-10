from django.shortcuts import render
import json
from django.http import HttpResponse
from django.core import serializers
from spectrum_backend.feed_fetcher.models import FeedItem

# Test API
def test_api(request):
  first_articles = get_articles(FeedItem.objects.all()[:3][::-1])
  return HttpResponse(json.dumps(first_articles), content_type='application/json')

def get_articles(article_objects):
  result = []
  articles_json = json.loads(serializers.serialize('json', article_objects))
  for i, article in enumerate(articles_json):
    article = article['fields']
    article_mod = article_objects[i]
    article['feed'] = {
      'category': article_mod.feed.category,
      'publication_name': article_mod.feed.publication.name,
      'publication_url': article_mod.feed.publication.base_url,
      'publication_bias': article_mod.feed.publication.bias
    }
    result.append(article)
  return result