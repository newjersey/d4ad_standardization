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
from utils.etpl_field_names import (
    sql_etpl_field_names,
    sql_excel_field_map,
    labor_fields_to_internal,
    internal_fields_to_labor,
    labor_etpl_field_names
)


logger = logging.getLogger(__name__)

# For better or worse, from different data soruces,
# I called field names all kinds of things. This dictionary
# returns the canonical name so that we don't have to hard code
# things everywhere. The source name is assumed to be unique.
canonical_field_name =\
    {
        'NAME': 'name',
        'NAME_1': 'name_1',
        'mentioned_job_search_duration': 'mentioned_job_search_duration'
    }

get_standardized =\
    {
        'name': 'standardized_name',
        'name_1': 'standardized_name_1',
        'description': 'standardized_description',
        'featuresdescription': 'standardized_featuresdescription',
        "is_wioa": "mentions_wioa"
    }

def input_source(from_filepath=None, from_table=None, remap_field_names=False, source="labor", debug_sample=None):
    df = None
    if from_filepath:
        file_extension = from_filepath.rsplit('.',1)[1]
        
        if file_extension in ('xls', 'xlsx'):
            df = pd.read_excel(from_filepath)
        if file_extension in ('csv'):
            df = pd.read_csv(from_filepath)
        
        # We ignore case by lowercasing all column names (e.g. labor gives
        # different casing than sql, etc)
        df.columns = map(str.lower, df.columns)

        if debug_sample:
            # Cheap way to run over a very small subset, inspect output
            df = df.sample(debug_sample)

    if remap_field_names:
        the_map = None
        if source=="sql":
            fields_in_common = sql_etpl_field_names.intersection(
                set(df.columns)
                )
            the_map = sql_excel_field_map

        if source == "labor":
            fields_in_common = labor_etpl_field_names.intersection(
                set(df.columns)
                )
            the_map = labor_fields_to_internal


        if len(fields_in_common) > 0:
            df =\
                df.rename(
                    columns=the_map
                )

    return df


def parenthesis_related(from_df, the_field):
    to_df = from_df
    # field = canonical_field_name[the_field]
    # standardized_field = get_standardized[field]
    field = canonical_field_name.get(the_field, the_field)
    standardized_field = get_standardized.get(field, field)

    # First we remove extranous content after the hyphen
    # e.g. "Program Management[ - Clemsen - A.S. Title IV]"
    to_df[standardized_field] =\
        split_on(to_df[field],
                 " - ",
                 n=1,
                 get_nth_result=1)

    # then we handle content immediately prior to a hyphen
    # e.g. "Program Management[- Clemsen - A.S. Title IV]"
    regex_pattern = '''
                    ^                   # start from beginning
                    (.+?                # capture everything non-greedily ...
                        (?:(?!-\s)      # ... except for the '- ', if it's there
                            .)          # and continue to match any character
                    *)                  # ... as many times as we can
                    '''
    to_df[standardized_field] =\
        extract_values(to_df[standardized_field], regex_pattern)

    # ... finally we handle odd fixed patterns that are common
    # e.g. "Program Management[- Clemsen (orange)"
    to_df[standardized_field] =\
        replace_values(to_df[standardized_field], "\(orange\)")

    to_df[standardized_field] =\
        replace_values(to_df[standardized_field], "closed")

    return to_df


def structured_parenthesis_related(from_df, the_field):
    to_df = from_df
    field = canonical_field_name.get(the_field, the_field)
    standardized_field = get_standardized.get(field, field)

    # Silver Version of Provider Names
    #
    # We first extract provider names from different locations
    # depending on whether the `field` starts, ends or internally
    # has a paranethesis. 
    # 
    # Note that we access the regex <the_name> group from the result

    # If provider field starts with a (...
    if not standardized_field in to_df:
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
    # note that we operate on `standardized_field` from this
    # point forward
    close_parenthesis_index = to_df[field].str[-1] == ')'
    closing_parenthesis_regex = '''
                    (?P<the_name>.*)  # get the actual name
                    (?P<paren>\(.*\)) # get the last parathensis                
                    '''
    to_df.loc[close_parenthesis_index, standardized_field] =\
        extract_values(
            to_df.loc[close_parenthesis_index, standardized_field],
            closing_parenthesis_regex).the_name

    # For those fields remaining, if a ( or ) exists ....
    internal_parenthesis_index =\
        to_df[standardized_field].str.contains('\(|\)', regex=True) &\
            ~(close_parenthesis_index|open_parenthesis_index)

    to_df.loc[internal_parenthesis_index, standardized_field] =\
        extract_values(
            to_df.loc[internal_parenthesis_index, standardized_field],
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
        "AA Degree",
        "A.A. Degree",
        "A.A.S. Degree",
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

    the_fields = [get_standardized['name_1'],
                  'description', 
                  'featuresdescription']
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

    field = get_standardized['is_wioa']
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

    to_df['mentioned_certificate'] = False
    to_df.loc[cert_indices, 'mentioned_certificate'] = True

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

    to_df['mentioned_associates'] = False
    to_df.loc[assoc_indices, 'mentioned_associates'] = True

    return to_df

def job_search_duration(from_df):
    to_df = from_df
    
    field = get_standardized['is_wioa']
    wioa_indices = to_df[field] == True
    to_df['default_job_search_duration'] = "0"
    to_df.loc[wioa_indices, 'default_job_search_duration'] = "6 months"

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
        to_df.loc[wioa_indices, 'description']\
            .str\
            .extractall(pat=training_context_regex, flags=re.I|re.VERBOSE)[0]

    field = canonical_field_name['mentioned_job_search_duration']
    to_df[field] = None
    job_search_length_mention =\
        job_search_length_mention.str.extract(
            duration_regex,
            flags=re.I|re.VERBOSE
        ).replace('-', '')\
        .replace('week', 'weeks')\
        .dropna()
    
    if not job_search_length_mention.empty:
        job_search_length_mention =\
            job_search_length_mention.droplevel('match')  # drop uneeded multi-index 

        to_df.loc[job_search_length_mention.index,
                field] =\
                    job_search_length_mention['numeric'] +\
                    job_search_length_mention['modifer'] +\
                    job_search_length_mention['base_duration']
    
    return to_df


@click.command()
@click.argument('remap_field_names', default=True)
@click.argument('output_filepath', type=click.Path(), default="./D4AD_Standardization/data/interim/")
@click.argument('from_filepath', type=click.Path(exists=True), default="./D4AD_Standardization/data/raw/sql_header_etpl_all_programsJune3.xls")
@click.argument('from_table', type=str, default='')
def main(remap_field_names, output_filepath, from_filepath, from_table):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger.info('Making final data set from raw data')

    remap_field_names = remap_field_names

    logger.info(f"... reading in input dataset, remap field names is set to {remap_field_names}")
    from_df = input_source(from_filepath, from_table, remap_field_names=remap_field_names)
    logger.info('... standardizing course names')    
    out_df =\
        parenthesis_related(from_df=from_df, the_field='NAME')
    out_df =\
        structured_parenthesis_related(from_df=out_df, the_field='standardized_name')
    
    logger.info('... standardizing provider names')
    out_df =\
        parenthesis_related(from_df=out_df, the_field='NAME_1')
    out_df =\
        structured_parenthesis_related(from_df=out_df, the_field='standardized_name_1')
    
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

    content_is='standardized_etpl'
    logger.info(f"Done. Writing {content_is} to {output_filepath}. Remap fields names is {remap_field_names}")

    write_out(out_df, output_filepath, content_is='standardized_etpl', remap_field_names=remap_field_names, remapper=internal_fields_to_labor)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
