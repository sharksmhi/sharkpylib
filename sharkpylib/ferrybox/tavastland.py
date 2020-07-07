# -*- coding: utf-8 -*-
# Copyright (c) 2019 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import re
import codecs

import datetime
import time
import numpy as np
import sharkpylib
from sharkpylib import loglib
from sharkpylib import mappinglib
from sharkpylib import exceptionlib

from sharkpylib.file.file_handlers import MappingDirectory
from sharkpylib.file.file_handlers import ListDirectory
from sharkpylib.file.file_handlers import Directory

from sharkpylib.qc.mask_areas import MaskAreasDirectory

from sharkpylib.file import txt_reader

try:
    import pandas as pd
except:
    pass

import sys
parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_directory not in sys.path:
    sys.path.append(parent_directory)
from .. import gismo


# def get_logger(**kwargs):
#     DEFAULT_LOG_INPUT = {'name': 'tavastland',
#                          'level': 'DEBUG'}
#     DEFAULT_LOG_INPUT.update(kwargs)
#     log_object = log.Logger(**DEFAULT_LOG_INPUT)
#     logger = log_object.get_logger()
#     return logger

class TavastlandException(Exception):
    """

    Blueprint for error message.
    code is for external mapping of exceptions. For example if a GUI wants to
    handle the error text for different languages.
    """
    code = None
    message = ''

    def __init__(self, message='', code=''):
        self.message = '{}: {}'.format(self.message, message)
        if code:
            self.code = code


class TavastlandExceptionCorrupedFile(TavastlandException):
    """
    """
    code = ''
    message = 'Corruped file'


class TavastlandExceptionNoCO2data(TavastlandException):
    """
    """
    code = ''
    message = ''


class TavastlandExceptionNoMatchWhenMerging(TavastlandException):
    """
    """
    code = ''
    message = ''



