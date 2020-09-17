import os
import pandas as pd
import re
import regex
import logging
from .etpl_field_names import (
    excel_to_sql_name_map,
    sql_type_map,
    internal_fields_to_labor
)

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

def split_on(the_series, split_on_string, n=1, get_nth_result=1):
    return \
        the_series.str.split(
            split_on_string,
            n=n,
            expand=True
        ).iloc[:,:get_nth_result]

def write_out(the_df, write_path, content_is, root_path=ROOT_PATH,
              file_type="csv", remap_field_names=False, remapper=None):

    if remap_field_names:
        the_df =\
            the_df.rename(
                columns=remapper
            )
        for field_name, sql_type in sql_type_map.items():
            if sql_type == "boolean":
                make_false = the_df[field_name] == ''

                the_df.loc[make_false, field_name] = False
                the_df.loc[~make_false, field_name] = True

    # Pandas does not default to nullable integers on read_csv
    # So we attempt type inference with the following
    numeric_columns = df.select_dtypes(include='number')

    for column in numeric_columns:
        looks_like_integer = (df[column].fillna(1) % 1 == 0).all()
        if looks_like_integer:
            # then we have integers that were converted to float because
            # we also have NaNs. We convert to special integer type
            # that can handle NaNs, instead.
            df[column] =\
                df[column].astype('Int64')    

    if 'csv' == file_type:
        logger.info(f" ... writing to " + root_path + write_path + f"{content_is}.{file_type}")
        the_df.to_csv(root_path + write_path + f"{content_is}.{file_type}",
              index = False,
              chunksize = 10000)