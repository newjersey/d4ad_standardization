# unstructed back up code, not sure where to place since 
#   the notebook(s) was refactored to not reconstruct and
# instead pull from known local file

#  ------
# this code was never used, pulls in a .sql file directlying using regexs

# Here we ingest Career One Stop certifications
#   I was goign to use this to de-acroymn-ize mentions but now am unsure
# if this is critical. It also may introduce errors, e.g. AES mapping to
# the "wrong acroymn"

# Here we read in a .sql directly as text and parse out the data.
# I do this to avoid the need for a database, db drivers, etc. 
# That said, this represented some investment in constructing the right regexs
if not SKIP_THIS:
    path = rootpath + externalpath + 'career_one_stop/'
    credential_sql = 'TEST-2-CERTIFICATIONS.sql' # '2-CERTIFICATIONS.sql'

    with open(path + credential_sql) as sql:
        my_string = sql.read()

    header_names =\
        (
            'CERT_ID', 'CERT_NAME', 'ORG_ID', 'TRAINING', 'EXPERIENCE', 
            'EITHER', 'EXAM', 'RENEWAL', 'CEU', 'REEXAM', 
            'CPD', 'CERT_ANY', 'URL', 'ACRONYM', 'NSSB_URL', 
            'CERT_URL', 'CERT_LAST_UPDATE', 'KEYWORD1', 'KEYWORD2', 'KEYWORD3', 
            'SUPPRESS', 'DATEADDED', 'COMMENTS', 'VERIFIED', 'UPDATEDBY', 
            'CERT_DESCRIPTION', 'DELETED', 'EXAM_DETAILS'
        )

    # Pandas assumes atomic python types when reading from records,
    # See: https://github.com/pandas-dev/pandas/issues/9381, so we need to use
    # Python types here
    dtypes =\
        np.dtype(
            "str, str, float, float,"
            "float, float, float, str,"
            "float, float, float, float,"
            "str, str, str, str,"
            "str, str, str, str,"
            "str, str, str, str," 
            "str, str, float, str"
        )

    flags = re.MULTILINE | re.DOTALL | re.VERBOSE
    the_fields_regex =\
        """
        (?P<values>Values\n\s+\()  # Start with the word Value <newline> (
            (?P<fields>.*?)        #    Grab all the field content
        (?P<end>\);)               # ... which stops at the terminating paren, ;
        """

    the_fields = re.compile(the_fields_regex, flags=flags)

    a_field_regex =\
        """
        '(?P<string>.*?)'[,)]           # get a quoted string ending at comma or paran or
        |(?P<date_time>TO_DATE\(.*?\))  # get the TO_DATE, parse out actual date later or
        |(?P<num>\d),                   # get numeric or
        |(?P<null>NULL)                 # get NULL
        """

    a_field = re.compile(a_field_regex, flags=flags)

    require_field_numbers = [1] # should be 13

    def yield_certification_records(sql_file=my_string, require_field_numbers=require_field_numbers):
        # do we skip those w/o certain fields, like acronymns
        temp_data = [0]*28
        for match in the_fields.finditer(sql_file):
            break_match = False

            for index, field in enumerate(a_field.finditer( match.group('fields') )):
                grp = None
                for grp, value in field.groupdict().items():
                    if value:
                        # then we transform the string value into the appropriate type, given the group name
                        if grp == 'date_time':
                            #  There is a difference between https://regex101.com/r/yphUXY/1/
                            # and what I see Python do here; if I don't capture the entire thing
                            # it gets re-raised as another potential match, even if I use ?:, etc.
                            value = value[9:28] # todo: convert to datetime
                        if grp == 'null':
                            value = None
                            if index in require_field_numbers:
                                break_match = True

                        if grp == 'num':
                            value = int(value)

                        temp_data[index] = value
                        break # only one possible match value
                if break_match: # and don't look at other fields
                    break

            if not break_match:
                yield tuple(value for value in temp_data)
            
            break_match = False

    certification_df =\
        pd.DataFrame.from_records(
            yield_certification_records(),
            columns=header_names)
    certification_df
print('done')





# --------
#  This code was used to construct a list of likely abbreviations that 
# when expanded incrementally improve Step 2 of 5.0-kpr-Program_Course_NAME.ipynb



# Here I identify two pretty common cases of acronymns and abbreviations:
#   All caps
#   Xx*. <- capitalized inital letter ending with a period

# Now let's attempt to extract presumed acronyms and see if we can
# directly label them. I assume there are far fewer unique abbreviations
# so that a person can actually do this in a short amount of time
abbreviation_pickle = rootpath + interimpath + 'abbreviation_label.pickle'

