from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^test_api$', views.test_api, name='test_api'),
    url(r'^publications$', views.all_publications, name='publications'),
    # url(r'^recent$', views.return_recent_articles, name='recent'),
    url(r'^associations$', views.get_associated_articles, name='associations'),
    url(r'^click$', views.track_click, name='click'),
    url(r'^feedback$', views.track_feedback, name='feedback'),
]
