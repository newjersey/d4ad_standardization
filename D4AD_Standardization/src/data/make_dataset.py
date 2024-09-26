# -*- coding: utf-8 -*-
import click
import logging
import datetime
import numpy as np
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import find_dotenv, load_dotenv
import pandas as pd
import regex
import re  # for field identification
from utils.dataframe_manipulation import (
    replace_values,
    extract_values,
    split_on,
    write_out
)
from utils.abbreviation import multiple_mapper
from utils.field_indicator import (
    get_name_name1_descriptions_indices,
    indices_from_regex_search
)
from utils.etpl_field_names import (
    sql_etpl_field_names,
    sql_excel_field_map,
    labor_fields_to_internal,
    internal_fields_to_labor,
    labor_etpl_field_names
)
from utils.nongov import nongov

logger = logging.getLogger(__name__)

# For better or worse, from different data soruces,
# I called field names all kinds of things. This dictionary
# returns the canonical name so that we don't have to hard code
# things everywhere. The source name is assumed to be unique.
#
# This includes new field names
canonical_field_name = \
    {
        'NAME': 'name',
        'NAME_1': 'name_1',
        'mentioned_job_search_duration': 'mentioned_job_search_duration',
        'TrainRoute1': 'google_direction_url',
        'directions': 'google_direction_url',
        'street1': 'street1',
        'street2': 'street2',
        'city': 'city',
        'state': 'state',
        'zip': 'zip',
        'mention_hybrid': 'mention_hybrid',
        'mention_inperson': 'mention_inperson',
        'mention_remote': 'mention_remote',
        'statecomments': 'statecomments',
        'commented_suspended_program_status': 'commented_suspended_program_status',
        'nongovapproval': 'nongovapproval',
        'standardized_nongovapproval': 'standardized_nongovapproval'
    }

get_standardized = \
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
        file_extension = from_filepath.rsplit('.', 1)[1]

        if file_extension in ('xls', 'xlsx'):
            df = pd.read_excel(from_filepath)
        if file_extension in ('csv'):
            df = pd.read_csv(from_filepath, dtype=str)

        # We ignore case by lowercasing all column names (e.g. labor gives
        # different casing than sql, etc)
        df.columns = map(str.lower, df.columns)

        if debug_sample:
            # Cheap way to run over a very small subset, inspect output
            df = df.sample(debug_sample)

    # Ensure cipcode is exactly 6 digits by prepending zeros to shorter values
    if 'cipcode' in df.columns:
        df['cipcode'] = df['cipcode'].str.zfill(6)

    if remap_field_names:
        the_map = None
        if source == "sql":
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
            df = \
                df.rename(
                    columns=the_map
                )

    return df


def parenthesis_related(from_df, the_field):
    to_df = from_df.copy()
    field = canonical_field_name.get(the_field, the_field)
    standardized_field = get_standardized.get(field, field)

    # Debugging: Check if the column exists in the DataFrame
    if field not in to_df.columns:
        print(f"Field '{field}' not found in DataFrame columns")
        return to_df

    # Debugging: Print the head of the original DataFrame and the specific column
    print(f"Original DataFrame head for field '{field}':")
    print(to_df[[field]].head())

    # Ensure split_on returns a single column
    result = split_on(to_df[field], " - ", n=1, get_nth_result=1)
    print(f"Result from split_on for field '{field}':")
    print(result.head())
    print(f"Result type: {type(result)}")

    if isinstance(result, pd.DataFrame):
        if result.empty:
            print(f"Result DataFrame for field '{field}' is empty")
            to_df[standardized_field] = ""
        else:
            print(f"DataFrame detected, shape: {result.shape}")
            result = result.iloc[:, 0]
            print(f"Result after selecting first column: {result.head()}")

    to_df[standardized_field] = result

    # Handle content immediately prior to a hyphen
    regex_pattern = r'''
                    ^                   # start from beginning
                    (.+?                # capture everything non-greedily ...
                        (?:(?!-\s)      # ... except for the '- ', if it's there
                            .)          # and continue to match any character
                    *)                  # ... as many times as we can
                    '''
    to_df[standardized_field] = extract_values(to_df[standardized_field], regex_pattern)

    # Handle odd fixed patterns
    if not to_df[standardized_field].empty:
        to_df[standardized_field] = replace_values(to_df[standardized_field], r"\(orange\)")
    to_df[standardized_field] = replace_values(to_df[standardized_field], "closed")

    return to_df


