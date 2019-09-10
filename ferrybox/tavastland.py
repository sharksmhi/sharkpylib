# -*- coding: utf-8 -*-
# Copyright (c) 2019 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import re
import codecs
import pandas as pd
import datetime
import numpy as np
import logger

import sys
parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_directory not in sys.path:
    sys.path.append(parent_directory)
import gismo


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


class File(object):
    def __init__(self, file_path='', **kwargs):
        self.file_path = file_path
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

    def _add_columns(self):
        # Time
        if 'Date' in self.df.columns:
            self.df['time_str'] = self.df['Date'] + ' ' + self.df['Time']
            self.df['time'] = pd.to_datetime(self.df['time_str'], format='%d.%m.%Y %H:%M:%S')
        elif 'PC Date' in self.df.columns:
            self.df['time_str'] = self.df['PC Date'] + ' ' + self.df['PC Time']
            self.df['time'] = pd.to_datetime(self.df['time_str'], format='%d/%m/%y %H:%M:%S')

        # Position
        if 'Lat' in self.df.columns:
            self.df['lat'] = self.df['Lat'].astype(float)
            self.df['lon'] = self.df['Lon'].astype(float)
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

        self.data_loaded = True

    def filter_data(self):
        """
        Filters the data from unwanted lines etc.
        :return:
        """
        # remove_boolean = pd.to_datetime(self.df['time']) == datetime.datetime(1904, 1, 1)
        if self.file_path_time:
            time_delta = datetime.timedelta(days=365)
            remove_before_datetime = self.file_path_time - time_delta
            remove_after_datetime = self.file_path_time + time_delta
            time_array = pd.to_datetime(self.df['time'])
            keep_boolean = (time_array >= remove_before_datetime) & (time_array <= remove_after_datetime)
            removed = self.df.loc[~keep_boolean]
            if len(removed):
                logger.warning('{} lines removed from file {}'.format(len(removed), self.file_path))
            self.df = self.df.loc[keep_boolean]

    def get_df(self):
        if not len(self.df):
            self.load_file()
        return self.df

    def old_get_time_range(self):
        def get_time(line):
            date = re.findall('\d{2}\.\d{2}\.\d{4}', line)
            time = re.findall('\d{2}:\d{2}:\d{2}', line)
            if date and time:
                return datetime.datetime.strptime(date[0]+time[0], '%d.%m.%Y%H:%M:%S')

            date = re.findall('\d{2}/\d{2}/\d{2}', line)
            time = re.findall('\d{2}:\d{2}:\d{2}', line)
            if date and time:
                return datetime.datetime.strptime(date[0] + time[0], '%d/%m/%y%H:%M:%S')

        self.time_start = None
        self.time_end = None
        timedelta = datetime.timedelta(weeks=1)
        if self.data_loaded:
            self.time_start = self.df.time.values[0]
            self.time_end = self.df.time.values[-1]
            return self.time_start, self.time_end
        else:
            with codecs.open(self.file_path) as fid:
                for r, line in enumerate(fid):
                    if self.valid_data_line(line):
                        data_line = line
                        if r == 0:
                            continue
                        time = get_time(data_line)
                        if self.file_path_possible_years:
                            if time.year not in self.file_path_possible_years:
                                continue
                        if not self.time_start:
                            self.time_start = time
                        self.time_end = time

        # print(self.time_end, self.file_path, r)
        return self.time_start, self.time_end

    def older_get_time_range(self):
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
                        data_line = line
                        if r == 0:
                            continue
                        elif not self.time_start:
                            time = get_time(data_line)
                            if self.file_path_time:
                                if (time + datetime.timedelta(1)) >= self.file_path_time:
                                    # print('time', datetime.timedelta(1), time, (time + datetime.timedelta(60*60*24)), self.file_path_time)
                                    self.time_start = time
                            else:
                                self.time_start = time
                self.time_end = get_time(data_line)
                # print('self.time_end', self.time_end, data_line)

        # print(self.time_end, self.file_path, r)
        return self.time_start, self.time_end

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

    def has_warnings(self):
        """
        Returns True if something strange is in file. Strange things kan be handled.
        :return:
        """
        raise NotImplementedError

    def has_errors(self):
        """
        Returns True if error in file. Errors ar obvious faults that can not be handled.
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

    def has_errors(self):
        # Check time
        start, end = self.get_time_range()
        if start < datetime.datetime(1980, 1, 1):
            return True


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


class FileHandler(object):
    def __init__(self, **kwargs):
        global logger
        logger = logger.get_logger(**kwargs.get('log_info', {}))
        logger.debug('Starting FileHandler for Tavastland')
        self.directories = {}
        self.directories['mit'] = kwargs.get('mit_directory', None)
        self.directories['co2'] = kwargs.get('co2_directory', None)

        self.export_directory = kwargs.get('export_directory', None)

        self.df_header = ['file_id', 'file_path', 'time_start', 'time_end']

        self.objects = dict()
        self.dfs = dict()

        self.files_with_errors = dict()

        self.reset_time_range()
        self.reset_data()

        self.set_time_delta(seconds=30)

        for file_type, directory in self.directories.items():
            if directory:
                self.set_directory(file_type, directory)

        # if self.mit_directory is not None:
        #     self.set_mit_directory(self.mit_directory)
        #
        # if self.co2_directory is not None:
        #     self.set_co2_directory(self.co2_directory)

    def set_directory(self, file_type, directory):
        """
        Saves path to files with the given directory for the given file_type
        :param file_type:
        :return:
        """
        this_year = datetime.datetime.now().year
        if file_type == 'mit':
            file_type_object = MITfile()
        elif file_type == 'co2':
            file_type_object = CO2file()

        self.files_with_errors[file_type] = set()

        self.objects[file_type] = dict()
        data_lines = []
        for root, dirs, files in os.walk(directory):
            for name in files:
                if not file_type_object.check_if_valid_file_name(name):
                    continue
                file_path = os.path.join(root, name)
                file_object = MITfile(file_path)
                start, end = file_object.get_time_range()
                if not all([start, end]):
                    logger.error('Could not find time in file {}.'.format(name))
                    self.files_with_errors[file_type].add(name)
                    # continue
                elif start > end:
                    logger.error('Start time > end time in file {}.'.format(name))
                    self.files_with_errors[file_type].add(name)
                    # continue
                elif any([start.year > this_year, end.year > this_year]):
                    logger.error('Start year or end year is later than current year in file {}.'.format(name))
                    self.files_with_errors[file_type].add(name)
                    # continue
                elif any([start.year == 1904, end.year == 1904]):
                    logger.error('Start year or end year is 1904 in file {}.'.format(name))
                    self.files_with_errors[file_type].add(name)
                    # continue
                data_lines.append([name, file_path, start, end])
                self.objects[file_type][name] = file_object
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
                raise AttributeError('Several files matches time stamp: {}'.format('\n'.join(list(result))))
            else:
                return result[0]
        else:
            raise AttributeError('Missing')

    def get_pervious_file_id(self, file_id, file_type='mit'):
        """
        Returns the previous file_id
        :param file_id:
        :return:
        """
        df = self.dfs.get(file_type)
        if file_id in df['file_id'].values:
            index = df.index[df['file_id'] == file_id][0]
            if index == 0:
                return None
            else:
                return df.at[index-1, 'file_id']


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
        if not all([self.current_time_start, self.current_time_end]):
            raise Exception

        self.reset_data()

        # Load files within time range
        self.current_data['mit'] = self.get_data_within_time_range('mit', self.current_time_start, self.current_time_end)
        self.current_data['co2'] = self.get_data_within_time_range('co2', self.current_time_start, self.current_time_end)

    def reset_data(self):
        self.current_data = {}
        self.current_merge_data = pd.DataFrame()
        self.pCO2_constants = {}
        self.std_val_list = []
        self.std_co2_list = []
        self.std_latest_time = None

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
            raise TavastlandExceptionNoCO2data('in time range {} - {}'.format(time_start, time_end))
        else:
            df.sort_values('time', inplace=True)

        df.columns = ['{}_{}'.format(file_type, item) for item in df.columns]
        df['time'] = df['{}_time'.format(file_type)]

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

    def merge_data(self, left='mit', right='co2'):
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

        self.current_merge_data = pd.merge_asof(self.current_data[left], self.current_data[right],
                                                on='time',
                                                tolerance=self.time_delta,
                                                direction='nearest')

        # Add time par (based on left df)
        self.current_merge_data['time'] = self.current_merge_data['{}_time'.format(left)]

        # Add diffs
        self.current_merge_data['diff_time'] = abs(self.current_merge_data['{}_time'.format(left)] - \
                                               self.current_merge_data['{}_time'.format(right)])

        self.current_merge_data['diff_lat'] = self.current_merge_data['{}_lat'.format(left)] - \
                                               self.current_merge_data['{}_lat'.format(right)]

        self.current_merge_data['diff_lon'] = self.current_merge_data['{}_lon'.format(left)] - \
                                               self.current_merge_data['{}_lon'.format(right)]

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

    def calculate_pCO2(self):
        """
        Calculates pCO2 on self.current_merge_data
        :return:
        """
        self.current_merge_data['k'] = np.nan
        self.current_merge_data['m'] = np.nan
        self.current_merge_data['Pequ'] = np.nan
        self.current_merge_data['pCO2 dry air'] = np.nan

        self.current_merge_data['xCO2'] = np.nan
        self.current_merge_data['pCO2'] = np.nan

        items = ['k', 'm', 'xCO2', 'Pequ', 'pCO2 dry air', 'time_since_latest_std']
        for i in self.current_merge_data.index:
            values = self._get_pCO2_data_from_row(self.current_merge_data.iloc[i])
            for key in items:
                self.current_merge_data.at[i, key] = values.get(key, np.nan)

            # self.current_merge_data.at[i, 'k'] = values.get('k', np.nan)
            # self.current_merge_data.at[i, 'm'] = values.get('m', np.nan)
            # self.current_merge_data.at[i, 'Pequ'] = values.get('Pequ', np.nan)
            # self.current_merge_data.at[i, 'pCO2 dry air'] = values.get('pCO2 dry air', np.nan)
            # self.current_merge_data.at[i, 'xCO2'] = values.get('xCO2', np.nan)

        self._calculate_pCO2()

    def _calculate_pCO2(self):

        salinity_par = 'mit_Sosal'
        temp_par = 'mit_Soxtemp'

        # Tequ = self.current_merge_data['co2_equ temp'].astype(float) + 273.15  # temp in Kelvin
        Tequ = np.array([as_float(item) for item in self.current_merge_data['co2_equ temp']]) + 273.15  # temp in Kelvin
        self.current_merge_data['Tequ'] = Tequ

        Pequ = self.current_merge_data['co2_equ press'].astype(float) + self.current_merge_data['co2_licor press'].astype(float)
        # Pequ is not in the same order as the privious cualculated self.current_merge_data['Pequ'] (has * 1e-3)

        VP_H2O = np.exp(24.4543 - 67.4509 * 100 / Tequ -
                        4.8489 * np.log(Tequ / 100) -
                        0.000544 * self.current_merge_data[salinity_par].astype(float))
        self.current_merge_data['VP_H2O'] = VP_H2O

        pCO2 = self.current_merge_data['xCO2'] * (Pequ / 1013.25 - VP_H2O) * np.exp(
            0.0423 * (self.current_merge_data[temp_par].astype(float) + 273.15 - Tequ))

        fCO2 = pCO2 * np.exp(((-1636.75 + 12.0408 * Tequ - 0.0327957 * Tequ ** 2 + 3.16528 * 1e-5 * Tequ ** 3)
                              + 2 * (1 - self.current_merge_data['xCO2'] * 1e-6) ** 2 * (
                                      57.7 - 0.118 * Tequ)) * Pequ / 1013.25 / (82.0575 * Tequ))
        self.current_merge_data['pCO2'] = pCO2
        self.current_merge_data['fCO2 SST'] = fCO2


    def _get_pCO2_data_from_row(self, series):
        """
        Calculates pCO2 for row or saves information needed to calculate pCO2.
        :param row_series: pandas.Series (row in df)
        :return:
        """
        type_value = series['co2_Type']
        co2_value = as_float(series['co2_CO2 um/m'])
        std_value = as_float(series['co2_std val'])
        equ_press_value = as_float(series['co2_equ press'])
        licor_press_value = as_float(series['co2_licor press'])

        if 'STD' in type_value:
            if is_std(type_value):
                # This row should be saved for regression calculation
                self.std_val_list.append(std_value)
                self.std_co2_list.append(co2_value)
                self.std_latest_time = series['time']
                return dict()
            else:
                return dict()
        else:
            # Calculate/save constants if data is available
            if self.std_val_list:
                self._set_constants(self.std_val_list, self.std_co2_list, file_id=self.get_file_id(time=series['time'],
                                                                                                   file_type='co2'))

                # Reset lists
                self.std_val_list = []
                self.std_co2_list = []

            if not self.pCO2_constants:
                self._set_constants_for_timestamp(series['time'])
                # return {'pCO2 dry air': co2_value,
                #         'xCO2': co2_value}

            # Make calculations
            k = self.pCO2_constants['k']  # k in y = kx + m
            m = self.pCO2_constants['m']  # m in y = kx + m

            x = (co2_value - m) / k  # x in y = kx + m

            xCO2 = co2_value + (1 - k) * x + m
            # value = measured Value + correction (correction = diff between y = x and y = kx + m)

            Pequ = (equ_press_value + licor_press_value) * 1e-3  # 1e-3
            # pressure due to EQU press and licor press

            pCO2_dry_air = xCO2 * Pequ

            # Check time since latest standard gas
            time_since_latest_std = np.nan
            if self.std_latest_time:
                time_since_latest_std = abs(self.std_latest_time - series['time'])


            return_dict = {'k': k,
                           'm': m,
                           'xCO2': xCO2,
                           'Pequ': Pequ,
                           'pCO2 dry air': pCO2_dry_air,
                           'time_since_latest_std': time_since_latest_std}

            return return_dict

    def _set_constants(self, std_val_list=[], std_co2_list=[], file_id='', **kwargs):
        """
        Returns the konstants from the regression calculated from standard gases.
        :return:
        """
        # print('std_val_list', std_val_list)
        # print('std_co2_list', std_co2_list)
        adapt = np.polyfit(np.array(std_val_list), np.array(std_co2_list), 1)
        self.pCO2_constants = dict(k=adapt[0],
                                   m=adapt[1],
                                   file_id=file_id)

    def _set_constants_for_timestamp(self, time_stamp):
        """
        Search in file or previous files to find cloasest STD rows. Sets constants and saves self.std_latest_time.
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
        while file_id and not index_list:
            print('=' * 40)
            print('file_id:', file_id)
            obj = self.objects['co2'][file_id]
            df = obj.get_df()
            df = df.loc[df['time'] <= time_object]
            for i in list(df.index)[::-1]:
                value = df.at[i, 'Type']
                if 'STD' in value:
                    index_list.append(i)
                elif index_list:
                    break
            if not index_list:
                # No STD values found
                print('-', file_id)
                file_id = self.get_pervious_file_id(file_id, file_type='co2')
                print('-', file_id)

        index_list.reverse()
        print(index_list)
        std_latest_time = df.at[index_list[-1], 'time']

        std_df = df.iloc[index_list, :]
        std_val_list = [as_float(item) for item in std_df['CO2 um/m']]
        std_co2_list = [as_float(item) for item in std_df['std val']]

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
        return sorted(set(merge_data['co2_Type']))

    def save_merge_data(self, directory=None, **kwargs):
        if not directory:
            directory = self.export_directory

        if not directory:
            raise AttributeError('No export directory found or given')

        if not os.path.exists(directory):
            os.makedirs(directory)

        time_format_str = '%Y%m%d%H%M%S'
        file_path = os.path.join(directory, 'merge_data_{}_{}.txt'.format(self.current_time_start.strftime(
                                                                              time_format_str),
                                                                          self.current_time_end.strftime(
                                                                              time_format_str)))
        kw = dict(sep='\t',
                  index=False)
        merge_data = self.get_merge_data()

        if kwargs.get('co2_types'):
            boolean = merge_data['co2_Type'].isin(kwargs.get('co2_types'))
            merge_data.loc[boolean].to_csv(file_path, **kw)
        else:
            merge_data.to_csv(file_path, **kw)



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


logger = logger.get_logger()