from spectrum_backend.feed_fetcher.tasks import task_add_new_associations
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
  def handle(self, *args, **options):
    task_add_new_associations.delay()