#if os.path.exists(abbreviation_pickle):
# if ../data doers nto exist
    flags = re.VERBOSE

    #  TODO: check if abbreviation labeled file already exists, if it does
    # we skip this portion

    # Pandas/Python doesn't like this verbose regex but likes other?
    # all_caps_regex = '''
    #                 \b(?P<all_caps>[A-Z]+)  # Get all caps words
    #                 [\s,:\d]                # sit before a space, comma or digit
    #                 '''
    all_caps_regex = r'\b(?P<all_caps>[A-Z]+)[\s,:\d]'

    dotted_word_regex = r'(?P<dot_abbreviation>[A-Z][a-z]+\.)'
    dotted_word_regex =\
        """
        (?P<dot_abbreviation>[a-zA-Z][a-z]+\.)
        """

    the_regexs = "|".join([all_caps_regex, dotted_word_regex])

    the_abbreviations =\
        the_df['STANDARDIZEDNAME_1'].str\
                                    .extractall(
                                        pat=the_regexs,
                                        flags=flags)
    print('constructed abbreviation list...')
    
print('done')

# Since we've run on the entire dataset we can now
# flatten the dataframe, de-duplicate and then directly label
if os.path.exists(abbreviation_pickle):
    len(the_abbreviations.all_caps.unique()) +\
        len(the_abbreviations.dot_abbreviation.unique()) # 1151

    # now we need to get the count of unique abbreviations so that we can
    # label in priority order. We also drop those abbreviations only occuring once
    # since they have a 1 / 26,660 chance of occuring (not worth our effort)

    # to properly label the all caps and abbreviations we need the 
    # context in which they occur. Since we're mapping to one definition
    # we assume only the first instance is really needed and label off of that
    abbreviations_to_label =\
        pd.concat(
            (the_abbreviations.drop_duplicates(
                subset=['all_caps'],
                keep='first')['all_caps'],
            the_abbreviations.drop_duplicates(
                subset=['dot_abbreviation'],
                keep='first')['dot_abbreviation']
            ),
            axis=0
        ).dropna()\
        .droplevel('match')\
        .reset_index() # so that index is a column

    abbreviations_to_label.rename(columns={'index':'the_df_index', 0:'abbreviation'}, inplace=True)
    print('created interim abbreviations data frame...')
print('done')

if os.path.exists(abbreviation_pickle) and not SKIP_THIS::
    # note here we read the main pickle file and assume 
    # those pickle files with random extensiosn were/are consolidated into this
    # the other pickle files are named to prevent overwriting ongoing work
    expanded_labels = pd.read_pickle(abbreviation_pickle)
    last_labeled_index = expanded_labels.index(None)
    former_labels = abbreviations_to_label.abbreviation[:last_labeled_index] #set(already_labeled[:last_labeled_index])

    unseen_abbreviations =\
        abbreviations_to_label.query('abbreviation not in @former_labels')
    unseen_abbreviations.abbreviation.value_counts()
    # note I'm seeing 1 across the board, both when using not in and in
    #   which suggests that we leave these be for now because their occurence
    # is so rare out of 26,660, although the bulk may be significant; better
    # to circle back though
    print('created mapping columns for former labels and their expansions...')



#  So now we manually label them and dump them here. If skipped, this data has
# been saved to data/external since it's raw and was created eternally
# through human decision making (e.g. what an abbreviation mapped to)
#
#  This is the procedure we follow
#       A) if a capitalized word is an entire word, leave it alone (no label)
#       B) provide a label for all dotted abbreviated words
if not SKIP_THIS:
    def display_func(row):
        # Note: We use globally available the_df to get context, bad form I know
        display(
            Markdown(
                "**Context:** " +  the_df.loc[ row.the_df_index ].NAME_1 \
            +   "\n\n" + row.abbreviation
            )
        )

    def preprocessor(x, y):
        # only take standardized column, leave everything else
        return x.abbreviation, y

    if os.path.exists(abbreviation_pickle) and not SKIP_THIS:
        labelling_widget = ClassLabeller(
            features=abbreviations_to_label,
            model=pipeline,
            model_preprocess=preprocessor,
            display_func=display_func,
            options=['No Label'],
            acquisition_function='entropy'
        )

        labelling_widget
        
print('done/skipped manual labelling')


#  Every now and then, with the labels in hand we simply output them (if a file doesn't already exist)
# so that we can save them incrementally. We should manually rename older files; this should
# be basically a 1 time process.

# Temp, save work locally so we don't loooooose it! 
if os.path.exists(abbreviation_pickle) and not SKIP_THIS:
    import random
    random_number = str(random.randint(0,255))
    pickle.dump(expanded_labels,
                open(abbreviation_pickle+random_number, 'wb'))
    print("done/don't forget to consolidate abbreviations")

    

