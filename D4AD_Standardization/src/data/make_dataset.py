# -*- coding: utf-8 -*-
import click
import logging
import datetime
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import pandas as pd
import regex
import re         # for field identification
from utils.dataframe_manipulation import (
    replace_values,
    extract_values,
    split_on,
    write_out
)
from utils.abbreviation import multiple_mapper
from utils.field_indicator import get_name_name1_descriptions_indices

logger = logging.getLogger(__name__)

get_standardized =\
    {
        'NAME': 'STANDARDIZED_NAME',
        'NAME_1': 'STANDARDIZED_NAME1',
        'DESCRIPTION': 'STANDARDIZED_DESCRIPTION',
        'FEATURESDESCRIPTION': 'STANDARDIZED_FEATURESDESCRIPTION',
        "IS_WIOA": "MENTIONS_WIOA"
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

    # ... now we remove degree related mentions that are left over
    degree_cert_variants =\
        ["A.S.",
        "AAS Degree",
        "AAS -",
        "A.S. Degree",
        "AS Degree",     
        "Degree",
        "degree",
        "certificate",
        "Certificate",
        "Associate of Applied Science",
        "-[\s\b]Associate",
        "^\s*In\b"]

    # to_df[standardized_field] =\
    #     replace_values(to_df[standardized_field],
    #                    degree_cert_variants,
    #                    regex=True)
    # I don't know why the above doesn't accept the list when it
    # internally calls the same function below...
    to_df[standardized_field] =\
        to_df[standardized_field].replace(degree_cert_variants, "", regex=True)

    return to_df

def handle_abbreviations(from_df):
    # "Gold" (or Better) Version of fields
    #
    # Here we need to expand out abbreviations that are used;
    # this promotes readabilty, understanding of what. Note
    # that this process replaces multiple abbrecations within a given string
    # so it can take a while. I've used regexs, which are in C
    # should be about as fast as possible.
    to_df = from_df

    # write timing to log
    start = datetime.datetime.now()
    logger.info(f"\t[abbreviation] starting at {start}")

    the_fields = [get_standardized['NAME_1'],
                  'DESCRIPTION', 
                  'FEATURESDESCRIPTION']
    for a_field in the_fields:
        # get the standardized field if it exists, else returns same field
        # so we can self-modify it
        standardized_field = get_standardized.get(a_field, a_field)
        to_df[standardized_field] =\
            to_df[a_field].dropna().map(multiple_mapper)
    end = datetime.datetime.now()

    logger.info(f"\t[abbreviation] stopped at {end}")
    logger.info(f"\t[abbreviation] took {(end-start)} time")
    return to_df

def mentions_wioa(from_df):
    to_df = from_df

    wioa_like =\
        regex.compile(
            '''
            (title\s+[IV1234]+\b\s*?)           # WOIA has 4 titles of funding in law, at end of sentence or space
            |(wioa){d<=1}                       # is called WOIA, WIA, allowed to miss a letter
            ''',
            flags=regex.I|regex.VERBOSE)

    wioa_indices =\
        get_name_name1_descriptions_indices(wioa_like, to_df)

    field = get_standardized['IS_WIOA']
    to_df[field] = False
    to_df.loc[wioa_indices, field] = True

    return to_df

def mentions_certificate(from_df):
    to_df = from_df
    cert_like =\
        regex.compile(
            '''
            (certification)
            |(certificate)
            |[\s\b](cert)[\s\b]
            ''',
            flags=regex.I|regex.VERBOSE)
    cert_indices =\
        get_name_name1_descriptions_indices(cert_like, to_df)

    to_df['Mentioned_Certificate'] = False
    to_df.loc[cert_indices, 'Mentioned_Certificate'] = True

    return to_df

def mentions_associates(from_df):
    to_df = from_df    
    as_like =\
        regex.compile(
            '''
            [\b\s](A\.A\.S\.)[\b\s]
            |[\b\s](A\.S\.)[\b\s]
            |[\b\s](AS\sDe)                   # AS Degree
            |[\b\s](AS\sSc)                   # AS Science
            |[\b\s](AAS)[\b\s]                # applied associates of science
            ''',
            flags=regex.VERBOSE)
    assoc_indices =\
        get_name_name1_descriptions_indices(as_like, to_df)

    to_df['Mentioned_Associates'] = False
    to_df.loc[assoc_indices, 'Mentioned_Associates'] = True

    return to_df

def job_search_duration(from_df):
    to_df = from_df
    field = get_standardized['IS_WIOA']
    wioa_indices = to_df[field] == True
    to_df['DEFAULT_JOB_SEARCH_DURATION'] = "0"
    to_df.loc[wioa_indices, 'DEFAULT_JOB_SEARCH_DURATION'] = "6 months"

    # We first extract the context in which mentions of
    # job searches occur (e.g. job search, assistance with employment search, etc.)
    training_context_regex =\
        """
        ((\w+\W+){0,8}        # first 8 or so words before
        (?P<job_search>job[\s\b.].*?search|assist[\w\s\b\.].*?employ\w*?\b) # help w/ job search
        (\W+\w+){0,8})       # and last 8 or so word after
        """

    # ... then we search for specific mentions of numerically qualified durations,
    # like four months. We take these as job search durations. Note there aren't
    # very many of them.
    numbers = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen"
    durations = "minute|day|week|month|year"
    duration_regex =\
       f"""
        (?P<numeric>\d|{numbers})       # numeric reference ...
        (?P<modifer>.*)                 # followed by content that might modify ...
        (?P<base_duration>{durations})     # ... the base duration
        """

    # todo: make this logic have fewer hardcoded things
    job_search_length_mention =\
        to_df.loc[wioa_indices, 'DESCRIPTION']\
            .str\
            .extractall(pat=training_context_regex, flags=re.I|re.VERBOSE)[0]

    field = 'MENTIONED_JOB_SEARCH_DURATION'
    to_df[field] = None
    job_search_length_mention =\
        job_search_length_mention.str.extract(
            duration_regex,
            flags=re.I|re.VERBOSE
        ).replace('-', '')\
        .replace('week', 'weeks')\
        .dropna()\
        .droplevel('match')  # drop uneeded multi-index 

    to_df.loc[job_search_length_mention.index,
              field] =\
                job_search_length_mention['numeric'] +\
                job_search_length_mention['modifer'] +\
                job_search_length_mention['base_duration']
    
    return to_df


@click.command()
@click.argument('output_filepath', type=click.Path(), default="./D4AD_Standardization/data/interim/")
@click.argument('from_filepath', type=click.Path(exists=True), default="./D4AD_Standardization/data/raw/etpl_all_programsJune3.xls")
@click.argument('from_table', type=str, default='')
def main(output_filepath, from_filepath, from_table):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger.info('Making final data set from raw data')

    logger.info('... standardizing course names')
    out_df =\
        course_name(from_df=input(from_filepath, from_table))
    logger.info('... standardizing provider names')
    out_df =\
        provider_name(from_df=out_df)
    logger.info('... standardizing abbreviations throughout ... will take a while ...')        
    out_df =\
       handle_abbreviations(from_df=out_df)
    logger.info('... identifying WIOA funded courses')
    out_df =\
        mentions_wioa(from_df=out_df)
    logger.info('... identifying certficate courses')
    out_df =\
        mentions_certificate(from_df=out_df)
    logger.info('... identifying associates')
    out_df =\
        mentions_associates(from_df=out_df)
    logger.info('... job search durations')
    out_df =\
        job_search_duration(from_df=out_df)

    # temp: write this so we know what's going on
    write_out(out_df, output_filepath, content_is='standardized_etpl')



if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
