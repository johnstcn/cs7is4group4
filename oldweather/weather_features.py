#!/usr/bin/env python3

import argparse
import csv
import logging
import re

import pandas as pd

import nltk
from nltk.corpus import wordnet as wn
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
        synsets.extend(ss.hyponyms())
    return set(synsets)

CONCEPTS_COLD = {
    'n': hyponyms_and_self('coldness.n.03', 'cold.n.03', 'snow.n.01', 'snow.n.02', 'winter.n.01'),
    'v': hyponyms_and_self('freeze.v.01', 'freeze.v.02', 'freeze.v.03'),
    'a': hyponyms_and_self('cold.a.01'),
}

CONCEPTS_WET = {
    'n': hyponyms_and_self('wetness.n.01', 'precipitation.n.03'),
    'v': hyponyms_and_self('wet.v.01', 'rain.v.01'),
    'a': hyponyms_and_self('wet.a.01', 'wet.a.02'),
}

forecasts_boards = pd.read_csv(open('../data/boards_mtcranium_forecast_2018.csv'))
forecasts_met = pd.read_csv(open('../data/met_forecast_waybackmachine_partial_2018.csv'))



def penn2wordnet(tag):
    if tag.startswith('N'):
        return 'n'
    
    if tag.startswith('V'):
        return 'v'
    
    if tag.startswith('J'):
        return 'a'

    if tag.startswith('R'):
        return 'r'

    return None


def synset_similarity(blob, concept):
    sims = {}
    counts = {}
    for word, tag in blob.tags:
        word_sim = 0
        wn_tag = penn2wordnet(tag)
        if not wn_tag:
            continue

        if wn_tag not in counts:
            counts[wn_tag] = 1
        else:
            counts[wn_tag] += 1

        concept_synsets = concept.get(wn_tag, set())
        match = concept_synsets.intersection(word.synsets)
        if match:
            LOG.debug("matched word: %s synsets: %s" % (word, match))
            word_sim = 1

        if wn_tag not in sims:
            sims[wn_tag] = word_sim
        else:
            sims[wn_tag] += word_sim
    
    if not sims:
        return None

    total = 0.0
    for key in sims.keys():
        total += sims[key]

    # XXX: weighting by total number of tokens by POS tag does not seem very useful
    LOG.debug("counts: %s similarities: %s" % (counts, sims))
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
        header.extend(['COLD', 'WET'])
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
                row.append("%0.2f" % (synset_similarity(blob, CONCEPTS_WET)))
                cw.writerow(row)


if __name__ == "__main__":
    main()