# First, construct an abbreviation to its expansion  dictionary
label_mapper =\
    pd.DataFrame(
        {
            "abbreviation": \
abbreviations_to_label.abbreviation[:last_labeled_index].values,
            "expanded": expanded_labels[:last_labeled_index]
        }
    )
copy_over_index = (label_mapper.expanded == "No Label") | (label_mapper.expanded == "Submit.")
label_mapper.expanded[copy_over_index] =\
    label_mapper.abbreviation[copy_over_index]

# Add in one-off acronyms observed through labelling that need attention
# too do, make this json or a python file
one_off_mappings =(
    ['AAS', 'Associate of Applied Science'],
    ['ESL', 'English as a Second Language'],
    ['Bus.Soft.', 'Business Software'],
    ['App', 'Application'],
    ['App.', 'Application'],
    ['Dev.', 'Developer'],
    ['CDL', 'Commerical Driver\'s License'],
    ['win', 'Windows'],
    ['Win', 'Windows'],    
    ['Contg.', 'Continuing'],
    ['Ed.', 'Education'],
    ['Mgmt.', 'Management'],
    ['Mous', 'Microsoft Office User Specialist']
)

for mapping in one_off_mappings:
    label_mapper.loc[len(label_mapper)+1] = mapping

# tricsk to get the mapping set I want
all_caps = label_mapper.abbreviation.str.fullmatch(r'^([A-Z]{4,})$')
#label_mapper.drop(index=all_caps, inplace=True)

label_mapper['same'] =\
   label_mapper.abbreviation == label_mapper.expanded

write_me = label_mapper.drop(label_mapper.index[label_mapper.same])

write_me.to_csv(
    "../data/external/label_mapper.csv",
    columns= ['abbreviation', 'expanded'],
    index=False
)




# temp: so we can just run this cell on updated vers of label_mapper
label_mapper = pd.read_csv(
    "./../data/external/label_mapper.csv"
)

# Convert the label mapper into a dictionary so that we can
# use it as a look up table
rep_dict = {
    **dict(zip(label_mapper.abbreviation, label_mapper.expanded))
}

#pattern = re.compile("[\b\W]|".join([re.escape(k) for k in rep_dict.keys()]), re.M)
pattern = re.compile(
    "|".join([re.escape(k) for k in rep_dict.keys()]),
    re.M)

def my_lookup(x):
    if not rep_dict.get(x, False):
        return rep_dict.get(x[1:], False)

start_abbrev = re.compile(
    "^"+"|^".join([re.escape(k) for k in rep_dict.keys()]), re.M)
start_abbrev = re.compile(
    "^HVAC", re.M)

def multiple_replace(string):
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)

def multiple_replace2(string):
    return start_abbrev.sub(
        lambda x: my_lookup(x), string)

def term_grouped_regex(term="", right_regex="", left_regex=""):
    #return left_regex + '(' + re.escape(term) + ')' + right_regex
    mystr = left_regex + '(' +\
                f"?P<{term}>"   +\
                re.escape(term) +\
            ')' +\
            right_regex
    return mystr

def make_term_grouped_regex(term="", right_regex="", left_regex=""):
    mystr = left_regex + '(' +\
                re.escape(term) +\
            ')' + right_regex
    return mystr


def make_grouped_regexes(replace_dict, left_regex="", right_regex=""):
    return (make_term_grouped_regex(left_regex=left_regex,
                                    term=key,
                                    right_regex=right_regex)\
                                        for key in replace_dict.keys()
            )

# a_abbrev = re.compile(
#     "|".join([
#         make_term_grouped_regex(
#             left_regex="^",
#             term=k
#         ) for k in rep_dict.keys()]), re.M)
    # "|".join(
    #     make_grouped_regexes(rep_dict, left_regex="^")
    # ) +\


a_abbrev = re.compile(
    "|".join(
        make_grouped_regexes(rep_dict, left_regex=r'\s', right_regex=r'\s')
    )
)

draft_output = the_df.iloc[:100,:][['NAME_1']]
pd.set_option('display.max_rows', None)
# draft_output['MULTI_REPLACE_STANDARDIZEDNAME_1'] =\
#     draft_output['NAME_1'].map(multiple_replace3)
# draft_output[['MULTI_REPLACE_STANDARDIZEDNAME_1', 'NAME_1']]

the_content = re.compile(r'\b(?P<key>\w+)\b')

test_string = 'Straight Truck Driver - CDL B'
test_string = "Bus.Soft. App/Office Proc.Legal/"

