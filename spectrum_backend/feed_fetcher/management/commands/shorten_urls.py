from django.core.management.base import BaseCommand, CommandError
from ._url_parser import URLParser

class Command(BaseCommand):
  def handle(self, *args, **options):
    URLParser().batch_shorten_urls()