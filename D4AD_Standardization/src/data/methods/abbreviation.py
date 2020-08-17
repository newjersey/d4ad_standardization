import spacy
import pandas as pd
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_lg")

# todo: set as env variable for raw main table
filepath = "./data/raw/etpl_all_programsJune3.xls"

columns = [
    "NAME_1",
    "DESCRIPTION",
    "PREREQUISITES",
    "DESCRIPTION",
    "FEATURESDESCRIPTION"
]

random_state = 42
N = 100
df = pd.read_excel(filepath, usecols=columns)
small_df = df.sample(n=N, random_state=random_state)
#  need to suss this out but basically, need a giant list of words,
# ONET tech list, (maybe even skills), Credential Engine Competency framework(s)
# (https://credentialfinder.org/ , select frameworks)

# Abrreviation unstandardrandom_state, N patterns
patterns =\
    [
        # these break up small_df.iloc[0] into unstandardized tokens
        #[{'POS': 'PUNCT'}],  # fails in later samples
        [{'POS': 'CCONJ'}],
        # modifiction that breaks up small_df.iloc[7]
        [{'ORTH': '/'}],
        # modifiction that combines small_df.iloc[15], [1]
        [{'ORTH': ','}],
        # modifiction seen generally past 50 or os
        [{'ORTH': ';'}]
    ]

matcher = Matcher(nlp.vocab)
matcher.add("DoNotStandardize", patterns)

doc = nlp(small_df.iloc[0].PREREQUISITES)
matches = matcher(doc) #  [(14862748245026736845, 2, 3)] --> [or]

# see: matcher.pipe
# at https://spacy.io/api/matcher#pipe