from django.core.management.base import BaseCommand, CommandError
from ._shorten_urls import URLShortener

class Command(BaseCommand):
  def handle(self, *args, **options):
    URLShortener().shorten()