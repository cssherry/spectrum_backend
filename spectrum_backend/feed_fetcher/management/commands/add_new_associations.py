from django.core.management.base import BaseCommand, CommandError
from ._add_new_associations import add

# Adds new associations
class Command(BaseCommand):
  def handle(self, *args, **options):
    add()