def structured_parenthesis_related(from_df, the_field):
    to_df = from_df
    field = canonical_field_name.get(the_field, the_field)
    standardized_field = get_standardized.get(field, field)

    # Ensure standardized_field exists in to_df
    if standardized_field not in to_df:
        to_df[standardized_field] = ""

    # Silver Version of Provider Names
    #
    # We first extract provider names from different locations
    # depending on whether the `field` starts, ends or internally
    # has a parenthesis.
    #
    # Note that we access the regex <the_name> group from the result

    # If provider field starts with a (...
    open_parenthesis_index = to_df[field].str[0] == '('
    open_parenthesis_regex = r'''
                    (?P<paren>\(.*\)) # get the first parenthesis
                    (?P<the_name>.*)  # then get the actual name
                    '''
    to_df.loc[open_parenthesis_index, standardized_field] = \
        extract_values(
            to_df.loc[open_parenthesis_index, field],
            open_parenthesis_regex).the_name

    # If provider field ends with a )...
    # note that we operate on `standardized_field` from this
    # point forward
    close_parenthesis_index = to_df[field].str[-1] == ')'
    closing_parenthesis_regex = r'''
                    (?P<the_name>.*)  # get the actual name
                    (?P<paren>\(.*\)) # get the last parenthesis                
                    '''
    to_df.loc[close_parenthesis_index, standardized_field] = \
        extract_values(
            to_df.loc[close_parenthesis_index, standardized_field],
            closing_parenthesis_regex).the_name

    # For those fields remaining, if a ( or ) exists ....
    internal_parenthesis_index = \
        to_df[standardized_field].str.contains(r'\(|\)', regex=True) & \
        ~(close_parenthesis_index | open_parenthesis_index)

    to_df.loc[internal_parenthesis_index, standardized_field] = \
        extract_values(
            to_df.loc[internal_parenthesis_index, standardized_field],
            closing_parenthesis_regex).the_name

    # Finally, copy everything else that has no parentheses
    no_parenthesis_index = ~(close_parenthesis_index | \
                             open_parenthesis_index | \
                             internal_parenthesis_index)
    to_df.loc[no_parenthesis_index, standardized_field] = \
        to_df.loc[no_parenthesis_index, field]

    # ... now we remove degree related mentions that are left over
    degree_cert_variants = \
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

    # Check if the column is empty before attempting to replace
    if not to_df[standardized_field].empty:
        to_df[standardized_field] = to_df[standardized_field].replace(degree_cert_variants, "", regex=True)

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

    the_fields = ['description',
                  'featuresdescription']
    for a_field in the_fields:
        # get the standardized field if it exists, else returns same field
        # so we can self-modify it
        standardized_field = get_standardized.get(a_field, a_field)
        to_df[standardized_field] = \
            to_df[a_field].dropna().map(multiple_mapper)
    end = datetime.datetime.now()

    logger.info(f"\t[abbreviation] stopped at {end}")
    logger.info(f"\t[abbreviation] took {(end - start)} time")
    return to_df


def mentions_wioa(from_df):
    to_df = from_df

    wioa_like = \
        regex.compile(
            r'''
            (title\s+[IV1234]+\b\s*?)           # WOIA has 4 titles of funding in law, at end of sentence or space
            |(wioa){d<=1}                       # is called WOIA, WIA, allowed to miss a letter
            ''',
            flags=regex.I | regex.VERBOSE)

    wioa_indices = \
        get_name_name1_descriptions_indices(wioa_like, to_df)

    field = get_standardized['is_wioa']
    to_df[field] = False
    to_df.loc[wioa_indices, field] = True

    return to_df


def mentions_certificate(from_df):
    to_df = from_df
    cert_like = \
        regex.compile(
            r'''
            (certification)
            |(certificate)
            |[\s\b](cert)[\s\b]
            ''',
            flags=regex.I | regex.VERBOSE)
    cert_indices = \
        get_name_name1_descriptions_indices(cert_like, to_df)

    to_df['mentioned_certificate'] = False
    to_df.loc[cert_indices, 'mentioned_certificate'] = True

    return to_df


