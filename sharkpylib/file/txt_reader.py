# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 10:23:06 2018

@author: a002028
"""
#import numpy as np
import pandas as pd


def load_txt_df(file_path='',
                seperator='\t',
                encoding='cp1252',
                # encoding='utf-8',
                # encoding='ISO-8859-1',
                encoding_list=['cp1252','utf-8','ISO-8859-1'],
                fill_nan='',
                header_row=0,
                as_dtype=str,
                as_dict=False,
                loading_info=''):
    """
    :param file_path: str
    :param seperator: str
    :param encoding: str
    :param fill_nan: str | np.nan
    :param header_row: int
    :param as_dtype: str | np.float | int
    :param as_dict: False | True
    :param loading_info: NotImplementedError
    :return: pd.DataFrame | Dictionary
    """
    print('Loading text file: '+file_path.split('/')[-1])
    if as_dtype:
        with open(file_path, 'r') as f:
            # is .strip('\r') necessary?
            header = f.readline().strip('\n').strip('\r').split(seperator)

        df = pd.read_csv(file_path,
                         sep=seperator,
                         encoding=encoding,
                         dtype={key: str for key in header},
                         engine='python').fillna(fill_nan)
    else:
        df = pd.read_csv(file_path, 
                         sep=seperator,
                         encoding=encoding,
                         header=header_row,
                         engine='python').fillna(fill_nan)
    if as_dict:
        df = df.fillna(fill_nan)
        return {key: df[key].values for key in df.keys()}
    else:
        return df
        

"""
#==============================================================================
#==============================================================================
"""


#class TXTreader(object):
#    """ """
#    def __init__(self):
#        
#        super(TXTreader, self).__init__()
#        
#    #==========================================================================
#    def load_txt(self, as_dataframe=True, as_dict=False):
#        """ """
        
        
    #==========================================================================