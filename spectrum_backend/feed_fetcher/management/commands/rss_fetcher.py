from django.core.management.base import BaseCommand, CommandError
from ._rss_fetcher import RSSFetcher

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            debug = options["debug"]
        except KeyError:
            debug = False
        RSSFetcher(stdout=self.stdout, style=self.style, debug=debug).fetch()