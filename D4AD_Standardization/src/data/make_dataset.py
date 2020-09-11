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

get_standardized =\
    {'NAME': 'STANDARDIZED_NAME'}

def input(from_filepath=None, from_table=None):
    df = None
    if from_filepath:
        file_extension = from_filepath.rsplit('.',1)[1]
        
        if file_extension in ('xls', 'xlsx'):
            df = pd.read_excel(from_filepath)

    return df


def make_course_name(from_df):
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
        make_course_name(input(from_filepath, from_table))

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
