from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^test_api$', views.test_api, name='test_api'),
    url(r'^publications$', views.all_publications, name='publications'),
    url(r'^recent$', views.return_recent_articles, name='recent'),
]
