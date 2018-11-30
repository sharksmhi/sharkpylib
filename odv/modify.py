# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
@author:
"""

import os
import codecs
import pandas as pd
import numpy as np
from . import odvfile


class ModifyODVfile_old(object):

    def __init__(self, file_path):
        if not os.path.exists(file_path):
            raise IOError
        self.file_path = file_path

    def convert_to_time_series(self, **kwargs):
        """
        Converts the file to a time series by adding the column "time_ISO8601" as first and primary variable
        //<subject>SDN:LOCAL:time_ISO8601</subject><object>SDN:P01::DTUT8601</object><units>SDN:P06::TISO</units>

        New file is save in sub directory "as_timeseries"

        :return:
        """

        primary_par = 'time_ISO8601'
        primary_semantic = '//<subject>SDN:LOCAL:time_ISO8601</subject><object>SDN:P01::DTUT8601</object><units>SDN:P06::TISO</units>\n'

        output_directory = os.path.join(os.path.dirname(self.file_path), 'as_timeseries')
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)
        output_file_path = os.path.join(output_directory, os.path.basename(self.file_path))

        semantic_added = False
        with codecs.open(output_file_path, 'w', encoding=kwargs.get('encoding_out', kwargs.get('encoding', 'utf8'))) as fid_out:
            with codecs.open(self.file_path, encoding=kwargs.get('encoding_in', kwargs.get('encoding', 'utf8'))) as fid_in:
                for line in fid_in:
                    if not line.strip():
                        continue
                    if line.startswith('//'):
                        if line.startswith('//<subject>'):
                            if not semantic_added:
                                fid_out.write(primary_semantic)
                                semantic_added = True
                        fid_out.write(line)
                    elif line.startswith('Cruise'):
                        split_line = line.split('\t')
                        header = split_line
                        new_header = []
                        for c, col in enumerate(header):
                            new_header.append(col)
                            if 'yyyy-mm-dd' in col:
                                time_col = c
                            elif 'bot' in col.lower() and 'depth' in col.lower():
                                primary_col = c+1
                                new_header.append(primary_par)
                        fid_out.write('\t'.join(new_header))
                    else:
                        split_line = line.split('\t')
                        new_split_line = []
                        for c, item in enumerate(split_line):
                            if c == primary_col:
                                new_split_line.append(split_line[time_col])
                            new_split_line.append(item)
                        fid_out.write('\t'.join(new_split_line))

    def remove_whitespace_in_parameters(self, **kwargs):
        """
        Created to remove whitespace in header and semantic header to ensure match. Example:
        '<  63_SIVUB_F2_NDT'
        '< 63_SIVUB_F2_NDT'

        :param kwargs:
        :return:
        """

        new_lines = []
        with codecs.open(self.file_path, encoding=kwargs.get('encoding_in', kwargs.get('encoding', 'utf8'))) as fid_in:
            for line in fid_in:
                line = line.strip('\n\r')
                if line.startswith('//<subject>SDN:LOCAL:'):
                    line = line.replace(' ', '')
                elif line.startswith('Cruise'):
                    split_line = [par.strip() for par in line.split('\t')]
                    new_split_line = []
                    for item in split_line:
                        split_item = item.split('[')
                        if split_item[0].strip() not in ['Bot. Depth']:
                            split_item[0] = split_item[0].replace(' ', '')
                            item = ' ['.join(split_item)

                        new_split_line.append(item)
                    line = '\t'.join(new_split_line)
                new_lines.append(line)

        file_path = kwargs.get('save_file_path', self.file_path)
        with codecs.open(file_path, 'w', encoding=kwargs.get('encoding_out', kwargs.get('encoding', 'utf8'))) as fid_out:
            fid_out.write('\n'.join(new_lines))

class ModifyODVfile(object):

    def __init__(self, file_path):
        if not os.path.exists(file_path):
            raise IOError
        self.file_path = file_path

        self.metadata = []
        self.data = []
        self.header = []
        self.df = []

        self.modifications_made = []


    def load_metadata(self, breakpoint='Cruise', **kwargs):
        """
        Read lines until the line that starts with breakpoint, default = 'Cruise' according to Seadatanet ODV file standard.

        :param breakpoint: 'Cruise' by default
        :param kwargs:
        :return:
        """
        self.metadata = []
        with codecs.open(self.file_path, encoding=kwargs.get('encoding_in', kwargs.get('encoding', 'cp1252'))) as fid_in:
            for line in fid_in:
                line = line.strip('\n\r')
                if line.startswith(breakpoint):
                    break
                else:
                    self.metadata.append(line)

    def load_data(self, comment_prefix='//', header_locator='Cruise', **kwargs):
        """
        Reader data and data header

        :param comment_prefix:
        :param header_locator:
        :param kwargs:
        :return:
        """
        self.data = []
        self.header = []
        with codecs.open(self.file_path, encoding=kwargs.get('encoding_in', kwargs.get('encoding', 'cp1252'))) as fid_in:
            for line in fid_in:
                line = line.strip('\n\r')
                if line.startswith(comment_prefix):
                    continue
                else:
                    if line.startswith(header_locator):
                        self.header = line.split('\t')
                    else:
                        self.data.append(line.split('\t'))
            self.df = pd.DataFrame.from_records(data=self.data, columns=self.header)

    def add_column(self, df=False, current_column_name='', new_column='QV:SEADATANET', data='1', position=1, **kwargs):
        """
        Add columns to ODV file.
        OBS! if you add parameter column it will break the Seadatanet ODV structure, you need to add a row in the
        metadata as well, not ready in this version yet. For now this is for adding missing quality flag columns.
        /OBac 2018-11-14

        :param df:
        :param current_column_name: name of the column used as a reference
        :param new_column: label of your new column
        :param data: mest be string(s) could be a scalar which will be the same for all rows, but also a list with the same len() as other data
        :param position: position in relation to current_column_name, 1 means directly after, -1 means before etc...
        :param kwargs:
        :return:
        """

        if df:
            self.df = df

        #else:
        #    if df:
        #        self.df = df
        #    else:
        #        raise ValueError('Missing pandas dataframe! Use _load_data() or supply your own dataframe as input')

        index = self.df.keys().get_loc(current_column_name)

        if self.df.keys()[index + position] != new_column:
            if type(data) == list:
                new_data = data
            else:
                new_data = [data] * len(self.df[current_column_name])
            self.df.insert(loc=index + position, column=new_column, value=new_data, allow_duplicates=True)
        else:
            print('WARNING! The column you want to insert is already present in your file: %s' % self.file_path)

    def convert_to_timeseries(self, **kwargs):
        """
        Converts the file to a time series by adding the column "time_ISO8601" as first and primary variable
        //<subject>SDN:LOCAL:time_ISO8601</subject><object>SDN:P01::DTUT8601</object><units>SDN:P06::TISO</units>
        Also adds the QV:SEADATANET column.
        Information of time is taken from the first metadata row.

        :return:
        """
        if 'convert_to_timeseries' in self.modifications_made:
            return

        primary_par = 'time_ISO8601 [yyyy-mm-dd]'
        primary_semantic = '//<subject>SDN:LOCAL:time_ISO8601</subject><object>SDN:P01::DTUT8601</object><units>SDN:P06::TISO</units>\n'

        # Check if file already has time as primary variable
        odv_file = odvfile.ODVfile(self.file_path)
        primary_variable = odv_file.get_primary_variable()
        # print('primary_variable', primary_variable)
        if primary_par in primary_variable: # Might be with unit in "primary_variable", hence "in".
            return

        # Add sematic header line
        lines = self.metadata[:]
        for k, line in enumerate(lines):
            if line.startswith('//<subject>'):
                self.metadata.insert(k, primary_semantic)
                break

        # Add data in dataframe
        time = self.df['yyyy-mm-ddThh:mm:ss.sss'].values[0]
        last_metadata_variable = kwargs.get('last_metadata_variable', 'Bot. Depth [m]')
        self.add_column(current_column_name=last_metadata_variable, new_column=primary_par, data=time, position=1)
        self.add_column(current_column_name=primary_par, new_column='QV:SEADATANET', data='1', position=1)

        self.modifications_made.append('convert_to_timeseries')

    def rename_column(self, **kwargs):
        self.df.rename(index=str, columns=kwargs, inplace=True)


    def replace_string_in_metadata(self, from_string, to_string):
        """
        Replaces string in metadata.
        :return:
        """
        if not self.metadata:
            print('No metadata loaded for file {}'.format(self.file_path))
            return
        for k, line in enumerate(self.metadata):
            self.metadata[k] = line.replace(from_string, to_string)

    def replace_string_in_column(self, from_string, to_string, *args):
        """
        Replaces string in columns given in args.
        :param from_string:
        :param to_string:
        :param args:
        :return:
        """
        for col in args:
            if col not in self.df.columns:
                continue
            self.df[col] = self.df[col].apply(lambda x: x.replace(from_string, to_string))

    def set_qf_for_column(self, column, flag, replace_flag=None):
        """
        Sets the 'QV:SEADATANET' column to flag for the given column.
        If replace_flag is given only this flag is changed
        :param column:
        :param flag:
        :return:
        """
        if column not in self.df:
            print('Column {} not in file {}'.format(column, self.file_path))
            return
        qf_index = list(self.df.columns).index(column) + 1
        if replace_flag is not None:
            self.df.iloc[np.where(self.df.iloc[:, qf_index] == replace_flag)[0], qf_index] = str(flag)
        else:
            self.df.iloc[:, qf_index] = flag

        # Replace with flag 9 if missing value
        index = np.where(self.df.iloc[:, qf_index-1] == '')[0]
        self.df.iloc[index, qf_index] = '9'




    def replace_values_in_col(self, df=False, column_name='Bot. Depth [m]', old_val = 'None', new_val = '', **kwargs):
        """
        Fix a bug when creating Seadatanet ODV-files that got None as Bot. Depth when value was missing,
        replace these None with empty string.

        :param df:
        :param column_name:
        :param kwargs:
        :return:
        """

        if df:
            self.df = df

        self.df.loc[self.df[column_name] == old_val, column_name] = new_val

    def write_new_odv(self, output_dir='D:/temp', file_name=False, df=False, metadata=False, **kwargs):
        """
        Write data and metadata to file.
        NEW: Removed empty rows in metadata

        :param self:
        :param output_dir: directory to store the new ODV-file
        :param file_name:
        :param df:
        :param metadata:
        :param kwargs:
        :return:
        """

        if df:
            self.df = df

        if metadata:
            self.metadata = metadata

        if not all([len(self.df), self.metadata]):
            print('No data loaded in file object for file {}'.format(self.file_path))
            return

        if not file_name:
            file_name = self.file_path.split('\\')[-1]

        with codecs.open(os.path.join(output_dir, file_name), 'w',
                         encoding=kwargs.get('encoding_out', kwargs.get('encoding', 'cp1252'))) as fid_out:

            for line in self.metadata:
                line = line.strip()
                if line:
                    fid_out.write(line + '\n')

            data_dict = self.df.to_dict('split')

            fid_out.write('\t'.join(list(self.df))+'\n')

            # if file_name == 'Perca_fluviatilis_6719_20090817.txt':
            #     print('=' * 50)
            #     print('=' * 50)
            #     print('=' * 50)
            #     print('=' * 50)
            #     print('=' * 50)
            #     print('=' * 50)
            #     print('\n'.join(self.metadata))
            #     print(self.metadata)
            for item in data_dict['data']:

                fid_out.write('\t'.join(item)+'\n')
