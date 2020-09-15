import pandas as pd
import re
import regex
import logging
import os
# from .etpl_field_names import excel_to_sql_name_map, sql_type_map

ROOT_PATH = os.getcwd() + "/"

logger = logging.getLogger(__name__)

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

def write_out(the_df, write_path, content_is, root_path=ROOT_PATH,
              file_type="csv", remap_field_names=False):

    if remap_field_names:
        the_df =\
            the_df.rename(
                columns=excel_to_sql_name_map
            )
        for field_name, sql_type in sql_type_map.items():
            if sql_type == "boolean":
                make_false = the_df[field_name] == ''

                the_df.loc[make_false, field_name] = False
                the_df.loc[~make_false, field_name] = True

    if 'csv' == file_type:
        logger.info(f" ... writing to " + root_path + write_path + f"{content_is}.{file_type}")
        the_df.to_csv(root_path + write_path + f"{content_is}.{file_type}",
              index = False,
              chunksize = 10000)