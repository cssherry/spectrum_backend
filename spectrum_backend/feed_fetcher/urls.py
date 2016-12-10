from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^test_api$', views.test_api, name='test_api'),
]