def mentions_associates(from_df):
    to_df = from_df
    as_like = \
        regex.compile(
            r'''
            [\b\s](A\.A\.S\.)[\b\s]
            |[\b\s](A\.S\.)[\b\s]
            |[\b\s](AS\sDe)                   # AS Degree
            |[\b\s](AS\sSc)                   # AS Science
            |[\b\s](AAS)[\b\s]                # applied associates of science
            ''',
            flags=regex.VERBOSE)
    assoc_indices = \
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
    training_context_regex = \
        r'''
        ((\w+\W+){0,8}        # first 8 or so words before
        (?P<job_search>job[\s\b.].*?search|assist[\w\s\b\.].*?employ\w*?\b) # help w/ job search
        (\W+\w+){0,8})       # and last 8 or so word after
        '''

    # ... then we search for specific mentions of numerically qualified durations,
    # like four months. We take these as job search durations. Note there aren't
    # very many of them.
    numbers = "one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen"
    durations = "minute|day|week|month|year"
    duration_regex = \
        f"""
        (?P<numeric>\d|{numbers})       # numeric reference ...
        (?P<modifer>.*)                 # followed by content that might modify ...
        (?P<base_duration>{durations})     # ... the base duration
        """

    # todo: make this logic have fewer hardcoded things
    job_search_length_mention = \
        to_df.loc[wioa_indices, 'description'] \
            .str \
            .extractall(pat=training_context_regex, flags=re.I | re.VERBOSE)[0]

    field = canonical_field_name['mentioned_job_search_duration']
    to_df[field] = None
    job_search_length_mention = \
        job_search_length_mention.str.extract(
            duration_regex,
            flags=re.I | re.VERBOSE
        ).replace('-', '') \
            .replace('week', 'weeks') \
            .dropna()

    if not job_search_length_mention.empty:
        job_search_length_mention = \
            job_search_length_mention.droplevel('match')  # drop uneeded multi-index

        to_df.loc[job_search_length_mention.index,
        field] = \
            job_search_length_mention['numeric'] + \
            job_search_length_mention['modifer'] + \
            job_search_length_mention['base_duration']

    return to_df


def google_direction_url(from_df):
    def clean_up(df, column):
        ret = df[column].str.replace(
            "\"", ""
        ) + "+"

        ret = \
            ret.apply(
                lambda url: quote_plus(url) + '+' if isinstance(url, str) else ''
            )

        return ret

    to_df = from_df
    direction_field = canonical_field_name['directions']

    base_url = "https://www.google.pl/maps/dir//"

    name_field_to_use = 'name_1'
    if get_standardized['name_1'] in from_df:
        name_field_to_use = get_standardized['name_1']

    to_df[direction_field] = \
        base_url + \
        clean_up(to_df, name_field_to_use) + \
        clean_up(to_df, canonical_field_name['city']) + \
        clean_up(to_df, canonical_field_name['state']) + \
        to_df['zip'].astype(str)

    # clear out nan
    nan_index = \
        to_df[direction_field].str.contains('//nan', regex=False)
    to_df.loc[nan_index, direction_field] = ''

    return to_df


def instruction_type(from_df):
    to_df = from_df

    """    
        'mention_hybrid':'mention_hybrid',
        'mention_inperson': 'mention_inperson',
        'mention_remote': 'mention_remote'
    """
    # Note: could make DRYer
    hybrid_like = \
        regex.compile(
            r'''
            (hybrid){s<=1}            # is called hybrid, hybrd, hybird, etc.
            ''',
            flags=regex.I | regex.VERBOSE)

    logger.info('\t[instruction type] mentions of hybrid')
    hybrid_indices = \
        get_name_name1_descriptions_indices(hybrid_like, to_df)

    field = canonical_field_name['mention_hybrid']
    to_df[field] = False
    to_df.loc[hybrid_indices, field] = True

    inperson_like = \
        regex.compile(
            r'''
            \W(in person){s<=1}            # is called in person, in-person in free text
            |(in person\)){s<=1}
            |(\(in person){s<=1}
            ''',
            flags=regex.I | regex.VERBOSE)

    logger.info('\t[instruction type] mentions of inperson')
    inperson_indices = \
        get_name_name1_descriptions_indices(inperson_like, to_df)

    field = canonical_field_name['mention_inperson']
    to_df[field] = False
    to_df.loc[inperson_indices, field] = True

    remote_like = \
        regex.compile(
            r'''
            \b(remote){s<=1}            # is called out as remote
            |(online\))
            |(\(online)            
            |(offered online){s<=1}            # is offered online
            ''',
            flags=regex.I | regex.VERBOSE)

    logger.info('\t[instruction type] mentions of remote')
    remote_indices = \
        get_name_name1_descriptions_indices(remote_like, to_df)

    field = canonical_field_name['mention_remote']
    to_df[field] = False
    to_df.loc[remote_indices, field] = True

    return to_df


