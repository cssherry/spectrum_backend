from django.conf import settings

def batch_query_set(query_set, batch_size=settings.ASSOCIATION_MEMORY_THRESHOLD):
    """
    Returns a (start, end, total, queryset) tuple for each batch in the given
    queryset.
    
    Usage:
        for start, end, total, qs in batch_query_set(feed_item_query_set):
            print "Now processing %s - %s of %s" % (start + 1, end, total)
            for article in qs:
                print article.body
    """
    total = query_set.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield (start, end, total, query_set[start:end])