def lookup_match(matchobj):
    #  The match corresponds to a key with regexs 
    # surrounding it. To properly replace it we
    # replace the key with its value in the whole matched
    # string
    the_original_string = matchobj.group(0)
    print('in lookup match')

    the_key = the_content.search(
        matchobj.group(0)
        ).group('key')

    the_value = rep_dict.get(the_key, None)
    if not the_value:
        # try the whole thing
        #print(rep_dict)
        #print(the_original_string.strip())
        the_value = rep_dict[the_original_string.strip()]
        # we then use the entire string
        print(the_key, "|", the_original_string)

    print(the_key, "|", the_original_string)
    #return the_original_string.replace(lookup_match, the_value)
    return the_original_string.replace(the_key, the_value)


def lookup_match(matchobj):
    #  The match corresponds to a key with regexs 
    # surrounding it. To properly replace it we
    # replace the key with its value inside of the whole matched
    # string.

    # This is overly complicated but we have a problem
    # of ambiguity in that the keys "Bus" and "Bus.Proc."
    # will both match to "Bus" if you strip out possible
    # left and right regexes; there is no way to know that
    # the periods in "Bus.Proc." don't indicate any character,
    # e.g. "BusXProcY"
    #
    # So what we do is use the beg-for-forgiveness paradigm
    # and first attempt to match to the large possible match ("Bus.Proc.")
    # and then match to the content found by a specialized regex only
    # if that fails
    the_original_string = matchobj.group(0)

    the_key = the_original_string.strip()
    final_word = rep_dict.get(
        the_key,
        None
    )

    if not final_word:
        shorter_key = the_content.search(
            the_original_string
            ).group('key')
        final_word = rep_dict[shorter_key]
        the_key = shorter_key

    return the_original_string.replace(the_key, final_word)


# See: https://stackoverflow.com/a/61952495/3662899
# So, we can have more than one match in a given string, so we 
# need to 

# Here we have a bank of regexs for very specific left, rgith situations
#   we could combine them for efficiency but it's easier to debug, examine
#   in a special case row by row bank
a_abbrev = re.compile(
    "|".join(   # match words at start of string
        make_grouped_regexes(rep_dict, left_regex=r'^', right_regex=r'\s')
    ) + "|" +\
    "|".join(   # match words surrounded by spaces
        make_grouped_regexes(rep_dict, left_regex=r'\s', right_regex=r'\s')
    ) + "|" +\
    "|".join(   # match words that make up entire fields, e.g. 'Nursing'
        make_grouped_regexes(rep_dict, left_regex=r'^', right_regex=r'$')
    ) + "|" +\
    "|".join(   # match words at end of string preceded by space or slash
        make_grouped_regexes(rep_dict, left_regex=r'[\s/]', right_regex=r'$')
    ) + "|" +\
    "|".join(   # match words within string that follow a slash, end with a space or slash
        make_grouped_regexes(rep_dict, left_regex=r'/', right_regex=r'[\s/]')
    )    
)

def multiple_replace(string):
    return a_abbrev.sub(lookup_match, string)

#re.sub(r'\s'+'(?P<CDL>CDL)'+r'\s' + '|' + "(?P<woot>ABC)", dashrepl, test_string)

#print(a_abbrev)
# test_string = "A+/N+/Mous"
# test_string = "/MOUS"
# test_string = "Mous"

# k = re.compile("MOUS|^Mous$")
# print( test_string in label_mapper.abbreviation)
# print( test_string in rep_dict, rep_dict[test_string])
# print("|"+label_mapper.abbreviation.iloc[-1]+'|')

# print(
#     k.sub("Microsoft Office User Something", test_string)
# )

#print(a_abbrev.pattern[100:])

# print(a_abbrev)
# k =multiple_replace(test_string)
# print(test_string)
# print(k)

draft_output['MULTI_REPLACE_STANDARDIZEDNAME_1'] =\
    draft_output['NAME_1'].map(multiple_replace)

# so, see: https://stackoverflow.com/a/61952495/3662899
# or we just run two times, again. Pretty simple, not scalable in the limit but whatever? in some sense it's probably about the same givne that we loop a constant
# number of times and I treat the scan and replace as O(1)

# Takes 15 seconds on my machine
draft_output['MULTI_REPLACE_STANDARDIZEDNAME_1'] =\
    draft_output['MULTI_REPLACE_STANDARDIZEDNAME_1'].map(multiple_replace)
draft_output['MULTI_REPLACE_STANDARDIZEDNAME_1'] =\
    draft_output['MULTI_REPLACE_STANDARDIZEDNAME_1'].map(multiple_replace)


draft_output[['MULTI_REPLACE_STANDARDIZEDNAME_1', 'NAME_1']]
#print('done')