# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on Thu Aug 30 15:53:08 2018

@author: a001985
"""
import os 
import pandas as pd
import codecs
import datetime
import numpy as np

class Directory(object):
    """
    Handels a directory with synonym mapping files.
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
    Handels a directory with mapping files.
    """

    def __init__(self, directory=None):
        self.files_id = 'mapping'
        Directory.__init__(self, directory)

    def load_file(self, file_id, **kwargs):
        self._check_valid(file_id)
        self.mapping_objects[file_id] = MappingFile(file_path=self.mapping_paths.get(file_id), **kwargs)

class SynonymDirectory(Directory):
    """
    Handels a directory with synonym mapping files.
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

    def get(self, item, from_col=None, to_col=None):
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
            return result.values[0]
        else:
            return item


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
        :param item:
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


