#!/usr/bin/env python

"""
Trevor Owens, Feb 2017

Generate the TF-IDF ratings for a collection of documents.

This script will also tokenize the input files to extract words
    (removes punctuation and puts all in lower case), and it will use
    the NLTK library to lemmatize words (get rid of stemmings)

IMPORTANT:
    A REQUIRED library for this script is NLTK, please make sure\
 it's installed along with the wordnet corpus before trying to run this script

Usage:
   python tfidf.py input_files.txt
"""
import codecs
import json
import math
import operator
import sys
import time
import unicodedata

import nltk
import numpy as np
from spectrum_backend.feed_fetcher.models import FeedItem
from spectrum_backend.feed_fetcher.models import Association

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
    # tokens = [token.lower() for token in tokens]
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
    """Take a document text and return a doc_frequency dictionary. If the
text string is empty, return an empty doc_frequency dictionary"""
    doc_frequency = {}
    if not text:
        return doc_frequency
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
    unique_terms = set(doc_frequency.keys())
    for term in unique_terms:
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


def calc_cosine_similarity(doc_dict_1, doc_dict_2, corpus_frequency, n,
                           prettyprint=False):
    df1 = doc_dict_1["doc_frequency"]
    df2 = doc_dict_2["doc_frequency"]

    common_words = set(list(df1.keys())) & set(list(df2.keys()))
    dot_product = 0
    for word in common_words:
        tfidfw1 = calc_tfidf(word, df1, corpus_frequency, n)
        tfidfw2 = calc_tfidf(word, df2, corpus_frequency, n)
        dot_product += tfidfw1 * tfidfw2

    tfidf_vec_length_1 = doc_dict_1["tfidf_vec_length"]
    tfidf_vec_length_2 = doc_dict_2["tfidf_vec_length"]

    if (tfidf_vec_length_1 > 0 and tfidf_vec_length_2 > 0):
        cosine_similarity = dot_product / (
            tfidf_vec_length_1 * tfidf_vec_length_2)
    else:
        cosine_similarity = -1

    mashup_1 = get_pub_name_title_mashup(doc_dict_1)
    mashup_2 = get_pub_name_title_mashup(doc_dict_2)
    update_similarity_dict(doc_dict_1, mashup_2, cosine_similarity)
    update_similarity_dict(doc_dict_2, mashup_1, cosine_similarity)
    
    if prettyprint:
        print("\n\nIntersecting : ")
        print(doc_dict_1["4. title"])
        print(doc_dict_2["4. title"])
        print("doc 1 number of terms: {}".format(len(list(df1.keys()))))
        print("doc 2 number of terms: {}".format(len(list(df2.keys()))))
        print("number of common words = {}".format(len(common_words)))
        # print(common_words)
        print("dot product = {0:.2f}".format(dot_product))
        print("tfidf_vec_length_1 = {0:.2f}".format(tfidf_vec_length_1))
        print("tfidf_vec_length_2 = {0:.2f}".format(tfidf_vec_length_2))
        print("cosine_similary = {0:.2f}".format(cosine_similarity))

    return cosine_similarity


def get_pub_name_title_mashup(doc_dic):
    """Creates a string from publication name and title"""
    pub_name = doc_dic["1. publication_name"]
    title = doc_dic["4. title"]
    mashup = pub_name + ": " + title
    return mashup


def exhaustive_similarities_calculation(doc_list, corpus_frequency, n):
    """For each document, compare to each other doucment, store comparison
in 'similarity' dictionarty. Must run update_df_and_cf_with_new_docs
FIRST. N is number of total documents in corpus.

    """
    for i in range(len(doc_list)):
        doc_dict_1 = doc_list[i]
        bias_1 = doc_dict_1["2. publication_bias"]
        for j in range(i, len(doc_list)):  # throws out self comp w/ bias check
            doc_dict_2 = doc_list[j]
            bias_2 = doc_dict_2["2. publication_bias"]
            if bias_2 != bias_1:
                calc_cosine_similarity(doc_dict_1, doc_dict_2,
                                       corpus_frequency, n)
            else:
                continue


def disjoint_sets_similarities_calculation(doc_list_new, doc_list_old,
                                           corpus_frequency, n):
    for i in range(len(doc_list_new)):
        doc_dict_1 = doc_list_new[i]
        bias_1 = doc_dict_1["2. publication_bias"]
        for j in range(len(doc_list_old)):
            doc_dict_2 = doc_list_old[j]
            bias_2 = doc_dict_2["2. publication_bias"]
            if bias_2 != bias_1:
                calc_cosine_similarity(doc_dict_1, doc_dict_2,
                                       corpus_frequency, n)
            else:
                continue


