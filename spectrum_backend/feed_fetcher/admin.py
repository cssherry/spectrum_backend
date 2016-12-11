from django.contrib import admin
from .models import Publication, Feed, FeedItem, Tag
from spectrum_backend.feed_fetcher.models import Publication, FeedItem

from import_export import resources
from import_export.admin import ImportExportMixin

class FeedItemResource(resources.ModelResource):
  class Meta:
    model = FeedItem

class FeedItemAdmin(ImportExportMixin, admin.ModelAdmin):
  resource_class = FeedItemResource

class PublicationResource(resources.ModelResource):
  class Meta:
    model = Publication

class PublicationAdmin(ImportExportMixin, admin.ModelAdmin):
  resource_class = PublicationResource

class FeedResource(resources.ModelResource):
  class Meta:
    model = Feed

class FeedAdmin(ImportExportMixin, admin.ModelAdmin):
  resource_class = FeedResource

class TagResource(resources.ModelResource):
  class Meta:
    model = Tag

class TagAdmin(ImportExportMixin, admin.ModelAdmin):
  resource_class = TagResource

admin.site.register(Publication, PublicationAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(FeedItem, FeedItemAdmin)
admin.site.register(Tag, TagAdmin)

# Register your models here.
