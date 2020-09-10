# d4ad-standardization
Data 4 American Dream (D4AD) standardization code for innovateNJ contract. See: https://d4ad.com/ for more details.

## Instructions for Standalone Production Standardized data
These instructions iteratively produce standardized version of D4AD provider data. First the environment must be set up (e.g. python environment, with libraries) and then a series of notebooks run. @kwame is currently refactoring the notebooks into a single source file that pulls in a set of modules so that this process is much simpler. But currently this is the procedure for running (note: only been tested on Kwame's machine, some revisions may be needed):

## Setup/Assumptions
* This project is cloned, e.g. `git clone https://github.com/robinsonkwame/d4ad_standardization/`
* A current excel spreadsheet of D4AD provider data, with unstandardized columns of data, is copied to `.D4AD_Standardization/data/raw`, e.g. `etpl_all_programsJune3.xls`
* The `pipenv` package is available and how to install it [can be found here](https://docs.pipenv.org/)

## How to Run
```
# at ./d4ad_standardization
pipenv shell
pipenv install # wait a while for various packages to be installed

# This `jupyter nbconvert ...` is a crude way to convert the notebook to a python script and then run it
# These scripts build off prior script outputs (found in ./data/interim) and must be run in order

# Generate a list of prerequisites, used to bootstrap abbreviation candidates, not needed
#jupyter nbconvert --to notebook --ExecutePreprocessor.timeout=-1 --execute ./D4AD_Standardization/notebooks/2.0-kpr-Abbreviations-DisqualifiedProviders-Content-Generation.ipynb

# Generate first standardization of the NAME field
jupyter nbconvert --to notebook --ExecutePreprocessor.timeout=-1 --execute ./D4AD_Standardization/notebooks/3.0-kpr-NAME.ipynb

# Generate first standardization of the NAME_1 (Program name) field, further standardization of the NAME field
jupyter nbconvert --to notebook --ExecutePreprocessor.timeout=-1 --execute ./D4AD_Standardization/notebooks/5.0-kpr-Progam_Course_NAME.ipynb

# Generate first standardization of description fields, IS_WIOA field
# note: this will take at least 3 minutes
jupyter nbconvert --to notebook --ExecutePreprocessor.timeout=-1 --execute ./D4AD_Standardization/notebooks/6.0-kpr-Description-with_Funding_type_degree_type_columns.ipynb

# Generate job search duration related fields 
jupyter nbconvert --to notebook --ExecutePreprocessor.timeout=-1 --execute ./D4AD_Standardization/notebooks/7.0-kpr-WIOA-field.ipynb
```

## Generated Datasets
The above commands should incremental generate the following .csv files
```
 42M Sep 10 12:11 with_job_search_durations.csv                           # 7.0 notebook
 42M Sep 10 12:08 standardized_descriptions_and_degree_funding_type.csv   # 6.0 notebook
 31M Sep 10 11:28 standardized_name_and_name1.csv                         # 5.0 notebook
 30M Sep 10 11:21 standardized_name.csv                                   # 3.0 notebook
5.7M Sep 10 11:16 state_comments.csv                                      # 2.0 notebook
 20M Sep 10 11:16 0_prereqs.csv                                           # 2.0 notebook
```

There are also `.xls` files in ./data/processed.

## TODOS
While this work does standardized the columns of the ETPL data there are a few things that need to happen to make more streamlined:

* A single python file created, move all utility and functions to a util.py file that is imported
* The incremental build up of datasets should include *all* unstandardized column so that proper joins can be made on id fields
* Need to work hand in hand with Anne and Aisha to assist with how this can be integrated into a SQL based solution; note that my contract was around standardization itself so I initially assumed generating a .csv file was okay as output and providing the general Python scripts was sufficient.
