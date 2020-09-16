import regex

# Crude labor style naming, should be movded to a config file
# or pulled from a single point
canonical_field_name =\
    {
        'NAME': 'name',
        'NAME_1': 'name_1',
        'mentioned_job_search_duration': 'mentioned_job_search_duration',
        'DESCRIPTION': 'description',
        'FEATURESDESCRIPTION': 'featuresdescription'
    }

course_name = canonical_field_name['NAME']
provider_name = canonical_field_name['NAME_1']
description_field = canonical_field_name['DESCRIPTION']
features_description_field = canonical_field_name['FEATURESDESCRIPTION']

def indices_from_regex_search(the_series, the_regex):
    return the_series.dropna()\
                     .map(the_regex.search)\
                     .dropna().index

def get_name_name1_descriptions_indices(from_regex, from_df):
    name =\
        indices_from_regex_search(
            from_df[course_name],
            from_regex
        )

    name_1 =\
        indices_from_regex_search(
            from_df[provider_name],
            from_regex
        )

    descriptions =\
        indices_from_regex_search(
            from_df[description_field],
            from_regex
        )

    features_description =\
        indices_from_regex_search(
            from_df[features_description_field],
            from_regex
        )

    return name.union(name_1)\
               .union(descriptions)\
               .union(features_description)
