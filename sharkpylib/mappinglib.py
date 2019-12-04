# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on Thu Aug 30 15:53:08 2018

@author: a001985
"""
import os
import datetime

try:
    import pandas as pd
    import numpy as np
except:
    pass

from . import file_io
from . import exceptionlib
from sharkpylib.file import txt_reader
from . import utils
from .file.file_handlers import Directory, ListDirectory
from .file.files import MappingFile, SynonymFile


class old_Directory(object):
    """
    Handles a directory.
    """

    def __init__(self, directory=None):
        assert directory

        self._list_files()

    def _list_files(self):
        """
        Lists file in directory. Mapping files must contain string "mapping"
        :return:
        """
        self.mapping_objects = {}
        self.mapping_paths = {}
        for file_name in os.listdir(self.directory):
            if self.files_id not in file_name:
                continue
            file_id = file_name.split('.')[0]
            self.mapping_paths[file_id] = os.path.join(self.directory, file_name)

    def _check_valid(self, file_id):
        if file_id not in self.mapping_paths:
            raise AttributeError('File ID {} does not match any valid mapping files'.format(file_id))

    def _check_loaded(self, file_id, **kwargs):
        self._check_valid(file_id)
        if file_id not in self.mapping_objects:
            self.load_file(file_id, **kwargs)

    def load_file(self, *args, **kwargs):
        """
        Overwritten in sub classes.
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def get_file_list(self):
        return sorted(self.mapping_paths)

    def get_file_path(self, file_name):
        file_path = self.mapping_paths.get(file_name, None)
        if not file_path:
            raise exceptionlib.MissingMappingFile('Cant find file: {}'.format(file_name))
        return file_path

    def get_mapping_object(self, file_id, **kwargs):
        self._check_loaded(file_id, **kwargs)
        return self.mapping_objects.get(file_id)

    def get(self, item=None, file_id=None, from_col=None, to_col=None):
        mapping_object = self.get_mapping_object(file_id)
        return mapping_object.get(item, from_col=from_col, to_col=to_col)


class MappingDirectory(Directory):
    """
    Handles a directory with mapping files.
    """

    def __init__(self, directory=None):
        self.directory = directory
        if directory is None:
            self.directory = os.path.join(os.path.dirname(__file__), 'mapping_files')
        self.files_id = 'mapping'
        Directory.__init__(self, self.directory)

    def load_file(self, file_id, **kwargs):
        self._check_valid(file_id)
        self.mapping_objects[file_id] = MappingFile(file_path=self.mapping_paths.get(file_id), **kwargs)


class SynonymDirectory(Directory):
    """
    Handles a directory with synonym mapping files.
    """

    def __init__(self, directory=None):
        self.files_id = 'synonym'
        Directory.__init__(self, directory)

    def load_file(self, file_id, **kwargs):
        self._check_valid(file_id)
        self.mapping_objects[file_id] = SynonymFile(file_path=self.mapping_paths.get(file_id), **kwargs)


class MapAndFilterPandasDataframe(object):
    def __init__(self, df):
        """
        Class to map pandas dataframe. Class will hold information about what has been mapped.
        :param df:
        """
        self.df = df
        self.df_filtered = pd.DataFrame()

        self.original_columns = self.df.columns[:]
        self.mapped_columns = []
        self.filtered_columns = []
        self.filtered_columns_list = []

        self.mapping_object = None
        self.filter_object = None

    def set_mapping_file(self, file_path, from_col, to_col, **kwargs):
        """
        Set the file that you want to be used as mapping file. You need to specify from_col and to_col
        :param file_path: file path for mapping file
        :param kwargs: from column
        :return:
        """
        self.mapping_object = MappingFile(file_path, from_col=from_col, to_col=to_col, **kwargs)


    def set_filter_list_from_file(self, file_path, **kwargs):
        """
        Filter file is a "list" file extracted with "file_io.get_list_from_file"
        containing the column names that you want to include for the output file.
        :param file_path:
        :return:
        """
        self.filtered_columns_list = file_io.get_list_from_file(file_path, **kwargs)

    def set_filter_list_from_column_file(self, file_path, column_name, **kwargs):
        """
        Filter file is a column file extracted with "file_io.get_list_from_column_file"
        containing the column names that you want to include for the output file.
        :param file_path:
        :return:
        """
        self.filtered_columns_list = file_io.get_list_from_column_file(file_path, column_name, **kwargs)

    def map(self):
        self.mapped_columns = []
        if not self.mapping_object:
            raise exceptionlib.MissingInformation('No mapping file added!')
        for col in self.original_columns:
            self.mapped_columns.append(self.mapping_object.get(col))
        self.df.columns = self.mapped_columns[:]

    def filter(self):
        """
        Filters columns in the dataframe. Also sort according to list.
        :return:
        """
        self.filtered_columns = []
        for col in self.filtered_columns_list:
            if col in self.df.columns:
                self.filtered_columns.append(col)

        self.df_filtered = self.df[self.filtered_columns]


