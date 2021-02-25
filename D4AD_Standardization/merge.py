# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 13:59:05 2021

@author: prite
"""

import pandas as pd


def input_source(*args):
    df = {}
    for i in range(len(args[0])):
        df["df{0}".format(i)] = args[0][i]
    for j in df:
        if df[j].rsplit('.', 1)[1] == 'csv':
            df[j] = pd.read_csv(df[j])
        elif df[j].rsplit('.', 1)[1] in ('xls', 'xlsx'):
            df[j] = pd.read_excel(df[j])

    # print(df['df0'])
    return df


def mergedf(leftdf, rightdf, jointype, leftcol, rightcol):
    df = pd.merge(left=leftdf, right=rightdf, how=jointype, left_on=leftcol, right_on=rightcol)
    # drop all columns except NAME column
    rightdf = rightdf.loc[:, rightdf.columns != 'NAME']
    drop_list = rightdf.columns.values.tolist()
    df.drop(drop_list, axis=1, inplace=True)
    add_column = df.pop('NAME')
    return df, add_column


def export(df):
    df.to_csv('programs_20210222.csv', index=False)


def main():
    from_filepath = "C:\Pritesh\Rutgers_DOL\Project\ETPL\d4ad_etplneeds\programs_20210209.csv"
    input_file1 = "C:\Pritesh\Rutgers_DOL\Project\ETPL\d4ad_etplneeds\TBLDEGREELU_DATA_TABLE.xlsx"
    input_file2 = "C:\Pritesh\Rutgers_DOL\Project\ETPL\d4ad_etplneeds\TBLINDUSTRYCREDENTIAL_DATA_TABLE.xlsx"
    input_file3 = "C:\Pritesh\Rutgers_DOL\Project\ETPL\d4ad_etplneeds\TBLLICENSE_DATA_TABLE.xlsx"

    # create dataframes equivalent to number of files.
    files_list = [from_filepath, input_file1, input_file2, input_file3]
    mydf = input_source(files_list)
    maindf = mydf['df0']
    df1, df2, df3 = mydf['df1'], mydf['df2'], mydf['df3']

    # merge degree
    leftcolslist = maindf.columns.values.tolist()
    rightcolslist = df1.columns.values.tolist()
    maindf, maindfcol = mergedf(maindf, df1, 'left', leftcolslist[15], rightcolslist[0])
    maindf.insert(16, 'NAME', maindfcol)
    maindf.rename(columns={maindf.columns[16]: "DEGREEAWARDEDNAME"}, inplace=True)

    # merge industry credential
    leftcolslist = maindf.columns.values.tolist()
    rightcolslist = df2.columns.values.tolist()
    maindf, maindfcol = mergedf(maindf, df2, 'left', leftcolslist[20], rightcolslist[0])
    maindf.insert(21, 'NAME', maindfcol)
    maindf.rename(columns={maindf.columns[21]: "INDUSTRYCREDENTIALNAME"}, inplace=True)

    # merge license
    leftcolslist = maindf.columns.values.tolist()
    rightcolslist = df3.columns.values.tolist()
    maindf, maindfcol = mergedf(maindf, df3, 'left', leftcolslist[18], rightcolslist[0])
    maindf.insert(19, 'NAME', maindfcol)
    maindf.rename(columns={maindf.columns[19]: "LICENSEAWARDEDNAME"}, inplace=True)

    # export to csv
    export(maindf)


if __name__ == '__main__':
    main()
