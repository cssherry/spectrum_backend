import re
import dateutil.parser
from django.utils import timezone
from raven.contrib.django.raven_compat.models import client

class RSSEntryWrapper:
    def __init__(self, feed, entry):
        self.entry = entry
        self.feed = feed
        self.title = self._parsed_title()
        self.url = self._parsed_url()
        self.raw_description = self._parsed_description()
        self.author = self._parsed_author()
        self.image_url = self._parsed_image_url()
        self.publication_date = self._parsed_publication_date()
        self.tags = self._parsed_tags()

    def _matches_element_format(self, element_name):
        return hasattr(self.entry, element_name)

    def _parsed_title(self):
        if self._matches_element_format('title'):
            return self.entry.title
        else:
            return ""

    def _parsed_description(self):
        if self._matches_element_format('description'):
            return self.entry.description
        elif self._matches_element_format('summary'):
            return self.entry.summary
        else:
            return ""

    def _parsed_author(self):
        if self._matches_element_format('author'):
            return self.entry.author
        else:
            return ""

    def _parsed_url(self):
        if self._matches_element_format('link'):
            return self.entry.link
        else:
            return ""

    def _parsed_image_url(self):
        if self._matches_element_format('media_content') and self.entry.media_content[0]:
            try:
                return self.entry.media_content[0]["url"]
            except KeyError:
                pass # Not a common error
        else:
            return ""

    def _parsed_publication_date(self):
        try:
            if self._matches_element_format('published'):
                return dateutil.parser.parse(self.entry.published) # TODO: May be causing timezone-naive errors
            else:
                return timezone.now() # TODO: find a better solution to this - maybe URL matching for date? Washington Post is culprit. Media Matters also has date problems
        except ValueError:
            pass # TODO - fix this. Error seen on Sentry

    def _parsed_tags(self):
        tags = []
        if self._matches_element_format('tags'):
            for tag in self.entry.tags:
                tags.append(tag.term)

        return tags
