import pandas as pd

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

#  need to suss this out but basically, need a giant list of words,
# ONET tech list, (maybe even skills), Credential Engine Competency framework(s)
# (https://credentialfinder.org/ , select frameworks)