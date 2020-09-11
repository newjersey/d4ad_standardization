import regex

def indices_from_regex_search(the_series, the_regex):
    return the_series.dropna()\
                     .map(the_regex.search)\
                     .dropna().index

def get_name_name1_descriptions_indices(from_regex, from_df):
    name =\
        indices_from_regex_search(
            from_df['NAME'],
            from_regex
        )

    name_1 =\
        indices_from_regex_search(
            from_df['NAME_1'],
            from_regex
        )

    descriptions =\
        indices_from_regex_search(
            from_df['DESCRIPTION'],
            from_regex
        )

    features_description =\
        indices_from_regex_search(
            from_df['FEATURESDESCRIPTION'],
            from_regex
        )

    return name.union(name_1)\
               .union(descriptions)\
               .union(features_description)
