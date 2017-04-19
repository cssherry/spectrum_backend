from django.core.management.base import BaseCommand, CommandError
from raven.contrib.django.raven_compat.models import client

# Adds new associations
class Command(BaseCommand):
  def handle(self, *args, **options):
    i_don_t_exist()