class File(object):
    def __init__(self, file_path='', **kwargs):
        self.file_path = file_path
        self.file_directory = os.path.dirname(self.file_path)
        self.file_name = os.path.basename(self.file_path)
        self.file_id = self.file_name

        self.df = pd.DataFrame()
        self.time_start = None
        self.time_end = None

        self.data_loaded = None

        self.time_in_file_name_formats = ['TP_%Y%m%d%H%M%S.mit']
        self._add_file_path_time()

        self.time_frozen_between = []

        if kwargs.get('load_file'):
            self.load_file()

    def _len_header_equals_len_data(self, file_path):
        with open(file_path) as fid:
            for r, line in enumerate(fid):
                split_line = line.split('\t')
                if r==0:
                    header = split_line
                else:
                    if len(header) == len(split_line):
                        return True
                    return False

    def _add_file_path_time(self):
        self.file_path_time = None
        self.file_path_year = None
        self.file_path_possible_years = []
        for time_format in self.time_in_file_name_formats:
            try:
                time_object = datetime.datetime.strptime(self.file_name, time_format)
                self.file_path_time = time_object
                break
            except ValueError:
                # logger.debug('No time in file path for file: {}'.format(self.file_path))
                pass

        # Find year
        result = re.findall('\d{4}', self.file_name)
        if result:
            self.file_path_year = int(result[0])
            self.file_path_possible_years = [self.file_path_year-1, self.file_path_year, self.file_path_year+1]

    def _delete_columns(self):
        if 'Date' in self.df.columns:
            self.df.drop(['Date'], axis=1, inplace=True)
            # Time is removed in method _add_columns
        elif 'PC Date' in self.df.columns:
            self.df.drop(['PC Date', 'PC Time'], axis=1, inplace=True)

        if 'Lat' in self.df.columns:
            self.df.drop(['Lat', 'Lon'], axis=1, inplace=True)
        elif 'latitude' in self.df.columns:
            self.df.drop(['latitude', 'longitude'], axis=1, inplace=True)

    def _add_columns(self):
        # Time
        if 'Date' in self.df.columns:
            time_str = self.df['Date'] + ' ' + self.df['Time'].copy()
            self.df.drop('Time', axis=1, inplace=True)
            self.df['time'] = pd.to_datetime(time_str, format='%d.%m.%Y %H:%M:%S')
        elif 'PC Date' in self.df.columns:
            time_str = self.df['PC Date'] + ' ' + self.df['PC Time']
            self.df['time'] = pd.to_datetime(time_str, format='%d/%m/%y %H:%M:%S')

        # Position
        if 'Lat' in self.df.columns:
            self.df['lat'] = self.df['Lat'].apply(as_float)
            self.df['lon'] = self.df['Lon'].apply(as_float)
        elif 'latitude' in self.df.columns:
            self.df['lat'] = self.df['latitude'].apply(as_float)
            self.df['lon'] = self.df['longitude'].apply(as_float)
        else:
            self.df['lat'] = np.nan
            self.df['lon'] = np.nan
            
        self.df['source_file'] = self.file_name

    def _remove_duplicates(self):
        # print('REMOVE DUPLICATES', self.file_id)
        # First save missing periodes
        dub_boolean = self.df.duplicated('time', keep=False)
        between = []
        missing_period = []
        for i, t0, b0, t1, b1 in zip(self.df.index[:-1], self.df['time'].values[:-1], dub_boolean.values[:-1],
                                     self.df['time'].values[1:], dub_boolean.values[1:]):
            if i == 0 and b0:
                missing_period.append('?')
            if b1 and not b0:
                #         t0s = pd.to_datetime(t0).strftime('%Y%m%d%H%M%S')
                #         missing_period.append(t0s)
                missing_period.append(t0)
            elif b0 and not b1:
                #         t1s = pd.to_datetime(t1).strftime('%Y%m%d%H%M%S')
                #         missing_period.append(t1s)
                missing_period.append(t1)
            #     print(missing_period)
            if len(missing_period) == 2:
                between.append(missing_period)
                #         between.append('-'.join(missing_period))
                missing_period = []
        if missing_period:
            missing_period.append('?')
            between.append(missing_period)
        #     between.append('-'.join(missing_period))
        # print('between:', len(between))
        self.time_frozen_between = between

        # Now drop all duplicates
        self.df.drop_duplicates('time', keep=False, inplace=True)

    def valid_data_line(self, line):
        if 'DD.MM.YYYY' in line:
            # print('DD.MM.YYYY', self.file_path)
            return False
        if not line.strip():
            # print('BLANK', self.file_path)
            return False
        return True

    def load_file(self, **kwargs):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError
        header = []
        data = []
        with codecs.open(self.file_path, encoding=kwargs.get('encoding', 'cp1252')) as fid:
            for row, line in enumerate(fid):
                split_line = line.strip('\n\r').split(kwargs.get('sep', '\t'))
                split_line = [item.strip() for item in split_line]
                if row == 1 and header:
                    if len(header) != len(split_line):
                        header = header[:len(split_line)]
                if not header:
                    header = split_line
                else:
                    if len(header) != len(split_line):
                        raise TavastlandExceptionCorrupedFile
                        logger.warning('invalid file: {}'.format(row, self.file_path))
                        self.data_loaded = False
                        return False
                    if not self.valid_data_line(line):
                        logger.warning('Removing invalid line {} from file: {}'.format(row, self.file_path))
                        continue
                    data.append(split_line)

        self.original_columns = header[:]
        self.df = pd.DataFrame(data, columns=header)
        self._add_columns()
        self._remove_duplicates()
        self.filter_data()
        self._delete_columns()
        self.data_loaded = True
        return True
    
    def filter_data(self):
        """
        Filters the data from unwanted lines etc.
        :return:
        """
        combined_keep_boolean = pd.Series([True]*len(self.df))

        keep_boolean = ~self.df[self.original_columns[0]].str.contains('DD.MM.YYYY')
        combined_keep_boolean = combined_keep_boolean & keep_boolean

        keep_boolean = ~self.df[self.original_columns[0]].str.contains('.1904')
        combined_keep_boolean = combined_keep_boolean & keep_boolean

        keep_boolean = self.df['time'] <= datetime.datetime.now()
        combined_keep_boolean = combined_keep_boolean & keep_boolean

        removed = self.df.loc[~combined_keep_boolean]
        if len(removed):
            logger.warning('{} lines removed from file {}'.format(len(removed), self.file_path))
        self.df = self.df.loc[combined_keep_boolean, :]

    def clean_file(self, export_directory):
        """
        Loads file (including filter data) and saves to the export directory.
        :return
        """
        # print(export_directory)
        if export_directory == self.file_directory:
            raise TavastlandException('Cannot export to the same directory!')
        if not os.path.exists(export_directory):
            os.makedirs(export_directory)
        if self.data_loaded is None:
            self.load_file()
        export_file_path = os.path.join(export_directory, self.file_name)
        self.df[self.original_columns].to_csv(export_file_path, index=False, sep='\t')

    def get_df(self):
        if self.data_loaded is None:
            self.load_file()
        return self.df

    def get_time_range(self):
        def get_time(line):
            date = re.findall('\d{2}\.\d{2}\.\d{4}', line)
            time = re.findall('\d{2}:\d{2}:\d{2}', line)
            if date and time:
                return datetime.datetime.strptime(date[0] + time[0], '%d.%m.%Y%H:%M:%S')

            date = re.findall('\d{2}/\d{2}/\d{2}', line)
            time = re.findall('\d{2}:\d{2}:\d{2}', line)
            if date and time:
                return datetime.datetime.strptime(date[0] + time[0], '%d/%m/%y%H:%M:%S')

        self.time_start = None
        self.time_end = None
        if self.data_loaded:
            self.time_start = self.df.time.values[0]
            self.time_end = self.df.time.values[-1]
            return self.time_start, self.time_end
        else:
            with codecs.open(self.file_path) as fid:
                for r, line in enumerate(fid):
                    if self.valid_data_line(line):
                        if r == 0:
                            continue
                        elif not self.time_start:
                            time = get_time(line)
                            self.time_start = time
                self.time_end = get_time(line)
        return self.time_start, self.time_end

    def in_time_range(self, datetime_object):
        if not self.time_start:
            self.get_time_range()
        return (datetime_object >= self.time_start) & (datetime_object <= self.time_end)

    def check_if_valid_file_name(self):
        """
        External method.
        Returns True if file_name follows the structure(s) described in method.
        :param file_name:
        :return:
        """
        raise NotImplementedError

    def warnings(self):
        """
        Returns a list of strange things found in file. Strange things kan be handled.
        :return: list with description of the warnings.
        """
        raise NotImplementedError

    def get_file_errors(self):
        """
        Returns a list of errors in file if any. Errors are obvious faults that can not be handled.
        :return list with description of the errors.
        """
        raise NotImplementedError

    def _get_file_errors(self):
        error_list = []
        if not self._len_header_equals_len_data(self.file_path):
            text = 'Header is not the same length as data in file: {}.'.format(self.file_name)
            error_list.append(text)
        return error_list


class MITfile(File):

    def __init__(self, file_path='', **kwargs):
        File.__init__(self, file_path, **kwargs)

    def check_if_valid_file_name(self, file_name):
        """
        External method.
        Returns True if file_name follows the structure(s) described in method.
        :param file_name:
        :return:
        """
        if not file_name.endswith('.mit'):
            return False
        return True

    def warnings(self):
        """
        Returns a list of strange things found in file. Strange things kan be handled.
        :return: list with description of the warnings.
        """
        raise NotImplementedError

    def get_file_errors(self):
        """
        Returns a list of errors in file if any. Errors are obvious faults that can not be handled.
        :return list with description of the errors.
        """
        error_list = self._get_file_errors()

        # Check time
        start, end = self.get_time_range()
        d = datetime.datetime(1980, 1, 1)
        this_year = datetime.datetime.now().year

        if not all([start, end]):
            text = 'Could not find time in file {}.'.format(self.file_name)
            error_list.append(text)
        else:
            if start < d:
                text = 'Start data is too early in file {}. Before {}'.format(self.file_name, d.strftime('%Y%m%d'))
                error_list.append(text)
                # continue
            if start > end:
                text = 'Start time > end time in file {}.'.format(self.file_name)
                error_list.append(text)
                # continue
            if any([start.year > this_year, end.year > this_year]):
                text = 'Start year or end year is later than current year in file {}.'.format(self.file_name)
                error_list.append(text)
                # continue
            if any([start.year == 1904, end.year == 1904]):
                text = 'Start year or end year is 1904 in file {}.'.format(self.file_name)
                logger.info(text)
                error_list.append(text)

        if error_list:
            logger.info('; '.join(error_list))

        return error_list