def provider_course_status(from_df):
    to_df = from_df.copy()
    field = canonical_field_name['statecomments']

    most_recent_entry = to_df[field].dropna().str.split('\n').str[0]

    # some entries, unfortunately, are separated by commas instead
    has_comma = most_recent_entry.str.contains(',')
    most_recent_entry[has_comma] = most_recent_entry[has_comma].str.split(',').str[0]

    suspend_like = re.compile(
        r'''
        \W(to suspended)
        |\W(not seeking)
        |\W(must submit)
        |\W(suspended per)
        |\W(expir)
        |\W(not.*approved)
        ''',
        flags=regex.I | regex.VERBOSE)

    suspend_indices = indices_from_regex_search(most_recent_entry, suspend_like)

    status_field = canonical_field_name['commented_suspended_program_status']
    to_df[status_field] = False
    to_df.loc[suspend_indices, status_field] = True

    return to_df


def standardized_nongovapproval(from_df):
    to_df = from_df
    field = canonical_field_name['nongovapproval']
    standardized_field = canonical_field_name['standardized_nongovapproval']

    """
    The number of approved items is medium-ish, about 300 that I see,

    innovateNJ commented at one point that there were only 27 or so of them,
    if I recall correctly, so I'm not sure why there are so many more.
    If the number should be reduced the utils/nongov.py file dictionary
    can be consolidated itself by grouping content under a common key w/o
    having to change this file.
    """

    to_df[standardized_field] = ''

    approvals = nongov

    has_approvals = \
        to_df[field].dropna()

    for key, items in nongov.items():
        instances_of_approvals = f"({key}\\b)"
        if len(items) == 1:
            # we can't use list concat, instead
            # we directly construct
            the_item = list(items)[0]
            instances_of_approvals += \
                r'|\b(' + f"{the_item}" + r')\b'

        if len(items) > 1:  # else 2 or more
            instances_of_approvals += \
                '|(' + \
                '\\b)|('.join(list(items)) + \
                ')'

        approval_like = \
            regex.compile(instances_of_approvals,
                          flags=regex.I | regex.VERBOSE)

        approval_indices = \
            indices_from_regex_search(has_approvals, approval_like)

        # we construct an in place of standardized names in
        # the return dataframe
        if len(approval_indices) > 0:
            to_df.loc[approval_indices, standardized_field] += ',' + key

    return to_df


@click.command()
@click.argument('remap_field_names', default=True)
@click.argument('output_filepath', type=click.Path(), default="./D4AD_Standardization/data/interim/")
@click.argument('from_filepath', type=click.Path(exists=True),
                default="./D4AD_Standardization/data/raw/sql_header_etpl_all_programsJune3.xls")
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
    out_df = \
        parenthesis_related(from_df=from_df, the_field='NAME')
    out_df = \
        structured_parenthesis_related(from_df=out_df, the_field='standardized_name')

    logger.info('... standardizing provider names')
    out_df = \
        parenthesis_related(from_df=out_df, the_field='NAME_1')
    out_df = \
        structured_parenthesis_related(from_df=out_df, the_field='standardized_name_1')
    logger.info('... standardizing abbreviations throughout ... will take a while ...')
    out_df = \
        handle_abbreviations(from_df=out_df)

    logger.info('... identifying WIOA funded courses')
    out_df = \
        mentions_wioa(from_df=out_df)

    logger.info('... identifying certficate courses')
    out_df = \
        mentions_certificate(from_df=out_df)

    logger.info('... identifying associates')
    out_df = \
        mentions_associates(from_df=out_df)

    logger.info('... job search durations')
    out_df = \
        job_search_duration(from_df=out_df)

    logger.info('... google direction link from listed address')
    out_df = \
        google_direction_url(from_df=out_df)

    logger.info('... identifying mentions of instruction type (remote, in-person, hybrid)')
    out_df = \
        instruction_type(from_df=out_df)

    logger.info('... identifying program statuses (from statecomments)')
    out_df = \
        provider_course_status(from_df=out_df)

    logger.info('... standardizing non-gov approvals (from dict in utils/nongov.py)')
    out_df = \
        standardized_nongovapproval(from_df=out_df)

    content_is = 'standardized_etpl'
    logger.info(f"Done. Writing {content_is} to {output_filepath}. Remap fields names is {remap_field_names}")

    write_out(out_df, output_filepath, content_is='standardized_etpl', remap_field_names=remap_field_names,
              remapper=internal_fields_to_labor)


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
