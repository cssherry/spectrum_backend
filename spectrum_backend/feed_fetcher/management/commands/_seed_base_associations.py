from django.core.management.base import BaseCommand, CommandError
from spectrum_backend.feed_fetcher.models import FeedItem
from django.conf import settings
from .tfidf import main
import heroku3
import os

# Initial seed for all associations
class SeedBaseAssociations(BaseCommand):
    def seed(self):
        heroku_conn = heroku3.from_key(os.environ['SPECTRUM_HEROKU_API_KEY'])
        app = heroku_conn.apps()['spectrum-backend']
        app.process_formation()['worker'].resize('standard-2x') # We scale this process up to ensure sufficient memory
        feed_items = FeedItem.recent_items_eligible_for_association(settings.DAYS_TO_CHECK_FOR)
        main(feed_items)
        app.process_formation()['worker'].resize('standard-1x') # We scale back down to avoid extra costs