class CO2file(File):

    def __init__(self, file_path='', **kwargs):
        File.__init__(self, file_path, **kwargs)

    def check_if_valid_file_name(self, file_name):
        """
        External method.
        Returns True if file_name follows the structure(s) described in method.
        :param file_name:
        :return:
        """
        if not file_name.endswith('dat.txt'):
            return False
        return True

    def warnings(self):
        """
        Returns a list of strange things found in file. Strange things kan be handled.
        :return: list with description of the warnings.
        """
        raise NotImplementedError

    def get_file_errors(self):
        """
        Returns a list of errors in file if any. Errors are obvious faults that can not be handled.
        :return list with description of the errors.
        """
        error_list = self._get_file_errors()

        # Check time
        start, end = self.get_time_range()
        d = datetime.datetime(1980, 1, 1)
        this_year = datetime.datetime.now().year

        if not all([start, end]):
            text = 'Could not find time in file {}.'.format(self.file_name)
            error_list.append(text)

        if error_list:
            logger.info('; '.join(error_list))

        return error_list


class FileHandler(object):
    def __init__(self, **kwargs):
        global logger
        logger = loglib.get_logger(**kwargs.get('log_info', {}))
        logger.debug('Starting FileHandler for Tavastland')
        self.directories = {}
        self.directories['mit'] = kwargs.get('mit_directory', None)
        self.directories['co2'] = kwargs.get('co2_directory', None)

        self.export_directory = kwargs.get('export_directory', None)

        self.save_directory = None

        self.current_merge_data = pd.DataFrame()

        self.df_header = ['file_id', 'file_path', 'time_start', 'time_end']

        self.export_time_format_str = '%Y%m%d%H%M%S'

        self.package_prefix = 'ferrybox-tavastland'

        self.objects = dict()
        self.dfs = dict()

        self.files_with_errors = dict()
        self.corruped_files = dict()

        self.metadata = []
        self.metadata_added = {}

        self.time_frozen_between = {}

        list_dir_object = ListDirectory()
        self.exclude_co2_types = list_dir_object.get_file_object('list_tavastland_exclude_types.txt', comment='#').get()

        self.reset_time_range()
        self.reset_data()

        self.set_time_delta(seconds=30)

        for file_type, directory in self.directories.items():
            if directory:
                self.set_file_directory(file_type, directory)

        # if self.mit_directory is not None:
        #     self.set_mit_directory(self.mit_directory)
        #
        # if self.co2_directory is not None:
        #     self.set_co2_directory(self.co2_directory)

    def set_export_directory(self, directory):
        """
        Sets the export directory.
        :param directory:
        :return:
        """
        self.export_directory = directory

    def set_file_directory(self, file_type, directory):
        """
        Saves path to files with the given directory for the given file_type
        :param file_type:
        :return:
        """
        this_year = datetime.datetime.now().year
        if file_type == 'mit':
            File_type_class = MITfile
            file_type_object = MITfile()
        elif file_type == 'co2':
            File_type_class = CO2file
            file_type_object = CO2file()

        self.files_with_errors[file_type] = []
        self.corruped_files[file_type] = []

        self.objects[file_type] = dict()
        data_lines = []
        for root, dirs, files in os.walk(directory):
            for name in files:
                if not file_type_object.check_if_valid_file_name(name):
                    continue
                file_path = os.path.join(root, name)
                file_object = File_type_class(file_path)
                start, end = file_object.get_time_range()

                errors = file_object.get_file_errors()
                if errors:
                    print('name', name)
                    print('errors', errors)
                    errors_dict = {name: errors}
                    self.files_with_errors[file_type].append(errors_dict)

                data_lines.append([name, file_path, start, end])
                self.objects[file_type][name] = file_object
        if not data_lines:
            raise TavastlandException('No valid {}-files found!'.format(file_type))
        self.dfs[file_type] = pd.DataFrame(data_lines, columns=self.df_header)
        self.dfs[file_type].sort_values('time_start', inplace=True)

    def get_file_id(self, time=None, file_type='mit'):
        """
        Returns the mit file matching the given input.

        :param time: datetime_object
        :return:
        """
        if time:
            result = self.dfs[file_type].loc[(self.dfs[file_type]['time_start'] <= time) &
                                             (time <= self.dfs[file_type]['time_end']), 'file_id'].values
            if len(result) > 1:
                logger.debug('Several files matches time stamp: {}\n{}'.format(time, '\n'.join(list(result))))
                raise TavastlandException('Several files matches time stamp {}: \n{}'.format(time, '\n'.join(list(result))))
            elif len(result) == 0:
                return None
            else:
                return result[0]
        else:
            raise AttributeError('Missing input parameter "time"')

    def get_previous_file_id(self, file_id=None, time_stamp=None, file_type='mit'):
        """
        Returns the previous file_id
        :param file_id:
        :return:
        """
        df = self.dfs.get(file_type)
        if file_id:
            if file_id in df['file_id'].values:
                index = df.index[df['file_id'] == file_id][0]
                if index == 0:
                    return None
                else:
                    return df.at[index-1, 'file_id']
            else:
                return None
        elif time_stamp:
            end_time_boolean = df['time_end'] < time_stamp
            matching_file_id_list = df.loc[end_time_boolean]['file_id'].values
            # print('='*20)
            # print('matching_file_id_list')
            # print(matching_file_id_list)
            # print(type(matching_file_id_list))
            if any(matching_file_id_list):
                return matching_file_id_list[-1]
            else:
                return None

    def set_time_range(self, time_start=None, time_end=None, time=None, file_id=None, file_type='mit'):
        """
        Selects/sets the period to work with. You can select data by giving start and end time or by file_id.
        Also option to find file_id by time stamp (looking at mit_file) given in time. All time objects ar of type
        datetime.datetime.

        :param time_start:
        :param time_end:
        :param time:
        :param file_name:
        :return:
        """
        if time:
            file_id = self.get_file_id(time=time, file_type=file_type)

        if file_id:
            for file_type in self.objects:
                if file_id in self.objects[file_type]:
                    time_start, time_end = self.objects[file_type][file_id].get_time_range()
                    break
            else:
                raise ValueError('Could not find file_id {}')

        self.reset_time_range()

        self.current_time_start = time_start
        self.current_time_end = time_end

    def set_time_delta(self, **kwargs):
        """
        Sets the timedelta allowed for matching data.
        :param kwargs:
        :return:
        """
        self.time_delta = pd.Timedelta(**kwargs)

    def reset_time_range(self):
        self.current_time_start = None
        self.current_time_end = None

        self.reset_data()

    def load_data(self):
        """
        Loades data in time range. Time range is set in method select_time_range.
        :return:
        """
        t0 = time.time()
        if not all([self.current_time_start, self.current_time_end]):
            raise Exception

        self.reset_data()

        # Load files within time range
        self.current_data['mit'] = self.get_data_within_time_range('mit', self.current_time_start, self.current_time_end)
        self.current_data['co2'] = self.get_data_within_time_range('co2', self.current_time_start, self.current_time_end)

        # Reset index
        self.current_data['mit'] = self.current_data['mit'].reset_index(drop=True)
        self.current_data['co2'] = self.current_data['co2'].reset_index(drop=True)

        # print('Load data')
        # print('mit', len(self.current_data['mit']))
        # print('co2', len(self.current_data['co2']))
        # print('Loaded in: {}'.format(time.time()-t0))

    def reset_data(self):
        self.current_data = {}
        self.current_merge_data = pd.DataFrame()
        self.pCO2_constants = {}
        self.std_val_list = []
        self.std_co2_list = []
        self.std_latest_time = None
        self.time_frozen_between = {}

    def clean_files(self, export_directory, file_list=False):
        if not self.current_data:
            raise TavastlandException
        if not file_list:
            file_list = []
            for key, value in self.objects.items():
                for file_name in value:
                    if self.objects[key][file_name].data_loaded:
                       file_list.append(file_name)
        # Clean files and save in subdirectories
        for key in self.objects:
            directory = os.path.join(export_directory, 'cleaned_files', key)
            for file_name in file_list:
                if file_name in self.objects[key]:
                    self.objects[key][file_name].clean_file(directory)

    def get_data_within_time_range(self, file_type, time_start, time_end):
        """
        Extracts data within time range from mit or c02 files. expands time limits with self.time_delta first.

        :param file_type: mit or co2
        :param time_start:
        :param time_end:
        :return:
        """
        # print('get_data_within_time_range')
        self.time_frozen_between[file_type] = []
        object_dict = self.objects.get(file_type)
        file_id_list = self.get_file_ids_within_time_range(file_type, time_start, time_end)

        ts = np.datetime64(time_start)
        te = np.datetime64(time_end)

        df = pd.DataFrame()
        for file_id in file_id_list:
            if file_id in self.files_with_errors:
                logger.warning('Discarding file {}. File has errors!'.format(file_id))
                continue
            object = object_dict.get(file_id)

            try:
                object_df = object.get_df()
            except TavastlandExceptionCorrupedFile:
                self.corruped_files[file_type].append(file_id)
                logger.warning('Discarding file {}. File has errors!'.format(file_id))
                continue

            df = df.append(object_df)

            # print('file_id', file_id)
            # print('object.time_frozen_between', object.time_frozen_between)
            for t in object.time_frozen_between:
                # print(t, time_start, time_end)
                add = False
                # print(t[0], time_start)
                # print(type(t[0]), type(time_start))
                if t[0] != '?' and t[0] >= ts:
                    add = True
                elif t[1] != '?' and t[1] <= te:
                    add = True
                if add:
                    self.time_frozen_between[file_type].append(t)

        if not len(df):
            raise TavastlandExceptionNoCO2data('No data in time range {} - {}'.format(time_start, time_end))
        else:
            df.sort_values('time', inplace=True)

        # Add file type to header
        df.columns = ['{}_{}'.format(file_type, item) for item in df.columns]
        df['time'] = df['{}_time'.format(file_type)]

        # Strip dates
        if file_type == 'co2':
            time_start = time_start - self.time_delta
            time_end = time_end + self.time_delta
        time_boolean = (df.time >= time_start) & (df.time <= time_end)
        df = df.loc[time_boolean]
        df.sort_values(by='time', inplace=True)

        return df

    def get_file_ids_within_time_range(self, file_type, time_start, time_end):
        """
        Returns a list of the matching file_id:s found in self.dfs
        :param file_type:
        :param time_start:
        :param time_end:
        :return:
        """
        df = self.dfs.get(file_type)
        ts = time_start - self.time_delta
        te = time_end + self.time_delta 
        boolean = (df['time_end'] >= ts) & (df['time_end'] <= te)
        # | (df['time_start'] <= ts) & (df['time_start'] <= te)
        # if not any(boolean):
        #     boolean = (df['time_end'] >= ts) & (df['time_end'] <= te)
        return sorted(df.loc[boolean, 'file_id'])

    def get_files_with_errors(self, file_type):
        """
        Returns a list with all files that has errors in them.
        :param file_type:
        :return:
        """
        file_list = []
        for file_name_dict in self.files_with_errors[file_type]:
            file_list.append(list(file_name_dict.keys())[0])
        return file_list

    def merge_data(self):
        """
        Merges the dataframes in self.current_data.
        :return:
        """
        missing_data = []
        for file_type, df in self.current_data.items():
            if not len(df):
                missing_data.append(file_type)
        if missing_data:
            raise Exception('Missing data from the following sources: {}'.format(', '.join(missing_data)))

        # We do not want same co2 merging to several lines in mit.
        # Therefore we start by merging co2 and mit with the given tolerance.
        co2_merge = pd.merge_asof(self.current_data['co2'], self.current_data['mit'],
                                  on='time',
                                  tolerance=self.time_delta,
                                  direction='nearest')

        # In this df we only want to keep lines that has mit_time
        co2_merge = co2_merge[~pd.isna(co2_merge['mit_time'])]
        # co2_merge.sort_values('time', inplace=True)

        # Now we merge (outer join) the original mit-dataframe with the one we just created.
        # This will create a df that only has one match of co2 for each mit (if matching).
        self.current_merge_data = pd.merge(self.current_data['mit'],
                                           co2_merge,
                                           left_on='mit_time',
                                           right_on='mit_time',
                                           suffixes=('', '_remove'),
                                           how='outer')

        remove_columns = [col for col in self.current_merge_data.columns if col.endswith('_remove')]
        self.current_merge_data.drop(remove_columns, axis=1, inplace=True)

        self.current_merge_data = self.current_merge_data.reset_index(drop=True)

        # Add time par
        self.current_merge_data['time'] = self.current_merge_data['mit_time']
        # Add position par
        self.current_merge_data['lat'] = self.current_merge_data['mit_lat']
        self.current_merge_data['lon'] = self.current_merge_data['mit_lon']

        self.mit_columns = [col for col in self.current_merge_data.columns if col.startswith('mit_')]
        self.co2_columns = [col for col in self.current_merge_data.columns if col.startswith('co2_')]

        # Add diffs
        self.current_merge_data['diff_time'] = abs(self.current_merge_data['co2_time'] - \
                                                   self.current_merge_data['mit_time']).astype('timedelta64[s]')

        self.current_merge_data['diff_lat'] = self.current_merge_data['co2_lat'] - \
                                              self.current_merge_data['mit_lat']

        self.current_merge_data['diff_lon'] = self.current_merge_data['co2_lon'] - \
                                              self.current_merge_data['mit_lon']

        self.diff_columns = [col for col in self.current_merge_data.columns if col.startswith('diff_')]

        if self.current_merge_data['diff_time'].isnull().values.all():
            raise TavastlandExceptionNoMatchWhenMerging('No match in data between {} and {} '
                                                        'with time tolerance {} seconds'.format(self.current_time_start,
                                                                                                 self.current_time_end,
                                                                                                 self.time_delta.seconds))
        self._sort_merge_data_columns()

        # Add merge comment
        if not self.metadata_added.get('time_tolerance'):
            self.metadata = [f'COMMENT_MERGE;{self._get_time_string()};Data merged with time tolerance '
                             f'{self.time_delta.seconds} seconds.']
            self.metadata_added['time_tolerance'] = True

    def _sort_merge_data_columns(self):
        columns = sorted(self.current_merge_data.columns)
        columns.pop(columns.index('time'))
        columns.pop(columns.index('lat'))
        columns.pop(columns.index('lon'))
        new_columns = ['time', 'lat', 'lon'] + columns
        self.current_merge_data = self.current_merge_data[new_columns]
        self.current_merge_data.fillna('', inplace=True)

    def _mapp_columns(self, df=None):
        if df is None:
            df = self.current_merge_data
        mapping_dir_object = MappingDirectory()
        mapping = mapping_dir_object.get_file_object('mapping_tavastland.txt', from_col='co2_merged_file', to_col='nodc')
        df.columns = mapping.get_mapped_list(df.columns)

    def _remove_types(self):
        boolean = self.current_merge_data['co2_Type'].isin(self.exclude_co2_types)
        self.current_merge_data.loc[boolean, self.co2_columns] = ''

    def old_remove_areas(self, file_path):
        """
        Remove areas listed in file_path. file_path should be of type gismo.qc.qc_trijectory.
        Maybe this class should be located in a more general place.
        :param file_path:
        :return:
        """
        area_object = gismo.qc.qc_trajectory.FlagAreasFile(file_path)
        areas = area_object.get_areas()
        df = self.current_merge_data
        masked_areas = []
        combined_boolean = df['time'] == ''
        for name, area in areas.items():
            lat_min = area.get('lat_min')
            lat_max = area.get('lat_max')
            lon_min = area.get('lon_min')
            lon_max = area.get('lon_max')

            boolean = (df['lat'].astype(float) >= lat_min) & \
                      (df['lat'].astype(float) <= lat_max) & \
                      (df['lon'].astype(float) >= lon_min) & \
                      (df['lon'].astype(float) <= lon_max)
            if len(np.where(boolean)):
                masked_areas.append(name)
            combined_boolean = combined_boolean | boolean
        # Remove areas
        self.current_merge_data = self.current_merge_data.loc[~combined_boolean, :]

        return masked_areas

    def get_nr_rows(self, file_type):
        return len(self.current_data[file_type])

    def get_min_and_max_time(self):
        """
        Returns the minimum and maximum time found looking in both time_start and time_end and all file_types.
        :return:
        """
        time_list = []
        for df in self.dfs.values():
            time_list.extend(list(df['time_start']))
            time_list.extend(list(df['time_end']))
        return min(time_list), max(time_list)

    def get_merge_data(self):
        """
        Returns merge data limited by time range
        :return:
        """
        boolean = (self.current_merge_data['time'] >= self.current_time_start) & \
                  (self.current_merge_data['time'] <= self.current_time_end)
        return self.current_merge_data.loc[boolean, :].copy()

    def old_map_header_like_iocftp(self):
        """
        :return:
        """

        mappings = mappinglib.MappingDirectory()
        mapping_object = mappings.get_mapping_object('mapping_tavastland',
                                                     from_col='merged_file',
                                                     to_col='IOCFTP_tavastland')
        new_header = []
        for col in self.current_merge_data.columns:
            new_header.append(mapping_object.get(col))

        self.current_merge_data.columns = new_header

    def old_map_header_like_internal(self):
        """
        :return:
        """

        mappings = mappinglib.MappingDirectory()
        mapping_object = mappings.get_mapping_object('mapping_tavastland',
                                                     from_col='IOCFTP_tavastland',
                                                     to_col='internal')
        new_header = []
        for col in self.current_merge_data.columns:
            new_header.append(mapping_object.get(col))

        self.current_merge_data.columns = new_header

    def calculate_pCO2(self):
        """
        Calculates pCO2 on self.current_merge_data
        :return:
        """
        self.current_merge_data['calc_k'] = np.nan
        self.current_merge_data['calc_m'] = np.nan
        self.current_merge_data['calc_Pequ'] = np.nan
        self.current_merge_data['calc_pCO2 dry air'] = np.nan

        self.current_merge_data['calc_xCO2'] = np.nan
        self.current_merge_data['calc_pCO2'] = np.nan

        items = ['calc_k', 'calc_m', 'calc_xCO2', 'calc_Pequ', 'calc_pCO2 dry air', 'calc_time_since_latest_std']
        for i in self.current_merge_data.index:
            values = self._get_pCO2_data_from_row(self.current_merge_data.iloc[i])
            for key in items:
                self.current_merge_data.at[i, key] = values.get(key, np.nan)

            # self.current_merge_data.at[i, 'calc_k'] = values.get('calc_k', np.nan)
            # self.current_merge_data.at[i, 'calc_m'] = values.get('calc_m', np.nan)
            # self.current_merge_data.at[i, 'calc_Pequ'] = values.get('calc_Pequ', np.nan)
            # self.current_merge_data.at[i, 'calc_pCO2 dry air'] = values.get('calc_pCO2 dry air', np.nan)
            # self.current_merge_data.at[i, 'calc_xCO2'] = values.get('calc_xCO2', np.nan)

        self._calculate_pCO2()

        self._sort_merge_data_columns()

        self._remove_types()

        # self._mapp_columns()

    def _calculate_pCO2(self):

        salinity_par = 'mit_Sosal'
        temp_par = 'mit_Soxtemp'
        equ_temp_par = 'co2_equ temp'

        # Tequ = self.current_merge_data['co2_equ temp'].astype(float) + 273.15  # temp in Kelvin
        try:
            Tequ = np.array([as_float(item) for item in self.current_merge_data[equ_temp_par]]) + 273.15  # temp in Kelvin
        except:
            raise
        self.current_merge_data['calc_Tequ'] = Tequ

        Pequ = self.current_merge_data['calc_Pequ']
        # Pequ = self.current_merge_data['co2_equ press'].astype(float) + self.current_merge_data['co2_licor press'].astype(float)
        # Pequ is not in the same order as the previous calculated self.current_merge_data['calc_Pequ'] (has * 1e-3)

        VP_H2O = np.exp(24.4543 - 67.4509 * 100 / Tequ -
                        4.8489 * np.log(Tequ / 100) -
                        0.000544 * self.current_merge_data[salinity_par].astype(float))
        self.current_merge_data['calc_VP_H2O'] = VP_H2O

        pCO2 = self.current_merge_data['calc_xCO2'] * (Pequ / 1013.25 - VP_H2O) * np.exp(
            0.0423 * (self.current_merge_data[temp_par].astype(float) + 273.15 - Tequ))

        fCO2 = pCO2 * np.exp(((-1636.75 + 12.0408 * Tequ - 0.0327957 * Tequ ** 2 + 3.16528 * 1e-5 * Tequ ** 3)
                              + 2 * (1 - self.current_merge_data['calc_xCO2'] * 1e-6) ** 2 * (
                                      57.7 - 0.118 * Tequ)) * Pequ / 1013.25 / (82.0575 * Tequ))
        self.current_merge_data['calc_pCO2'] = pCO2
        self.current_merge_data['calc_fCO2 SST'] = fCO2


    def _get_pCO2_data_from_row(self, series):
        """
        Calculates xCO2 etc. for row or saves information needed to calculate pCO2.
        :param row_series: pandas.Series (row in df)
        :return:
        """
        return_dict = {'calc_k': np.nan,
                       'calc_m': np.nan,
                       'calc_xCO2': np.nan,
                       'calc_Pequ': np.nan,
                       'calc_pCO2 dry air': np.nan,
                       'calc_time_since_latest_std': np.nan}

        type_value = series['co2_Type']
        if type(type_value) == float and np.isnan(type_value):
            return return_dict
        co2_time = series['co2_time']
        co2_value = as_float(series['co2_CO2 um/m'])
        std_value = as_float(series['co2_std val'])

        # print('co2_equ press in series', 'co2_equ press' in series)       False
        # print('co2_licor press in series', 'co2_licor press' in series)   True

        equ_press_value = as_float(series['co2_equ press'])
        # equ_press_value = as_float(series['calc_Pequ'])
        licor_press_value = as_float(series['co2_licor press'])

        # print('-'*30)
        # print('SERIES')
        # print(series['co2_time'])
        # print(series['co2_source_file'])
        # print(series['mit_time'])
        # print(series['mit_source_file'])
        if not type_value:
            return dict()

        # Added by Johannes 2020-04-29
        if not hasattr(self, 'co2_time_list'):
            self.co2_time_list = []
        if not hasattr(self, 'std_val_list'):
            self.std_val_list = []
        if not hasattr(self, 'std_co2_list'):
            self.std_co2_list = []

        if 'STD' in type_value:
            if is_std(type_value):
                if co2_time in self.co2_time_list:
                    return dict()
                # print('¤'*40)
                # print('STD', type_value)
                # print(self.std_val_list)
                # This row should be saved for regression calculation
                self.co2_time_list.append(co2_time)
                self.std_val_list.append(std_value)
                self.std_co2_list.append(co2_value)
                self.std_latest_time = series['time']
                # print('STD: self.std_latest_time', self.std_latest_time)
                return dict()
            else:
                return dict()
        else:
            # Calculate/save constants if data is available
            if self.std_val_list:
                # print('self.std_latest_time', self.std_latest_time)
                # print()
                # print('¤'*40)
                # for t, st, co in zip(self.co2_time_list, self.std_val_list, self.std_co2_list):
                #     print(t, st, co)
                # print('-'*40)
                self._set_constants(self.std_val_list, self.std_co2_list, file_id=self.get_file_id(time=series['time'],
                                                                                                   file_type='co2'))
                # # Reset lists
                # self.std_val_list = []
                # self.std_co2_list = []

            if not self.pCO2_constants:
                self._set_constants_for_timestamp(series['time'])
                # return {'calc_pCO2 dry air': co2_value,
                #         'calc_xCO2': co2_value}

            # Reset lists
            self.co2_time_list = []
            self.std_val_list = []
            self.std_co2_list = []

            # Make calculations
            k = self.pCO2_constants['calc_k']  # k in y = kx + m
            m = self.pCO2_constants['calc_m']  # m in y = kx + m

            x = (co2_value - m) / k  # x in y = kx + m

            xCO2 = co2_value + (1 - k) * x + m
            # value = measured Value + correction (correction = diff between y = x and y = kx + m)

            Pequ = (equ_press_value + licor_press_value)
            # pressure due to EQU press and licor press

            pCO2_dry_air = xCO2 * Pequ * 1e-3

            # Check time since latest standard gas
            time_since_latest_std = np.nan
            if self.std_latest_time:
                time_since_latest_std = int(abs((self.std_latest_time - series['time']).total_seconds()))


            return_dict = {'calc_k': k,
                           'calc_m': m,
                           'calc_xCO2': xCO2,
                           'calc_Pequ': Pequ,
                           'calc_pCO2 dry air': pCO2_dry_air,
                           'calc_time_since_latest_std': time_since_latest_std}

            return return_dict

    def _set_constants(self, std_val_list=[], std_co2_list=[], file_id='', **kwargs):
        """
        Returns the constants from the regression calculated from standard gases.
        :return:
        """
        # if len(std_val_list) < 3:
        #     return
        try:
            # print('std_val_list', std_val_list, len(std_val_list)/3.)
            # print('std_co2_list', std_co2_list, len(std_co2_list)/3.)
            adapt = np.polyfit(np.array(std_val_list), np.array(std_co2_list), 1)
        except:
            # print('='*30)
            # print(file_id)
            # for val, co2 in zip(std_val_list, std_co2_list):
            #     print(val, co2, type(val), type(co2))
            raise
        self.pCO2_constants = dict(calc_k=adapt[0],
                                   calc_m=adapt[1],
                                   file_id=file_id)

    def _set_constants_for_timestamp(self, time_stamp):
        """
        Search in file or previous files to find closest STD rows. Sets constants and saves self.std_latest_time.
        :return:
        """
        data = self.get_std_basis_for_timestamp(time_stamp)
        self._set_constants(**data)
        self.std_latest_time = data.get('std_latest_time')

    def get_std_basis_for_timestamp(self, time_object):
        """
        Finds information of the most resent std gasses
        :param time_object:
        :return:
        """
        index_list = []
        file_id = self.get_file_id(time=time_object, file_type='co2')
        if not file_id:
            # Cannot find file id for the given time stamp. Need to find the latest file id.
            file_id = self.get_previous_file_id(time_stamp=time_object, file_type='co2')
        if not file_id:
            raise TavastlandExceptionNoCO2data('No CO2 file found for time {} or earlier!'.format(time_object))

        while file_id and not index_list:
            # print('=' * 40)
            # print('looking for get_std_basis_for_timestamp for time: {}'.format(time_object))
            # print('in file_id:', file_id)
            obj = self.objects['co2'][file_id]
            try:
                df = obj.get_df()
            except TavastlandExceptionCorrupedFile:
                continue
            df = df.loc[df['time'] <= time_object]
            for i in list(df.index)[::-1]:
                value = df.at[i, 'Type']
                if 'STD' in value:
                    if is_std(value):
                        index_list.append(i)
                elif index_list:
                    break
            if not index_list:
                # No STD values found
                # print('-', file_id)
                file_id = self.get_previous_file_id(file_id=file_id, file_type='co2')
                # print('-', file_id)

        index_list.reverse()
        # print(index_list)
        std_latest_time = df.at[index_list[-1], 'time']

        std_df = df.iloc[index_list, :]
        std_val_list = [as_float(item) for item in std_df['std val']]
        std_co2_list = [as_float(item) for item in std_df['CO2 um/m']]

        return_dict = dict(file_id=file_id,
                           std_latest_time=std_latest_time,
                           std_val_list=std_val_list,
                           std_co2_list=std_co2_list)
        return return_dict

    def get_types_in_merge_data(self):
        """
        Returns a list of types in loaded merged data
        :return:
        """
        merge_data = self.get_merge_data()
        all_types = sorted(set(merge_data['co2_Type']))
        if '' in all_types:
            all_types.pop(all_types.index(''))
        return all_types

    def save_data(self, directory=None, overwrite=False, **kwargs):
        self.save_dir = self._get_export_directory(directory)

        if os.path.exists(self.save_dir):
            if not overwrite:
                raise FileExistsError('One or more files exists. Set overwrite=True to overwrite package')

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        processed_file_path = self._save_merge_data(directory=self.save_dir, **kwargs)
        raw_mit_file_path = self._save_mit_data(directory=self.save_dir, **kwargs)
        raw_co2_file_path = self._save_co2_data(directory=self.save_dir, **kwargs)

        # Add comment to metadata
        if not self.metadata_added.get('merged_files'):
            mit_file_name = os.path.basename(raw_mit_file_path)
            co2_file_name = os.path.basename(raw_co2_file_path)
            time_string = self._get_time_string()
            self.metadata.append(';'.join(['COMMENT_MERGE', time_string, f'Data merged are in files: {mit_file_name} and {co2_file_name}']))
            self.metadata_added['merged_files'] = True

        # Add "time frozen" comment to metadata
        if not self.metadata_added.get('frozen_time'):
            self._add_frozen_time_comment()
            self.metadata_added['frozen_time'] = True

        # Write metadata file
        merge_file_base = os.path.basename(processed_file_path).split('.')[0]
        metadata_file_path = os.path.join(self.save_dir, f'metadata_{merge_file_base}.txt')
        self._save_metadata(metadata_file_path)

        return self.save_dir

    def _add_frozen_time_comment(self):
        for file_type, between in self.time_frozen_between.items():
            if not between:
                continue
            time_string = self._get_time_string()
            between_list = []
            for (f, t) in between:
                if f != '?':
                    f = pd.to_datetime(f).strftime('%Y%m%d%H%M%S')
                if t != '?':
                    t = pd.to_datetime(t).strftime('%Y%m%d%H%M%S')
                between_list.append(f'{f}-{t}')

            between_str = ','.join(between_list)

            self.metadata.append(';'.join(
                ['COMMENT_MERGE', time_string, f'In {file_type}-files time was frozen between: {between_str}']))

    def _get_time_string(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    def _get_save_dir_name(self):
        """
        Returns the directory name to save data in. Directory name is based on platform an time span.
        :return:
        """
        return '{}_{}'.format(self.package_prefix,
                              self._get_file_time_string())

    def _get_file_time_string(self):
        return '{}_{}'.format(self.current_time_start.strftime(
                              self.export_time_format_str),
                              self.current_time_end.strftime(
                              self.export_time_format_str))

    def _save_metadata(self, file_path):
        with open(file_path, 'w') as fid:
            for item in self.metadata:
                fid.write(f'{item}\n')

    def _save_mit_data(self, directory=None, **kwargs):
        """
        Saves mit data to file. The scope is the time span used for merging. e.i the time span +- time delta.
        :param directory:
        :param kwargs:
        :return:
        """
        df = self.current_data['mit']
        time_list = df['time'].values

        file_path = os.path.join(directory,
                                 'mit_{}_{}.txt'.format(pd.to_datetime(time_list[0]).strftime(self.export_time_format_str),
                                                           pd.to_datetime(time_list[-1]).strftime(self.export_time_format_str)))
        df.to_csv(file_path, sep='\t', index=False)

        return file_path


    def _save_co2_data(self, directory=None, **kwargs):
        """
        Saves co2 data to file. The scope is the time span used for merging. e.i the time span +- time delta.
        :param directory:
        :param kwargs:
        :return:
        """
        df = self.current_data['co2']
        time_list = df['time'].values

        file_path = os.path.join(directory,
                                 'co2_{}_{}.txt'.format(pd.to_datetime(time_list[0]).strftime(self.export_time_format_str),
                                                           pd.to_datetime(time_list[-1]).strftime(self.export_time_format_str)))
        df.to_csv(file_path, sep='\t', index=False)

        return file_path
        
    def _save_merge_data(self, directory=None, **kwargs):

        if not os.path.exists(directory):
            # Added by Johannes 2020-04-29
            os.makedirs(directory)

        file_path = os.path.join(directory, 'merge_{}_{}.txt'.format(self.package_prefix,
                                                                     self._get_file_time_string()))
        kw = dict(sep='\t',
                  index=False)
        merge_data = self.get_merge_data()

        self._mapp_columns(merge_data)

        # @Johannes 2020-04-29
        self._set_decimals(merge_data)

        if kwargs.get('co2_types'):
            boolean = merge_data['co2_Type'].isin(kwargs.get('co2_types'))
            merge_data.loc[boolean].to_csv(file_path, **kw)
        else:
            merge_data.to_csv(file_path, **kw)

        return file_path

    @staticmethod
    def _set_decimals(df):
        """
        @Johannes
        Temporary solution for setting number of decimals.
        Rather then using df.apply() we enhance performance with numpy.vectorize()
        :param df: pd.DataFrame
        :return: No return. We intend to change values df-changes(inplace=True)
        """
        def vectorize(x):
            if x:
                return round(x, 3)
            else:
                return x

        parameters = ['calc_Pequ', 'calc_Tequ', 'calc_VP_H2O', 'calc_fCO2 SST', 'calc_k', 'calc_m',
                      'calc_pCO2', 'calc_pCO2 dry air', 'calc_time_since_latest_std', 'calc_xCO2']
        for parameter in parameters:
            if parameter in df:
                if df[parameter].any():
                    df[parameter] = df[parameter].apply(as_float)
                    df[parameter] = np.vectorize(vectorize)(df[parameter])

    def _get_export_directory(self, directory=None):
        """
        Returns the export directory and creates it if non existing.
        :param directory:
        :return:
        """
        if not directory:
            directory = self.export_directory 
        
        if not directory:
            raise AttributeError('No export directory found or given')
        
        exp_directory = os.path.join(directory, self._get_save_dir_name())

        self.save_directory = exp_directory

        return exp_directory


class ManageTavastlandFiles(object):
    def __init__(self, directory):
        self.directory = directory
        self.files_id = 'tavastland'
        self.match_format = '\d{14}_\d{14}'

        self.mapping_files = MappingDirectory()
        self.mapping_file = self.mapping_files.get_path('mapping_tavastland.txt')
        self.col_files = 'nodc'
        self.col_qc0 = 'iocftp_number'

        self._load_directory()

    def _load_directory(self):
        self.dir_object = Directory(self.directory, match_string=self.files_id, match_format=self.match_format)

    def get_file_list(self):
        return self.dir_object.get_list()

    def list_files(self):
        print('Files in directory:')
        for file in self.get_file_list():
            print(f'   {file}')

    def _get_merge_file_path(self):
        for fname in self.get_file_list():
            if fname.startswith('merge_'):
                return self.dir_object.get_path(file_id=fname)

    def flag_areas(self):
        mask_areas_file_id = 'mask_areas_tavastland.txt'
        mask_files = MaskAreasDirectory()
        mask_obj = mask_files.get_file_object(mask_areas_file_id)
        data_file_path = self._get_merge_file_path()
        df = txt_reader.load_txt_df(data_file_path)

        mapping_files = sharkpylib.file.file_handlers.MappingDirectory()
        mapping_obj = mapping_files.get_file_object('mapping_tavastland.txt', from_col='co2_merged_file', to_col='nodc')

        lat_list = [float(value) for value in df[mapping_obj.get('lat', 'lat')]]
        lon_list = [float(value) for value in df[mapping_obj.get('lon', 'lon')]]
        boolean = mask_obj.get_masked_boolean(lat_list, lon_list)

        # Loop q columns
        for col in df.columns:
            if col.startswith('Q_'):
                df[col][boolean] = '4'

        df.to_csv(data_file_path, sep='\t', index=False)
        return data_file_path

    def create_qc0_file(self):
        qc0_file_path = mappinglib.create_file_for_qc0(file_path=self._get_merge_file_path(),
                                                       mapping_file_path=self.mapping_file,
                                                       file_col=self.col_files,
                                                       qc0_col=self.col_qc0,
                                                       save_file=True)
        return qc0_file_path

    def add_nodc_qc_columns(self):
        merge_file_path = self._get_merge_file_path()
        mappinglib.add_nodc_qc_columns_to_df(file_path=merge_file_path,
                                             save_file=True)
        return merge_file_path

    def add_qc0_info_to_nodc_column_file(self):
        merge_file_path = self._get_merge_file_path()
        mappinglib.merge_data_from_qc0(main_file_path=merge_file_path,
                                       mapping_file_path=self.mapping_file,
                                       file_col=self.col_files,
                                       qc0_col=self.col_qc0,
                                       save_file=True)
        return merge_file_path


def as_float(item):
    try:
        return float(item)
    except:
        return np.nan


def is_std(item):
    if not item.startswith('STD'):
        return False
    # Drain is acceptable as STD: 2019-11-20
    # if 'DRAIN' in item:
    #     return False
    if item[-1] in ['z', 's']:
        return False
    return True


logger = loglib.get_logger()