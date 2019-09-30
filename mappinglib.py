# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on Thu Aug 30 15:53:08 2018

@author: a001985
"""
import os 
import pandas as pd 
import datetime
import numpy as np
import codecs
        
class Directory(object):
    """
    Handles a directory.
    """

    def __init__(self, directory=None):
        if directory:
            self.directory = directory
        else:
            self.directory = os.path.join(os.path.dirname(__file__), 'mapping_files')

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

    def get_available_files(self):
        return sorted(self.mapping_paths)

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
        self.files_id = 'mapping'
        Directory.__init__(self, directory)

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


class MappingFile(object):

    def __init__(self, file_path=None, from_col=None, to_col=None, **kwargs):

        kw = {'sep': '\t',
              'encoding': 'cp1252'}
        kw.update(kwargs)

        self.from_col = from_col
        self.to_col = to_col

        self.file_path = file_path
        if self.file_path and os.path.exists(self.file_path):
            self.df = pd.read_csv(file_path, **kw)
        else:
            self.df = pd.DataFrame()

    def get(self, item, from_col=None, to_col=None, missing_value=None, **kwargs):
        if not self.file_path:
            return item

        if not from_col:
            from_col = self.from_col
        if not to_col:
            to_col = self.to_col

        # Saving current columns
        self.from_col = from_col
        self.to_col = to_col

        result = self.df.loc[self.df[from_col] == item, to_col]
        if len(result):
            return str(result.values[0])
        else:
            if missing_value is not None:
                return missing_value
            else:
                return str(item)

    def get_mapped_list(self, item_list, **kwargs):
        """
        Maps a iterable
        :param item_list:
        :param kwargs: Se options in method get
        :return:
        """

        output_list = []
        for k, item in enumerate(item_list):
            mapped_item = self.get(item, **kwargs)
            output_list.append(mapped_item)
        return output_list


class SynonymFile(object):

    def __init__(self, file_path=None, **kwargs):
        self.data = {}
        self.file_path = file_path
        if self.file_path:
            with codecs.open(file_path) as fid:
                for line in fid:
                    line = line.strip()
                    if not line:
                        continue
                    split_line = line.split('\t')
                    if len(split_line) > 1:
                        items = [key.strip() for key in split_line[1].split(';')]
                        for key in items:
                            self.data[key] = split_line[0]
                            self.data[key.upper()] = split_line[0]
                            self.data[key.lower()] = split_line[0]

    def get(self, item, no_match_value=None):
        return self.data.get(item, no_match_value)

    def get_mapped_list(self,
                 item_list,
                 no_match_value=None,
                 col_nummer_if_no_match=False,
                 as_array=False):
        """
        Maps a iterable.
        :param item_list:
        :param no_match_value:
        :param col_nummer_if_no_match:
        :param kwargs:
        :return:
        """
        output_list = []
        for k, item in enumerate(item_list):
            if col_nummer_if_no_match:
                mapped_item = self.get(item, str(k+1))
            else:
                mapped_item = self.get(item, no_match_value)
            output_list.append(mapped_item)
        if as_array:
            output_list = np.array(output_list)

        return output_list
        
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
    
    
    
    
    
    
    
    
    
    