def to_decmin(pos):
    """
    Converts a position form decimal degree to decimal minute. 
    """
    pos = float(strip_position(pos))
    deg = np.floor(pos)
    dec_deg = pos-deg
    minute = 60 * dec_deg 
    
    deg_str = str(int(deg))
    minute_str = str(minute)
    if deg < 10: 
        deg_str = '0' + deg_str
    
    if minute < 10:
        minute_str = '0' + minute_str
    #print(minute)
    
    return deg_str + minute_str
    #print(new_lat)
    
    
def strip_position(pos):
    """
    Stripes position from +- and blankspaces. 
    """
    pos = str(pos)
    return pos.strip(' +-').replace(' ', '')
    

def split_date(date): 
    """
    Splits date from format %y%m%d to %y-%m-%d
    """
    
    date = str(date) 
    y = date[:4]
    m = date[4:6]
    d = date[6:]
    return '-'.join([y, m, d]) 



def datetime_from_odv(odv_time_string, apply_function=None): 
    """
    Converts an ODV time string to a datetime object. 
    The ODV time format is "yyyy-mm-ddThh:mm:ss.sss" or parts of it
    """
    parts = []
    T_parts = odv_time_string.split('T') 
    parts.extend(T_parts[0].split('-'))
    if len(T_parts) == 2: 
        time_parts = T_parts[1]. split(':')
        if len(time_parts) == 3 and '.' in time_parts[-1]: 
            time_parts = time_parts[:2] + time_parts[-1].split('.') 
        parts.extend(time_parts) 
    
    parts = [int(p) for p in parts]
    return datetime.datetime(*parts) 


def sdate_from_odv_time_string(odv_time_string): 
    return odv_time_string.split('T')[0]


def stime_from_odv_time_string(odv_time_string): 
    T_parts = odv_time_string.split('T') 
    if len(T_parts) == 2:
        return T_parts[1][:5]
    else:
        return ''
    

def sdate_from_datetime(datetime_object, format='%y-%m-%d'): 
    """
    Converts a datetime object to SDATE string. 
    """ 
    return datetime_object.strftime(format)


def stime_from_datetime(datetime_object, format='%H:%M'): 
    """
    Converts a datetime object to STIME string. 
    """ 
    return datetime_object.strftime(format)


def create_file_for_qc0(file_path=None, mapping_file_path=None, file_col=None, qc0_col=None, **kwargs):
    """
    Creates a file for QC0, file that can be run by IOCFTP.
    :param file_path: str
    :param mapping_file_path: str
    :param file_col: str, column name to convert from
    :param qc0_col: str, column name to convert to
    :return: pandas Dataframe or path is saved
    """

    mapping_object = MappingFile(file_path=mapping_file_path, from_col=file_col, to_col=qc0_col)
    print(mapping_object.file_path)
    print(mapping_object.df.columns)
    df = txt_reader.load_txt_df(file_path)

    # Map columns
    columns_to_keep = []
    all_cols = []
    qc_columns_to_add = []
    new_column_order = []
    for col in df.columns:
        if col == 'time':
            all_cols.append(col)
            continue
        mapped_col = mapping_object.get(col, missing_value=False)
        if mapped_col:
            columns_to_keep.append(mapped_col)
            qc_col = f'8{mapped_col}'
            qc_columns_to_add.append(qc_col)
            new_column_order.append(mapped_col)
            new_column_order.append(qc_col)
            all_cols.append(mapped_col)
        else:
            all_cols.append(col)

    # Change column names in df
    df.columns = all_cols

    # Keep mapped columns
    df = df[columns_to_keep]

    # Add qc columns
    for col in qc_columns_to_add:
        df[col] = '0'

    # Change order of columns
    df = df[new_column_order]

    # Save file
    if kwargs.get('save_file'):
        output_file_path = _get_qc0_file_path(file_path)
        df.to_csv(output_file_path, sep='\t', index=False)
        return output_file_path

    return df


