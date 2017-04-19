from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem

class Command(BaseCommand):
  def handle(self, *args, **options):
    FeedItem.delete_duplicate_redirect_urls()