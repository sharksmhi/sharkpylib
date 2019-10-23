# -*- coding: utf-8 -*-
# Copyright (c) 2019 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import re
import codecs

import datetime
import time
import numpy as np
from .. import loglib
from .. import mappinglib
from .. import exceptionlib

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

# ==============================================================================
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

# ==============================================================================
class TavastlandExceptionNoCO2data(TavastlandException):
    """
    """
    code = ''
    message = ''

# ==============================================================================
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

        self.data_loaded = False

        self.time_in_file_name_formats = ['TP_%Y%m%d%H%M%S.mit']
        self._add_file_path_time()

        if kwargs.get('load_file'):
            self.load_file()

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
        # Log().information('Loading file: {}'.format(self.file_path))

        header = []
        data = []
        with codecs.open(self.file_path, encoding=kwargs.get('encoding', 'cp1252')) as fid:
            for row, line in enumerate(fid):
                split_line = line.strip('\n\r').split(kwargs.get('sep', '\t'))
                split_line = [item.strip() for item in split_line]
                if not header:
                    header = split_line
                else:
                    if not self.valid_data_line(line):
                        logger.warning('Removing invalid line {} from file: {}'.format(row, self.file_path))
                        continue
                    data.append(split_line)

        self.original_columns = header[:]
        self.df = pd.DataFrame(data, columns=header)
        self._add_columns()
        self.filter_data()
        self._delete_columns()
        self.data_loaded = True

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
        self.df = self.df.loc[combined_keep_boolean]

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
        if not self.data_loaded:
            self.load_file()
        export_file_path = os.path.join(export_directory, self.file_name)
        self.df[self.original_columns].to_csv(export_file_path, index=False, sep='\t')

    def get_df(self):
        if not len(self.df):
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

    def errors(self):
        """
        Returns a list of errors in file if any. Errors are obvious faults that can not be handled.
        :return list with description of the errors.
        """
        raise NotImplementedError


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

    def errors(self):
        """
        Returns a list of errors in file if any. Errors are obvious faults that can not be handled.
        :return list with description of the errors.
        """
        error_list = []
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
            logger.info(text.join('; '))

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

    def errors(self):
        """
        Returns a list of errors in file if any. Errors are obvious faults that can not be handled.
        :return list with description of the errors.
        """
        error_list = []
        # Check time
        start, end = self.get_time_range()
        d = datetime.datetime(1980, 1, 1)
        this_year = datetime.datetime.now().year

        if not all([start, end]):
            text = 'Could not find time in file {}.'.format(self.file_name)
            error_list.append(text)

        if error_list:
            logger.info(text.join('; '))

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

        self.df_header = ['file_id', 'file_path', 'time_start', 'time_end']

        self.export_time_format_str = '%Y%m%d%H%M%S'

        self.file_prefix = 'ferrybox-tavastland'

        self.objects = dict()
        self.dfs = dict()

        self.files_with_errors = dict()

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

        self.objects[file_type] = dict()
        data_lines = []
        for root, dirs, files in os.walk(directory):
            for name in files:
                if not file_type_object.check_if_valid_file_name(name):
                    continue
                file_path = os.path.join(root, name)
                file_object = File_type_class(file_path)
                start, end = file_object.get_time_range()

                errors = file_object.errors()
                if errors:
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

        print('Load data')
        print('mit', len(self.current_data['mit']))
        print('co2', len(self.current_data['co2']))
        print('Loaded in: {}'.format(time.time()-t0))

    def reset_data(self):
        self.current_data = {}
        self.current_merge_data = pd.DataFrame()
        self.pCO2_constants = {}
        self.std_val_list = []
        self.std_co2_list = []
        self.std_latest_time = None

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
        object_dict = self.objects.get(file_type)
        file_id_list = self.get_file_ids_within_time_range(file_type, time_start, time_end)
        df = pd.DataFrame()
        for file_id in file_id_list:
            if file_id in self.files_with_errors:
                logger.warning('Discarding file {}. File has errors!'.format(file_id))
                continue
            df = df.append(object_dict.get(file_id).get_df())

        if not len(df):
            raise TavastlandExceptionNoCO2data('No data in time range {} - {}'.format(time_start, time_end))
        else:
            df.sort_values('time', inplace=True)

        # Add file type to header
        df.columns = ['{}_{}'.format(file_type, item) for item in df.columns]
        df['time'] = df['{}_time'.format(file_type)]

        # Strip dates
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

    def _sort_merge_data_columns(self):
        columns = sorted(self.current_merge_data.columns)
        columns.pop(columns.index('time'))
        columns.pop(columns.index('lat'))
        columns.pop(columns.index('lon'))
        new_columns = ['time', 'lat', 'lon'] + columns
        self.current_merge_data = self.current_merge_data[new_columns]

    def remove_areas(self, file_path):
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

    def map_header_like_iocftp(self):
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

    def map_header_like_internal(self):
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

    def _calculate_pCO2(self):

        salinity_par = 'mit_Sosal'
        temp_par = 'mit_Soxtemp'
        equ_temp_par = 'co2_equ_temp'

        # Tequ = self.current_merge_data['co2_equ temp'].astype(float) + 273.15  # temp in Kelvin
        Tequ = np.array([as_float(item) for item in self.current_merge_data[equ_temp_par]]) + 273.15  # temp in Kelvin
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
        equ_press_value = as_float(series['co2_equ press'])
        licor_press_value = as_float(series['co2_licor press'])

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
                return dict()
            else:
                return dict()
        else:
            # Calculate/save constants if data is available
            if self.std_val_list:
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

            pCO2_dry_air = xCO2 * Pequ

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
        # print('#'*30)
        # print('std_val_list', std_val_list)
        # print('std_co2_list', std_co2_list)
        # print(file_id)
        adapt = np.polyfit(np.array(std_val_list), np.array(std_co2_list), 1)
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
            df = obj.get_df()
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
        types = []
        for item in merge_data['co2_Type']:
            if type(item) == str:
                types.append(item)
        return sorted(set(types))

    def save_mit_data(self, directory=None, **kwargs):
        """
        Saves mit data to file. The scope is the time span used for merging. e.i the time span +- time delta.
        :param directory:
        :param kwargs:
        :return:
        """
        directory = self._get_export_directory(directory)
        df = self.current_data['mit']
        time_list = df['time'].values

        file_path = os.path.join(directory,
                                 'mit_{}_{}_{}.txt'.format(self.file_prefix,
                                                           pd.to_datetime(time_list[0]).strftime(self.export_time_format_str),
                                                           pd.to_datetime(time_list[-1]).strftime(self.export_time_format_str)))
        df.to_csv(file_path, sep='\t', index=False)


    def save_co2_data(self, directory=None, **kwargs):
        """
        Saves co2 data to file. The scope is the time span used for merging. e.i the time span +- time delta.
        :param directory:
        :param kwargs:
        :return:
        """
        directory = self._get_export_directory(directory)
        df = self.current_data['co2']
        time_list = df['time'].values

        file_path = os.path.join(directory,
                                 'co2_{}_{}_{}.txt'.format(self.file_prefix,
                                                           pd.to_datetime(time_list[0]).strftime(self.export_time_format_str),
                                                           pd.to_datetime(time_list[-1]).strftime(self.export_time_format_str)))
        df.to_csv(file_path, sep='\t', index=False)


    def save_merge_data(self, directory=None, **kwargs):

        directory = self._get_export_directory(directory)

        file_path = os.path.join(directory, 'merge_{}_{}_{}.txt'.format(self.file_prefix,
                                                                        self.current_time_start.strftime(
                                                                            self.export_time_format_str),
                                                                          self.current_time_end.strftime(
                                                                              self.export_time_format_str)))
        kw = dict(sep='\t',
                  index=False)
        merge_data = self.get_merge_data()

        if kwargs.get('co2_types'):
            boolean = merge_data['co2_Type'].isin(kwargs.get('co2_types'))
            merge_data.loc[boolean].to_csv(file_path, **kw)
        else:
            merge_data.to_csv(file_path, **kw)

        return file_path

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

        if not os.path.exists(directory):
            os.makedirs(directory)

        return directory