def add_nodc_qc_columns_to_df(df=None, file_path=None, default_q='', default_qc0='0', default_qc1='0', **kwargs):
    """
    Adds the three QC columns that should be present in the SMHI nods standard format.
    :param df:
    :param columns:
    :param default_q:
    :param default_qc0:
    :param default_qc1:
    :return:
    """
    def q_col(par):
        if any([par.startswith(qc) for qc in ['Q_', 'QC0_', 'QC1']]):
            return True
        return False

    q = 'Q'
    qc0 = 'QC0'
    qc1 = 'QC1'

    if file_path:
        df = txt_reader.load_txt_df(file_path)

    columns = list(df.columns)

    # Find metadata columns
    metadata_columns = ListDirectory().get_file_object('list_metadata_columns.txt').get()
    data_columns = [col for col in columns if col not in metadata_columns]

    data_par_list = [par for par in data_columns if not q_col(par)]

    # Add qc columns
    new_columns = []
    for par in columns:
        if par in data_par_list:
            qpar = par.split('[')[0].strip()
            new_columns.append(par)
            new_columns.append(f'{q}_{qpar}')
            new_columns.append(f'{qc0}_{qpar}')
            new_columns.append(f'{qc1}_{qpar}')
        else:
            if par not in new_columns:
                new_columns.append(par)

    # Add columns to dataframe if missing
    for col in new_columns:
        if col not in columns:
            if col.startswith(qc0):
                df[col] = default_qc0
            elif col.startswith(qc1):
                df[col] = default_qc1
            elif col.startswith(q):
                df[col] = default_q

    # Change columns order
    df = df[new_columns]

    if kwargs.get('save_file'):
        if file_path:
            # info = utils.PathInfo(file_path)
            # output_file_path = os.path.join(info.directory, f'{info.file_base}_with_nodc_qc_cols.{info.extension}')
            # df.to_csv(output_file_path, sep='\t', index=False)
            df.to_csv(file_path, sep='\t', index=False)
            return file_path
        return df
    return df


def merge_data_from_qc0(main_file_path=None, mapping_file_path=None, file_col=None, qc0_col=None, **kwargs):
    qc0_file_path = _get_qc0_file_path(main_file_path)

    if not os.path.exists(main_file_path):
        raise FileNotFoundError(main_file_path)

    if not os.path.exists(qc0_file_path):
        raise FileNotFoundError(qc0_file_path)

    main_df = txt_reader.load_txt_df(main_file_path)
    qc0_df = txt_reader.load_txt_df(qc0_file_path)
    mapping_object = MappingFile(file_path=mapping_file_path, from_col=qc0_col, to_col=file_col)

    for col in qc0_df.columns:
        # Only check qc columns
        if not (len(col) == 5 and col[0] == '8'):
            continue
        par = col[1:]
        print('par:', par)
        mapped_par = mapping_object.get(par, missing_value=False)
        qc0_mapped_par = f'QC0_{mapped_par}'
        if not mapping_object:
            raise ValueError(f'Could not find mapping for column: {col}')
        if qc0_mapped_par in main_df:
            print(qc0_mapped_par, par)
            main_df[qc0_mapped_par] = qc0_df[col]

    # Save file
    if kwargs.get('save_file'):
        # info = utils.PathInfo(main_file_path)
        # output_file_path = os.path.join(info.directory, f'{info.file_base}_with_added_qc0.{info.extension}')
        # main_df.to_csv(output_file_path, sep='\t', index=False)
        main_df.to_csv(main_file_path, sep='\t', index=False)

    return main_df

def _get_qc0_file_path(file_path):
    """
    Builds a file path for qc0 and returns it.
    :param file_path:
    :return:
    """
    info = utils.PathInfo(file_path)
    qc_file_path = os.path.join(info.directory, f'qc0_{info.file_base}.{info.extension}')
    return qc_file_path
    