#!/usr/bin/env python

"""
Trevor Owens, Feb 2017

Generate the TF-IDF ratings for a collection of documents.

This script will also tokenize the input files to extract words
    (removes punctuation and puts all in lower case), and it will use
    the NLTK library to lemmatize words (get rid of stemmings)

IMPORTANT:
    A REQUIRED library for this scripit is NLTK, please make sure\
 it's installed along with the wordnet corpus before trying to run this script

Usage:
   python tfidf.py input_files.txt
"""
import codecs
import json
import math
# import operator
import sys
import time
import unicodedata

import nltk
import numpy as np
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Association
from spectrum_backend.feed_fetcher.models import CorpusWordFrequency
from django.core.management.base import BaseCommand
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()


def remove_diacritic(tokens):
    for i in range(len(tokens)):
        w = unicode(tokens[i], 'ISO-8859-1')
        w = unicodedata.normalize('NFKD', w).encode('ASCII', 'ignore')
        tokens[i] = w.lower()
    return tokens

    
def tokenize_lemmatize_clean(doc_string):
    lowers = doc_string.lower()
    # no_punctuation = lowers.translate(None, string.punctuation)
    tokens = nltk.word_tokenize(lowers)
    stopwords = nltk.corpus.stopwords.words('english')
    tokens = [w for w in tokens if w not in stopwords]
    # lemmatize words. try both noun and verb lemmatizations
    lmtzr = nltk.stem.wordnet.WordNetLemmatizer()
    # need to see if this is being used right...
    for i in range(0, len(tokens)):
        res = lmtzr.lemmatize(tokens[i])
        if res == tokens[i]:
            tokens[i] = lmtzr.lemmatize(tokens[i], 'v')
        else:
            tokens[i] = res
    tokens = [t for t in tokens if len(t) > 1 and not t.isdigit()]
    return tokens


def read_json(filename):
    print('writing results to file {}'.format(filename))
    fileSystemEncoding = sys.getfilesystemencoding()
    #  INPUT_FILE = os.path.expanduser(u'./' + filename)
    with codecs.open(filename,
                     encoding=fileSystemEncoding,
                     mode="rU") as f:
        text = f.read()
        json_text = json.loads(text)
    return json_text


def calc_doc_frequency(text):
    """Take a document text and a FeedItem document
and populate a WordFrequencyDictionary for it"""
    doc_frequency = {}
    tokens = tokenize_lemmatize_clean(text)
    for word in tokens:
        if word in doc_frequency:
            doc_frequency[word] += 1
        else:
            doc_frequency[word] = 1
    return doc_frequency


def update_corpus_frequency(corpus_frequency, doc_frequency):
    """Given a new document, update the corpus frequency dictionary using
doc_frequency dictionary"""
    # n_common_words = len(set(list(corpus_frequency.keys())) & set(list(doc_frequency.keys())))
    # unique_words = len(doc_frequency) - n_common_words
    # print("number of unique words {}".format(unique_words))
    for term in doc_frequency.keys():
        if term in corpus_frequency:
            corpus_frequency[term] += 1
        else:
            corpus_frequency[term] = 1


def calc_tfidf(term, doc_frequency, corpus_frequency, n):
    """Calculate the term frequency inverse document frequency score for a term.
If the term is not in the doc_frequency dictionary, return 0"""
    if term in doc_frequency:
        tfidf = doc_frequency[term] * np.log(n / corpus_frequency[term])
    else:
        return 0
    return tfidf


def calc_tfidf_vec_length(doc_frequency, corpus_frequency, n):
    self_score = 0
    for term in doc_frequency:
        tfidf = calc_tfidf(term, doc_frequency, corpus_frequency, n)
        self_score += tfidf * tfidf
    return math.sqrt(self_score)


def update_similarity_dict(doc_dict, name_of_other_doc, cosine_similarity):
    key = "similarity"
    if key in doc_dict:
        doc_dict[key][name_of_other_doc] = cosine_similarity
    else:
        doc_dict[key] = {}
        doc_dict[key][name_of_other_doc] = cosine_similarity


def update_associations(doc_item_1, doc_item_2,
                        cosine_similarity, threshold=0.2):
    if cosine_similarity > threshold:
        try:
            Association.objects.update_or_create(
                base_feed_item=doc_item_1,
                associated_feed_item=doc_item_2,
                defaults={'similarity_score': cosine_similarity})
            Association.objects.update_or_create(
                base_feed_item=doc_item_2,
                associated_feed_item=doc_item_1,
                defaults={'similarity_score': cosine_similarity})
        except ValidationError:
            pass


