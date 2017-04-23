from django.core.management.base import BaseCommand, CommandError
from ._clean_entries import CleanEntries

class Command(BaseCommand):
  def handle(self, *args, **options):
    CleanEntries().clean()