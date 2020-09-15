import regex

# DEFINE COLUMNS
provider_name_field = 'name'
program_name_field = 'officialname'
description_field = 'description'
feature_description_field = 'featuresdescription'
is_wioa_field = 'wiaeligible'


def indices_from_regex_search(the_series, the_regex):
    return the_series.dropna()\
                     .map(the_regex.search)\
                     .dropna().index

def get_name_name1_descriptions_indices(from_regex, from_df):
    name =\
        indices_from_regex_search(
            from_df[program_name_field],
            from_regex
        )

    name_1 =\
        indices_from_regex_search(
            from_df[provider_name_field],
            from_regex
        )

    descriptions =\
        indices_from_regex_search(
            from_df[description_field],
            from_regex
        )

    features_description =\
        indices_from_regex_search(
            from_df[feature_description_field],
            from_regex
        )

    return name.union(name_1)\
               .union(descriptions)\
               .union(features_description)
