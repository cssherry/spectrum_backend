from django.shortcuts import render
from spectrum_backend.feed_fetcher.views import recent_articles

def homepage(request):
  context = {
    'entries': recent_articles(request),
    'page_template': 'home/article_template.html',
  }
  return render(request, 'home.html', context)