def calc_cosine_similarity(
        frequency_1, frequency_2, self_score_1, self_score_2,
        corpus_frequency, n):
    df1 = frequency_1
    df2 = frequency_2
    tfidf_vec_length_1 = self_score_1
    tfidf_vec_length_2 = self_score_2
    if (tfidf_vec_length_1 == 0 or tfidf_vec_length_2 == 0):
        return -1
    
    common_words = set(list(df1.keys())) & set(list(df2.keys()))
    dot_product = 0
    for word in common_words:
        tfidfw1 = calc_tfidf(word, df1, corpus_frequency, n)
        tfidfw2 = calc_tfidf(word, df2, corpus_frequency, n)
        dot_product += tfidfw1 * tfidfw2
    
    cosine_similarity = dot_product / (
        tfidf_vec_length_1 * tfidf_vec_length_2)

    return cosine_similarity


def get_pub_name_title_mashup(doc_dic):
    """Creates a string from publication name and title"""
    pub_name = doc_dic["1. publication_name"]
    title = doc_dic["4. title"]
    mashup = pub_name + ": " + title
    return mashup


def single_list_self_comparison(doc_list,
                                corpus_frequency,
                                n, pretty_print=False,
                                storage_threshold=0.2):
    """For each document, compare to each other doucment, store comparison
in association class dictionary. Must run update_df_and_cf_with_new_docs
FIRST. N is number of total documents in corpus.

    """
    print("Comparing documents and storing comparison data")
    for i in range(len(doc_list)):
        doc_item_1_list = doc_list[i:i+1]
        doc_list_to_compare_to = doc_list[i:]  # throw out self comp with bias
        dissimilar_lists_comparison(doc_item_1_list,
                                    doc_list_to_compare_to,
                                    corpus_frequency,
                                    n,
                                    pretty_print,
                                    storage_threshold)
        if i % 100 == 0:
            print("%s items processed" % (i + 1)) 


def dissimilar_lists_comparison(doc_list_new, doc_list_old,
                                corpus_frequency, n,
                                pretty_print=False,
                                storage_threshold=0.2):

    for i in range(len(doc_list_new)):
        doc_item_1 = doc_list_new[i]
        bias_1 = doc_item_1.publication_bias()
        frequency_1 = doc_item_1.frequency_dictionary
        self_score_1 = doc_item_1.self_score
        for j in range(len(doc_list_old)):
            doc_item_2 = doc_list_old[j]
            bias_2 = doc_item_2.publication_bias()
            frequency_2 = doc_item_2.frequency_dictionary
            self_score_2 = doc_item_2.self_score
            if bias_2 != bias_1:
                if pretty_print:
                    print("\n\nIntersecting : ")
                    print(doc_item_1.title)
                    print(doc_item_2.title)
                    print("doc 1 number of terms: {}".format(
                        len(list(frequency_1.keys()))))
                    print("doc 2 number of terms: {}".format(
                        len(list(frequency_2.keys()))))
                cosine_similarity = calc_cosine_similarity(
                    frequency_1, frequency_2, self_score_1, self_score_2,
                    corpus_frequency, n)
                if pretty_print:
                    print("cosine_similary={0:.2f}".format(cosine_similarity))
                update_associations(doc_item_1, doc_item_2,
                                    cosine_similarity, storage_threshold)
            else:
                continue


def update_df_and_cf_with_new_docs(doc_list, corpus_frequency, n,
                                   exclude_no_article=True):
    """For each document, calc doc frequency, store it, and update corpus
frequency.  N is total number of docs in corpus, not just length of
doc_list.  Need to then update the similarity scores. If
exclude_no_article, then if there is no body text, exclude from
matching.

    """
    for i in range(len(doc_list)):
        doc_item = doc_list[i]
        title = doc_item.title
        summary = doc_item.description
        body = doc_item.content
        if not body and exclude_no_article:
            continue
        text = title + summary + body
        doc_frequency = calc_doc_frequency(text)
        doc_item.frequency_dictionary = doc_frequency
        doc_item.save()
        update_corpus_frequency(corpus_frequency, doc_frequency)
        if i % 1000 == 0:
            print("Corpus frequency length: %s" % len(corpus_frequency))
    
    CorpusWordFrequency.set_corpus_dictionary(corpus_frequency)
    # -> are we smashing words together?
    # print(CorpusWordFrequency.get_corpus_dictionary())
        
    # now that updated, for each document, add in tfidf self score
    print("Calculating self scores")
    for i in range(len(doc_list)):
        doc_item = doc_list[i]
        doc_frequency = doc_item.frequency_dictionary
        tfidf_vec_length = calc_tfidf_vec_length(doc_frequency,
                                                 corpus_frequency, n)
        doc_item.self_score = tfidf_vec_length
        doc_item.save()
        if i % 1000 == 0:
            print("%s document self scores processed" % (i + 1))

        
def get_top_associations(doc_item):
    title = doc_item.title
    bias = doc_item.publication_bias()
    list_of_associations = doc_item.base_associations.all()

    if len(list_of_associations) == 0:
        return
    print("\n\n{0} \n\tbias ={1} and associations:".format(title, bias))
    print("---------------------------------\
---------------------------------------")
    for association in list_of_associations:
        similar_doc_item = association.associated_feed_item
        similarity_score = association.similarity_score
        title_other = similar_doc_item.title
        bias_other = similar_doc_item.publication_bias()
        print("{0} : {1} : {2}".format(
            title_other, bias_other, similarity_score))


