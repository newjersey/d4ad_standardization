import spacy
import pandas as pd
from spacy.tokenizer import Tokenizer

#  from https://spacy.io/usage/linguistic-features#native-tokenizers
special_cases = {":)": [{"ORTH": ":)"}]}  # this keeps this string no matter what
prefix_re = re.compile(r'''^[[("']''') # this is regex for keeping prefixes in a string
suffix_re = re.compile(r'''[])"']$''') # ^ but for suffices
infix_re = re.compile(r'''[-~]''') # this keeps these characters
simple_url_re = re.compile(r'''^https?://''') # this is annoying

# build a custom tokenizer
#
# we want to build a tokenizer that:
#   splits on stopwords with certain dependencies  (like to but not Abilty To Benefit)
#   splits on commas, word like and
def custom_tokenizer(nlp):
    return Tokenizer(nlp.vocab, rules=special_cases,
                                prefix_search=prefix_re.search,
                                suffix_search=suffix_re.search,
                                infix_finditer=infix_re.finditer,
                                url_match=simple_url_re.match)

# todo: set as env variable for raw main table
filepath = "./data/raw/etpl_all_programsJune3.xls"

columns = [
    "NAME_1",
    "DESCRIPTION",
    "PREREQUISITES",
    "DESCRIPTION",
    "FEATURESDESCRIPTION"
]

df = pd.read_excel(filepath, usecols=columns)
small_df = df.sample(n=100, random_state=42)
#  need to suss this out but basically, need a giant list of words,
# ONET tech list, (maybe even skills), Credential Engine Competency framework(s)
# (https://credentialfinder.org/ , select frameworks)

nlp = spacy.load("en_core_web_lg")

nlp.tokenizer = custom_tokenizer(nlp)