class MergeIOCFTPfile(object):
    def __init__(self, iocftp_file_path=None, data_file_path=None, **kwargs):
        """
        Class to merge (and save) an iocftp file with its original data.
        Time span and "name" must be the same in the two file names. Time is checked in files so that they match.
        :param iocftp_df:
        :param df:
        """
        assert iocftp_file_path
        assert data_file_path

        self.iocftp_file_path = iocftp_file_path
        self.data_file_path = data_file_path

        self._check_files()

        self._load_files()
        self._merge_files()

        save_file = kwargs.pop('save_file', None)
        save_directory = kwargs.pop('save_directory', None)

        if save_file:
            self.save_merged_file(directory=save_directory)

    def _check_files(self):
        iocftp_parts = self.iocftp_file_path.split('_')
        data_parts = self.data_file_path.split('_')
        if not (iocftp_parts[-1] == data_parts[-1]) & (iocftp_parts[-2] == data_parts[-2]):
            raise exceptionlib.NonMatchingInformation('Timestamps are not the same in the given files')

    def _load_files(self):
        self.df_iocftp = pd.read_csv(self.iocftp_file_path, sep='\t')
        self.df_data = pd.read_csv(self.data_file_path, sep='\t')

        if len(self.df_iocftp) != len(self.df_data):
            raise exceptionlib.NonMatchingData('Files ar of different length')

    def _merge_files(self):
        """
        Combines files and add a QC0 column
        :return:
        """
        mapping_directory_object = mappinglib.MappingDirectory()
        platform_mapping_object = mapping_directory_object.get_mapping_object('mapping_iocftp_platforms')
        parameter_mapping_object = mapping_directory_object.get_mapping_object('mapping_tavastland')

        # IOCFTP prep
        mapped_iocftp_columns = []
        for col in self.df_iocftp.columns[:]:
            if len(col) == 5:
                # QC column
                mapped_col = parameter_mapping_object.get(col[1:], 'iocftp_number', 'co2_merged_file')
                col_name = 'QC0_{}'.format(mapped_col)
            elif len(col) == 4:
                col_name = parameter_mapping_object.get(col[1:], 'iocftp_number', 'co2_merged_file')
            else:
                # Platform number
                col_name = 'time'
            mapped_iocftp_columns.append(col_name)

        self.df_iocftp.columns = mapped_iocftp_columns

        # DATA prep
        self.df_merged = self.df_data.copy().fillna('').astype(str)
        # Create QC0 columns
        added_columns = []
        parent_added_column = []
        updated_data_columns_order = []
        qc0_flag_series = np.zeros(len(self.df_merged)).astype(int).astype(str)
        for col in self.df_merged.columns:
            updated_data_columns_order.append(col)
            qc0_col = 'QC0_{}'.format(col)
            updated_data_columns_order.append(qc0_col)
            parent_added_column.append(col)
            added_columns.append(qc0_col)

        # Add columns
        for col, parent_col in zip(added_columns, parent_added_column):
            boolean = self.df_merged[parent_col] == ''
            add_series = qc0_flag_series.copy()
            add_series[boolean] = ''  # Check if this should be included
            self.df_merged[col] = add_series

        # Set column order
        self.df_merged = self.df_merged[updated_data_columns_order]

        # COMBINE
        for col in self.df_merged.columns:
            if col in self.df_iocftp.columns:
                self.df_merged[col] = self.df_iocftp[col]

    def save_merged_file(self, directory=None):
        """
        If directory is not given the file is saved in tha same directory as the data file.
        File name is set according to data_file_name.
        :param directory:
        :return:
        """
        if directory is None:
            directory = os.path.dirname(self.data_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        data_file_name = os.path.basename(self.data_file_path)

        file_name = 'QC0_{}'.format(data_file_name)
        file_path = os.path.join(directory, file_name)
        self.df_merged.to_csv(file_path, sep='\t', index=False)


def as_float(item):
    try:
        return float(item)
    except:
        return np.nan

def is_std(item):
    if not item.startswith('STD'):
        return False
    if 'DRAIN' in item:
        return False
    if item[-1] in ['z', 's']:
        return False
    return True


logger = loglib.get_logger()