def test(threshold):
    print(FeedItem.objects.count())
    #  All feed_items with content field available
    doc_list = FeedItem.items_eligible_for_similarity_score()
    print(len(doc_list))
    # database check
    d1 = doc_list[0]
    print(d1.title)
    print(d1.publication_name())
    print(d1.publication_bias())
    print(d1.summary)
    print(d1.description)

    print("len original doc_list: {}".format(len(doc_list)))
    
    t = time.time()
    
    # now have a list of all documents
    corpus_frequency = {}  # CorpusWordFrequency.get_corpus_dictionary()
    
    #  chop for testing
    doc_list_old = doc_list[::40]
    print("len doc_list_old: {}".format(len(doc_list_old)))
    doc_list_new = doc_list[1::40]
    print("len doc_list_new: {}".format(len(doc_list_new)))
    
    n = len(doc_list_old)  # total number of docs in corpus, right now
    update_df_and_cf_with_new_docs(doc_list_old, corpus_frequency, n)

    # batch_calculate_similarities
    single_list_self_comparison(doc_list_old, corpus_frequency, n,
                                False, threshold)
    # find top similarities
    for i in range(n):
        doc_item = doc_list_old[i]
        get_top_associations(doc_item)

    elapsed_time = time.time() - t
    print("elapsed_time = {}".format(elapsed_time))

# -----------------------------------------------------------------
    # now for doc_list_new, create online algorithm
    # so first update df and cf
    corpus_frequency = CorpusWordFrequency.get_corpus_dictionary()
    n += len(doc_list_new)  # set n to total number of docs
    update_df_and_cf_with_new_docs(doc_list_new, corpus_frequency, n)
    # now do exhaustive_update for docs with themselves:
    single_list_self_comparison(doc_list_new, corpus_frequency, n)
    # now compare these docs with all other docs
    dissimilar_lists_comparison(doc_list_new, doc_list_old,
                                corpus_frequency, n)
    # find top similarities
    print("len doc_list_old = {}".format(len(doc_list_old)))
    print("len doc_list_new = {}".format(len(doc_list_new)))
    doc_list_old.extend(doc_list_new)
    print("after extension len doc_list_old = {}".format(len(doc_list_old)))
    for i in range(n):
        doc_item = doc_list_old[i]
        get_top_associations(doc_item)

    elapsed_time = time.time() - t
    print("total elapsed_time = {}".format(elapsed_time))
    return
    
        
def main(old_list=[], new_list=[]):
    """Given a single list, will populate associations for that list
relative only to itself. Otherwise, given a new list, assumes old list
has already been populated and will build associations for the new
list relative to each other and then to the old list.

I estimate the time will grow polynomially. Usine least squares and
converting the data to log-log space, we can find that the time in
seconds grows roughly like:

t = 0.00468 * n ^ 1.398

So on other hardware, the exponential should remain about the same.
So for 16k documents, this means 1 hour of computation time.

    """
    threshold = 0.2  # threshold for storage of matches
    print("test")
    print(len(old_list))
    if not new_list and old_list:
        print("Running initial job to build associations")
        corpus_frequency = {}
        n = len(old_list)  # total number of docs in corpus, right now
        update_df_and_cf_with_new_docs(
            old_list, corpus_frequency, n)
        # batch_calculate_similarities
        single_list_self_comparison(old_list,
                                    corpus_frequency, n,
                                    False, threshold)
    elif old_list and new_list:
        print("both lists are populated. Running update")
        corpus_frequency = CorpusWordFrequency.get_corpus_dictionary()
        n = len(old_list) + len(new_list)  # set n to total number of docs
        update_df_and_cf_with_new_docs(new_list, corpus_frequency, n)
        # now do exhaustive_update for docs with themselves:
        single_list_self_comparison(new_list, corpus_frequency, n)
        # now compare these docs with all other docs
        dissimilar_lists_comparison(new_list,
                                    old_list,
                                    corpus_frequency, n)

    else:
        print("the first list must be populated with documents whose\
 associations have already been determined")
        print("running test")
        # Association.objects.all().delete()
        # test(threshold)
    return


if __name__ == "__main__":
    main()

"""
Mapping of JSON fields to db fields (can be called directly on feed_item)
base_object = {
    "publication_name": item.publication_name(),
    "publication_bias": item.publication_bias(),
    "feed_category": item.feed_category(),
    "title": item.title,
    "summary": item.summary,
    "description": item.description,
    "content": item.content,
    "url": item.url,
}
rest_of_object = {
    "author": item.author,
    "image_url": item.image_url,
    "publication_date": item.friendly_publication_date(),
    "tags": list(item.tags()),
}
"""
