# -*- coding: utf-8 -*-
# Copyright (c) 2019 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import re
import codecs
import pandas as pd
import datetime
import numpy as np


class File(object):
    def __init__(self, file_path='', **kwargs):
        self.file_path = file_path

        self.df = pd.DataFrame()
        self.time_start = None
        self.time_end = None

        self.data_loaded = False

        if kwargs.get('load_file'):
            self.load_file()

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
        else:
            self.df['lat'] = np.nan
            self.df['lon'] = np.nan

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
            for line in fid:
                split_line = line.strip('\n\r').split(kwargs.get('sep', '\t'))
                split_line = [item.strip() for item in split_line]
                if not header:
                    header = split_line
                else:
                    if not self.valid_data_line(line):
                        continue
                    data.append(split_line)

        self.original_columns = header[:]
        self.df = pd.DataFrame(data, columns=header)

        self._add_columns()

        self.data_loaded = True

    def get_time_range(self):
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
                            self.time_start = get_time(data_line)
                self.time_end = get_time(data_line)
                # print('self.time_end', self.time_end, data_line)

        # print(self.time_end, self.file_path, r)
        return self.time_start, self.time_end

    def in_time_range(self, datetime_object):
        if not self.time_start:
            self.get_time_range()
        print(self.file_path)
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
        self.mit_directory = kwargs.get('mit_directory', None)
        self.co2_directory = kwargs.get('co2_directory', None)

        self.mit = dict()
        self.co2 = dict()

        if self.mit_directory is not None:
            self.set_mit_directory(self.mit_directory)

        if self.co2_directory is not None:
            self.set_co2_directory(self.co2_directory)

    def set_mit_directory(self, directory):
        """
        Saves path to mit-files in directory tree with root "directory"
        :param directory:
        :return:
        """
        mit_object = MITfile()
        self.mit = dict()
        for root, dirs, files in os.walk(directory):
            for name in files:
                if not mit_object.check_if_valid_file_name(name):
                    continue
                file_path = os.path.join(root, name)
                file_object = MITfile(file_path)
                start, end = file_object.get_time_range()
                self.mit[name] = dict(file_name=name,
                                      file_path=file_path,
                                      object=file_object,
                                      time_start=start,
                                      time_end=end)

    def set_co2_directory(self, directory):
        """
        Saves path to co2-files in directory tree with root "directory"
        :param directory:
        :return:
        """
        co2_object = CO2file()
        self.co2 = dict()
        for root, dirs, files in os.walk(directory):
            for name in files:
                if not co2_object.check_if_valid_file_name(name):
                    continue
                file_path = os.path.join(root, name)
                file_object = CO2file(file_path)
                start, end = file_object.get_time_range()
                self.co2[name] = dict(file_name=name,
                                      file_path=file_path,
                                      object=file_object,
                                      time_start=start,
                                      time_end=end)






