#!/usr/bin/env python
# coding: utf-8

# In[44]:


import spacy
import nltk
import spacy_experimental
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nlp = spacy.load('en_core_web_sm')
nlp_coref = spacy.load("en_coreference_web_trf")

# use replace_listeners for the coref components
nlp_coref.replace_listeners("transformer", "coref", ["model.tok2vec"])
nlp_coref.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])


# we won't copy over the span cleaner
nlp.add_pipe("coref", source=nlp_coref)

def pre_process_text(input_text):
    input_text = input_text.replace("id", "identifier")
    doc = nlp(input_text)
    
    input_tokens = []
    for i, token in enumerate(doc):
        if token.tag_ == "CD":
            doc[i+1].pos_ = "X"

        if i < len(doc) - 1 and token.pos_ == "NOUN" and (doc[i+1].pos_ == "NOUN" or doc[i+1].pos_ == "ADJ"):
            input_tokens.append(token.text + "_" + doc[i+1].text)
        elif not (token.pos_ == "NOUN" and (doc[i-1].pos_ == "NOUN" or doc[i-1].pos_ == "ADJ")):
            input_tokens.append(token.text)
        elif (token.pos_ == "NOUN" and not(doc[i-1].pos_ == "NOUN")):
            input_tokens.append(token.text)

    input_tokens = [token.replace(',', '') for token in input_tokens]
    input_text = ' '.join(input_tokens)

    def remove_stopwords(words):
        stop_words = set(stopwords.words('english'))
        for word in words:
            stop_words.discard(word)
        return list(stop_words)

    words_to_remove = ["have", "having", "haven", "had", "has", "there", "each", "only", "all", "it's","own",
                       "same", "theirs", "any", "both", "and", "the", "it", "he", "she", "they", "them"]
    stop_words = remove_stopwords(words_to_remove)

    word_tokens = word_tokenize(input_text)
    
    
    filtered_sentence = [w for w in word_tokens if w not in stop_words]
    filtered_sentence = ' '.join(filtered_sentence)
    
    filtered_doc = nlp(filtered_sentence)
    
    extracted_info = []
    for token in filtered_doc:
        extracted_info.append({
            'word': 'id' if token.text == 'identifier' else token.text,
            'pos': 'NOUN' if token.text == 'identifier' or '_' in token.text else token.pos_,
            'ner': token.ent_type_,
            'tag': token.tag_
        })
    coref_clusters = []
    for cluster_key, cluster_mentions in filtered_doc.spans.items():
        mentions = [mention.text for mention in cluster_mentions]
        coref_clusters.append(mentions)

    for item in extracted_info:
        if coref_clusters and item['word'] == coref_clusters[0][1]:
            item['coreference_resolver'] = coref_clusters[0][0]
            del coref_clusters[0]
        else:
            item['coreference_resolver'] = None

    return extracted_info

