# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import pandas as pd
from utils.dataframe_manipulation import (
    replace_values,
    extract_values,
    split_on,
    write_out
)
from utils.abbreviation import multiple_mapper

get_standardized =\
    {
        'NAME': 'STANDARDIZED_NAME',
        'NAME_1': 'STANDARDIZED_NAME1'
    }

def input(from_filepath=None, from_table=None):
    df = None
    if from_filepath:
        file_extension = from_filepath.rsplit('.',1)[1]
        
        if file_extension in ('xls', 'xlsx'):
            df = pd.read_excel(from_filepath)

    return df


def course_name(from_df):
    to_df = from_df
    field = 'NAME'

    # First we remove extranous content after the hyphen
    # e.g. "Program Management[ - Clemsen - A.S. Title IV]"
    to_df[get_standardized[field]] =\
        split_on(to_df[field],
                 " - ",
                 n=1,
                 get_first_n_results=1)

    # then we handle content immediately prior to a hyphen
    # e.g. "Program Management[- Clemsen - A.S. Title IV]"
    regex_pattern = '''
                    ^                   # start from beginning
                    (.+?                # capture everything non-greedily ...
                        (?:(?!-\s)      # ... except for the '- ', if it's there
                            .)          # and continue to match any character
                    *)                  # ... as many times as we can
                    '''
    to_df[get_standardized[field]] =\
        extract_values(to_df[field], regex_pattern)

    # ... finally we handle odd fixed patterns that are common
    # e.g. "Program Management[- Clemsen (orange)"
    to_df[get_standardized[field]] =\
        replace_values(to_df[field], "\(orange\)")

    to_df[get_standardized[field]] =\
        replace_values(to_df[field], "closed")

    return to_df


def provider_name(from_df):
    to_df = from_df
    field = 'NAME_1'
    standardized_field = get_standardized[field]

    # Silver Version of Provider Names
    #
    # We first extract provider names from different locations
    # depending on whether the `field` starts, ends or internally
    # has a paranethesis. 
    # 
    # Note that we access the regex <the_name> group from the result

    # If provider field starts with a (...
    to_df[standardized_field] = ""
    open_parenthesis_index = to_df[field].str[0] == '('
    open_parenthesis_regex = '''
                    (?P<paren>\(.*\)) # get the first parathesis
                    (?P<the_name>.*)  # then get the actual name
                    '''
    to_df.loc[open_parenthesis_index, standardized_field] =\
        extract_values(
            to_df.loc[open_parenthesis_index, field],
            open_parenthesis_regex).the_name

    # If provider field ends with a )...
    close_parenthesis_index = to_df[field].str[-1] == ')'
    closing_parenthesis_regex = '''
                    (?P<the_name>.*)  # get the actual name
                    (?P<paren>\(.*\)) # get the last parathensis                
                    '''
    to_df.loc[close_parenthesis_index, standardized_field] =\
        extract_values(
            to_df.loc[close_parenthesis_index, field],
            closing_parenthesis_regex).the_name

    # For those fields remaining, if a ( or ) exists ....
    internal_parenthesis_index =\
        to_df[field].str.contains('\(|\)', regex=True) &\
            ~(close_parenthesis_index|open_parenthesis_index)

    to_df.loc[internal_parenthesis_index, standardized_field] =\
        extract_values(
            to_df.loc[internal_parenthesis_index, field],
            closing_parenthesis_regex).the_name

    # Finally, copy everything else that has no parentheses
    no_parenthesis_index = ~(close_parenthesis_index |\
                            open_parenthesis_index  |\
                            internal_parenthesis_index)
    to_df.loc[no_parenthesis_index, standardized_field] =\
        to_df.loc[no_parenthesis_index, field]

    return to_df

# This is waht 5.0 does butnot sure if well where picked up
def handle_abbreviations(from_df):
    # "Gold" (or Better) Version of fields
    #
    # Here we need to expand out abbreviations that are used
    # this promotes readabilty, understanding of what
    to_df = from_df
    field = 'NAME_1'
    standardized_field = get_standardized[field]

    to_df['MULTI_REPLACE_STANDARDIZEDNAME_1'] =\
        to_df[standardized_field].dropna().map(multiple_mapper) # ~ 26k rows/10 seconds

    return to_df

@click.command()
@click.argument('output_filepath', type=click.Path(), default="./D4AD_Standardization/data/interim/")
@click.argument('from_filepath', type=click.Path(exists=True), default="./D4AD_Standardization/data/raw/etpl_all_programsJune3.xls")
@click.argument('from_table', type=str, default='')
def main(output_filepath, from_filepath, from_table):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('... making final data set from raw data')

    out_df =\
        course_name(from_df=input(from_filepath, from_table))
    out_df =\
        provider_name(from_df=out_df)
    out_df =\
        handle_abbreviations(from_df=out_df)

    # temp: write this so we know what's going on
    write_out(out_df, output_filepath, content_is='test_output')



if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