def update_df_and_cf_with_new_docs(doc_list, corpus_frequency, n):
    """For each document, calc doc frequency, store it, and update corpus
frequency.  N is total number of docs in corpus, not just length of
doc_list.  Need to then update the similarity scores

    """
    for i in range(len(doc_list)):
        doc_dic = doc_list[i]
        title = doc_dic["4. title"]
        text = doc_dic["7. content"]
        text = title + text
        doc_frequency = calc_doc_frequency(text)
        doc_dic["doc_frequency"] = doc_frequency
        update_corpus_frequency(corpus_frequency, doc_dic["doc_frequency"])
        print(len(corpus_frequency))
        
    # now that updated, for each document, add in tfidf self score
    for i in range(len(doc_list)):
        doc_dic = doc_list[i]
        tfidf_vec_length = calc_tfidf_vec_length(doc_dic["doc_frequency"],
                                                 corpus_frequency, n)
        # print(doc_dic["4. title"])
        # print("has tfidf_vec_length = {0:.2f}".format(tfidf_vec_length))
        doc_dic["tfidf_vec_length"] = tfidf_vec_length


def get_top_similarities(doc_dict, prettyprint=True, threshold=0.4):
    """Returns ordered list of matching documents given threshold as
tuples: (name, score

    """
    similarity = doc_dict["similarity"]
    sorted_similarity = sorted(similarity.items(),
                               key=operator.itemgetter(1), reverse=True)
    #  This is a list of tuples
    sorted_similarity = sorted_similarity[:5]

    filtered = [(k, v) for (k, v) in sorted_similarity if v > threshold]
    if filtered and prettyprint:
        print("\n\nTop similarities for {}".format(
            get_pub_name_title_mashup(doc_dict)))
        for doc, score in filtered:
            print("{0} : {1:.3f}".format(doc, score))
    return filtered


def main():
    # db_docs = FeedItem.items_eligible_for_similarity_score() # All feed_items with content field available

    bias_dic = read_json('data.json')
    print("number of C's: {}".format(len(bias_dic["C"])))
    print("number of L's: {}".format(len(bias_dic["L"])))
    print("number of R's: {}".format(len(bias_dic["R"])))
    print("keys: {}".format(bias_dic.keys()))
    doc_list = list()  # list of all documents
    for key in bias_dic.keys():  # returns a list of dictionaries
        doc_list.extend(bias_dic[key])
    print("len original doc_list: {}".format(len(doc_list)))
    
    t = time.time()
    
    # now have a list of all documents
    corpus_frequency = dict()  # dictionary for holding corpus frequency

    #  chop for testing
    doc_list_old = doc_list[::3]
    doc_list_new = doc_list[1::3]

    n = len(doc_list_old)  # total number of docs in corpus, right now
    update_df_and_cf_with_new_docs(doc_list_old, corpus_frequency, n)

    # batch_calculate_similarities
    exhaustive_similarities_calculation(doc_list_old, corpus_frequency, n)
    # find top similarities
    for i in range(n):
        doc_dict = doc_list_old[i]
        get_top_similarities(doc_dict)

    elapsed_time = time.time() - t
    print("elapsed_time = {}".format(elapsed_time))
    
    # -----------------------------------------------------------------
    # now for doc_list_new, create online algorithm
    # so first update df and cf
    n += len(doc_list_new)  # set n to total number of docs
    update_df_and_cf_with_new_docs(doc_list_new, corpus_frequency, n)
    # now do exhaustive_update for docs with themselves:
    exhaustive_similarities_calculation(doc_list_new, corpus_frequency, n)
    # now compare these docs with all other docs
    disjoint_sets_similarities_calculation(doc_list_new, doc_list_old,
                                           corpus_frequency, n)
    # find top similarities
    print("len doc_list_old = {}".format(len(doc_list_old)))
    print("len doc_list_new = {}".format(len(doc_list_new)))
    doc_list_old.extend(doc_list_new)
    print("after extension len doc_list_old = {}".format(len(doc_list_old)))
    for i in range(n):
        doc_dict = doc_list_old[i]
        get_top_similarities(doc_dict)

    elapsed_time = time.time() - t
    print("total elapsed_time = {}".format(elapsed_time))

 # FINAL STEP (works for new or existing association): Association.objects.update_or_create(base_feed_item=main_doc, associated_feed_item=docs_we_found_similiarities_for, defaults={'similarity_score': new_or_updated_similarity_score})


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

if __name__ == "__main__":
    main()
