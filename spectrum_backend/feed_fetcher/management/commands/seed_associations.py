"""
This module takes an initial list of feed items and does an
exhaustive comparison within this list to itself only and populates
the database with the results

"""
import time
import tfidf
from spectrum_backend.feed_fetcher.models import Association
from spectrum_backend.feed_fetcher.models import FeedItem
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()


def main():
    Association.objects.all().delete()
    t = time.time()
    threshold = 0.4  # threshold for storage of matches
    doc_list = FeedItem.items_eligible_for_similarity_score()
    corpus_frequency = {}
    doc_list_old = doc_list[::40]
    print("len doc_list_old: {}".format(len(doc_list_old)))
    n = len(doc_list_old)  # total number of docs in corpus, right now
    tfidf.update_df_and_cf_with_new_docs(doc_list_old, corpus_frequency, n)
    # batch_calculate_similarities
    tfidf.single_list_self_comparison(doc_list_old, corpus_frequency, n,
                                      False, threshold)
    for doc_item in doc_list_old:
        tfidf.get_top_associations(doc_item)
        elapsed_time = time.time() - t
        print("elapsed_time = {}".format(elapsed_time))
    return


if __name__ == "__main__":
    main()
