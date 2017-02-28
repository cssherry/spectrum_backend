import sys
import os
import django

# sys.path.append('../spectrum_backend')
# os.environ['DJANGO_SETTINGS_MODULE'] = 'spectrum_backend.settings'
# from spectrum_backend.feed_fetcher.models import FeedItem
# django.setup()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SPECTRUM_DIR = os.path.dirname(BASE_DIR)
sys.path.append(SPECTRUM_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'spectrum_backend.settings'

django.setup()