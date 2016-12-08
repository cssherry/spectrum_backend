from django.contrib import admin
from .models import Publication, Feed, FeedItem, Tag

admin.site.register(Publication)
admin.site.register(Feed)
admin.site.register(FeedItem)
admin.site.register(Tag)

# Register your models here.
