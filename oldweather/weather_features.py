#!/usr/bin/env python3

import argparse
import csv
import logging
import re

import pandas as pd

import nltk
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize.treebank import TreebankWordTokenizer

import textblob

LOG = logging.getLogger(logging.basicConfig())
LOG.setLevel(logging.DEBUG)

# these features are hand-picked for now
# WEATHER_FEATURES = {
#     'WET': ['wet', 'shower', 'rain', 'drizzle', 'snow', 'hail'],
#     'DRY': ['dry'],
#     'COLD': ['cold', 'wintri', 'hail', 'snow', 'chill', 'icy', 'ici', 'frost', 'frosti'],
#     'WARM': ['warm', 'mild'],
#     'CLOUDY': ['overcast', 'hazi', 'cloudi', 'cloudy', 'dull', 'cloud'],
#     'SUNNY': ['bright', 'clear', 'sunshin', 'sun', 'sunni'],
# }

def hyponyms_and_self(*ssids):
    synsets = []
    for ssid in ssids:
        ss = wn.synset(ssid)
        synsets.append(ss)
        # all of the hyponyms and not just the direct children
        synsets.extend(ss.closure(lambda s: s.hyponyms(), depth=9999))
    return set(synsets)

CONCEPTS_COLD = hyponyms_and_self(
    'coldness.n.03',
    'cold.n.03',
    'snow.n.01',
    'snow.n.02',
    'winter.n.01',
    'freeze.v.01',
    'freeze.v.02',
    'freeze.v.03',
    'frosty.s.02',
    'cold.a.01',
)

CONCEPTS_HOT = hyponyms_and_self(
    'hotness.n.01',
    'heat.n.03',
    'warmth.n.03',
    'heat.v.01',
    'heat.v.02',
    'heat.v.04',
    'warm.v.01',
    'warm.v.02',
    'warm.a.01',
    'hot.a.01',
)

CONCEPTS_WET = hyponyms_and_self(
    'wetness.n.01', 
    'precipitation.n.03',
    'wet.v.01',
    'rain.v.01',
    'wet.a.01',
    'wet.a.02',
)

CONCEPTS_DRY = hyponyms_and_self(
    'dry.v.01',
    'dry.v.02',
    'dry.a.01',
)

CONCEPTS_CLOUDY = hyponyms_and_self(
    'cloudy.a.02',
    'overcast.a.01',
    'overcast.n.01',
    'overcast.n.02',
    'cloud.n.01',
)

CONCEPTS_WINDY = hyponyms_and_self(
    'gale.n.01',
    'gust.n.01',
    'blowy.s.01',
    'wind.n.01',
    'blustering.s.01',
)

STOPWORDS = set(stopwords.words('english'))

def synset_similarity(blob, concept):
    total = 0.0
    for word in blob.words:
        if word in STOPWORDS:
            continue
        match = concept.intersection(word.synsets)
        if match:
            LOG.debug("matched word: %s synsets: %s" % (word, match))
            total += 1.0
    
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, nargs="+")
    parser.add_argument('output', type=str)
    parser.add_argument('--write_header', action='store_true')
    args = parser.parse_args()
    
    with open(args.output, 'w') as f:
        cw = csv.writer(f, csv.QUOTE_ALL)
        header = ['date', 'source', 'forecast']
        header.extend(['COLD', 'HOT', 'WET', 'DRY', 'CLOUDY', 'WINDY'])
        if args.write_header:
            cw.writerow(header)

        for ifname in args.input:
            input_file = pd.read_csv(ifname)
            for row in input_file.iterrows():
                raw_date = row[1].date
                raw_text = row[1].forecast
                raw_src = row[1].source
                blob = textblob.TextBlob(raw_text)
                row = [raw_date, raw_src, raw_text]
                row.append("%0.2f" % (synset_similarity(blob, CONCEPTS_COLD)))
                row.append("%0.2f" % (synset_similarity(blob, CONCEPTS_HOT)))
                row.append("%0.2f" % (synset_similarity(blob, CONCEPTS_WET)))
                row.append("%0.2f" % (synset_similarity(blob, CONCEPTS_DRY)))
                row.append("%0.2f" % (synset_similarity(blob, CONCEPTS_CLOUDY)))
                row.append("%0.2f" % (synset_similarity(blob, CONCEPTS_WINDY)))
                cw.writerow(row)


if __name__ == "__main__":
    main()