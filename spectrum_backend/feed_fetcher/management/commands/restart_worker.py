from django.core.management.base import BaseCommand, CommandError
import heroku3
import os

class Command(BaseCommand):
    def handle(self, *args, **options):
        heroku_conn = heroku3.from_key(os.environ['SPECTRUM_HEROKU_API_KEY'])
        app = heroku_conn.apps()['spectrum-backend']
        app.restart()