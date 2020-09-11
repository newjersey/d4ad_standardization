import pandas as pd
import numpy as np
import random
import pickle
import re
import regex  # for better, more capbale regex api
import os
import zipfile
import more_itertools
from itertools import chain
from .dataframe_manipulation import ROOT_PATH

label_mapper = pd.read_csv(
    ROOT_PATH + "./D4AD_Standardization/data/external/" + "label_mapper.csv"
)

def make_term_grouped_regex(term="", right_regex="", left_regex=""):
    mystr = left_regex + '(' +\
                re.escape(term) +\
            ')' + right_regex
    return mystr

def make_grouped_regexes(replacement, left_regex="", right_regex=""):
    return (make_term_grouped_regex(left_regex=left_regex,
                                    term=key,
                                    right_regex=right_regex)\
            for key in replacement.keys()
    )

def construct_map(label_mapper):
    return {
        **dict(zip(label_mapper.abbreviation, label_mapper.expanded))
    }

def multiple_mapper(string):
    return abbrevation_pattern.sub(
        lambda x: \
        x.group().replace( # replace the found string
            more_itertools.first_true(x.groups() # where the first matched group...
        ),  replacement_map[more_itertools.first_true(x.groups())] # ... is replaced with the lookup
    ), string)

replacement_map = construct_map(label_mapper)

# Regex caveat: There can be matches that are subpatterns of each other
# I've only really seen this with Oracle OCP and CDL XYZ but in theory
# it could occur with another pattern so I'm hesitant to special case it
#
# So, I use POSIX leftmost longest matching, see: https://bitbucket.org/mrabarnett/mrab-regex/issues/150
# to implement longest matching, with `(?p)`
#
# This generally will make matching take slightly longer, but it should be
# only longer linear in the number of possible matching patterns in a given pattern
abbrevation_pattern =\
    regex.compile(
        "(?p)" +
        "|".join(   # match words at start of string
            make_grouped_regexes(replacement_map, left_regex=r'^', right_regex=r'[\s:]')
        ) + "|" +\
        "|".join(   # match words surrounded by spaces
            make_grouped_regexes(replacement_map, left_regex=r'\s', right_regex=r'\s')
        ) + "|" +\
        "|".join(   # match words that make up entire fields, e.g. 'Nursing'
            make_grouped_regexes(replacement_map, left_regex=r'^', right_regex=r'$')
        ) + "|" +\
        "|".join(   # match words at end of string preceded by space or slash
            make_grouped_regexes(replacement_map, left_regex=r'[\s/]', right_regex=r'$')
        ) + "|" +\
        "|".join(   # match words within string that follow a slash, end with a space or slash
            make_grouped_regexes(replacement_map, left_regex=r'/', right_regex=r'[\s/]')
        )
    )