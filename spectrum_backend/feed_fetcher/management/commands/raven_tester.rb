from django.core.management.base import BaseCommand, CommandError

# Adds new associations
class Command(BaseCommand):
  def handle(self, *args, **options):
    i_don_t_exist()