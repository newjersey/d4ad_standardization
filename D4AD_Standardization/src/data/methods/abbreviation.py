import spacy
import pandas as pd
from spacy.matcher import Matcher
# todo: refactor to accept content or non-content matcher
#           generate content from provided column using matcher
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
        [{'ORTH': ';'}],
        # TODO: fix this to work, i could be special casing too early/improperly
        # modifiction seen random_state*2
        [{'IS_SPACE': True}], # captures present spaces after tokenizations
    ]

matcher = Matcher(nlp.vocab)
matcher.add("DoNotStandardize", patterns)

BATCH_SIZE = 50

small_df2.fillna('', inplace=True)

def make_batch_of_docs(df, column_index=0, nlp=nlp, batch_size=BATCH_SIZE, disable=["parser","ner", "entity_linker"]):
    yield nlp.pipe(df.iloc[:,column_index].values,
                   batch_size=batch_size,
                   disable=disable)


def make_standardizable_matches():
    pass


total_cases = 0
for row in small_df2.iterrows():
    prerequisites = row[1].PREREQUISITES
    if isinstance(prerequisites, str):
        for doc, matches in matcher.pipe(return_matches=True,
                                         batch_size=1000):
            # yield standardable content
            match_start = 0
            for match in matches:
                total_cases += 1
                match_end = match[2]
                print("\t", doc[match_start:match_end])
                yield doc[match_start:match_end]
                match_start = match[2]
            yield doc[match_start:]
    else:
        total_cases += 1

# Importing the libraries 
import pandas as pd 
import missingno as msno 
  
# Loading the dataset 
df = pd.read_csv("kamyr-digester.csv") 
  
# Visualize the number of missing 
# values as a bar chart 
msno.bar(df) 


""" small_df2 = df.sample(n=N, random_state=random_state*2)

# quick and dirty eval loop; random_seed = 42 for 100 samples had
# 6 wrong, prodigy NER sheet recommends you use rule matchers if
# you're sure they evalute better than 90%
case_rows = []

number_incorrect = 0
total_cases = 0
for row in small_df2.iterrows():
    if isinstance(row[1].PREREQUISITES, str):
        doc = \
            nlp(row[1].PREREQUISITES)
        matches = matcher(doc)
        # pipe might be faster but we're only examining 100 cases
        print("\t {} Prerequistites:\t".format(row[0]), doc)
        match_start = 0
        for match in matches:
            total_cases += 1
            match_end = match[2]
            print(doc[match_start:match_end])
            answer = input("correct?")
            if answer == 'n':
                number_incorrect += 1
                case_rows.append(row[0])
            match_start = match[2]
            #match_end = match[2]
        # print last match
        print(doc[match_start:])
        answer = input("correct?")
        if answer == 'n':
            number_incorrect += 1
    else:
        total_cases += 1

print("After that examination we found " + str(number_incorrect) + "  cases out of {}".format(total_cases))
print("{}".format((total_cases-number_incorrect)/total_cases))


doc = nlp(small_df.iloc[0].PREREQUISITES)
matches = matcher(doc) #  [(14862748245026736845, 2, 3)] --> [or]

# see: matcher.pipe
# at https://spacy.io/api/matcher#pipe """