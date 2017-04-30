from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.tasks import task_seed_base_associations

# Initial seed for all associations
class Command(BaseCommand):
    def handle(self, *args, **options):
        task_seed_base_associations.delay()