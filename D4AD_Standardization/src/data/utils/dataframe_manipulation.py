import pandas as pd
import re
import regex

ROOT_PATH = "/hdd/work/d4ad_standardization/"

# We establish a common api on which to manipulate dataframes
# these are mostly pass through but make code more DRY and
# include common defaults for this application

def replace_values(the_series, to_replace, value="", regex=False):
    return \
        the_series.str.replace(
            to_replace,
            value,
            regex=regex
        )

def extract_values(the_series, pat, flags=re.VERBOSE):
    return \
        the_series.str.extract(
            pat=pat,
            flags=flags
        )

def split_on(the_series, split_on_string, n=1, get_first_n_results=1):
    return \
        the_series.str.split(
            split_on_string,
            n=n
        )[:get_first_n_results]

def write_out(the_df, write_path, content_is, root_path=ROOT_PATH, file_type=".csv"):
    if '.csv' == file_type:
        the_df.to_csv(root_path + write_path + f"{content_is}.{file_type}",
              index = False,
              chunksize = 10000)


# technically not manipulation, but this type of search happens a lot
def indices_from_regex_search(the_series, the_regex):
    return the_series.dropna()\
                     .map(the_regex.search)\
                     .dropna().index
