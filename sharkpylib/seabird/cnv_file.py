from pathlib import Path
import datetime

from sharkpylib.seabird.file import SeabirdFile
from sharkpylib.seabird.patterns import get_cruise_match_dict

from sharkpylib.seabird import xmlcon_parser


class HeaderName:
    _string = None
    _index = None
    _code = None
    _parameter = None

    def __init__(self, string):
        self._string = string.strip()
        self._save_info()

    def __str__(self):
        return self._string

    def __repr__(self):
        return self.__str__()

    def _save_info(self):
        split_line = self._string.split('=', 1)
        self._index = int(split_line[0].strip().split()[-1])
        split_par = split_line[1].split(':')
        self._code = split_par[0].strip()
        self._parameter = split_par[1].strip()

    @property
    def index(self):
        return self._index

    @property
    def code(self):
        return self._code

    @property
    def parameter(self):
        return self._parameter


class Header:
    def __init__(self, linebreak='\n'):
        self.linebreak = linebreak
        self.rows = []

    def add_row(self, row):
        self.rows.append(row.strip())

    # def insert_row_after(self, row, after_str, ignore_if_string=None):
    #     for line in self.rows:
    #         if row == line:
    #             return
    #     for i, value in enumerate(self.rows[:]):
    #         if after_str in value:
    #             if ignore_if_string:
    #                 if ignore_if_string in self.rows[i+1]:
    #                     continue
    #             self.rows.insert(i+1, row.strip())
    #             break
    #
    # def append_to_row(self, string_in_row, append_string):
    #     for i, value in enumerate(self.rows[:]):
    #         if string_in_row in value:
    #             new_string = self.rows[i] + append_string.rstrip()
    #             if self.rows[i] == new_string:
    #                 continue
    #             self.rows[i] = new_string
    #             break
    #
    # def get_row_index_for_matching_string(self, match_string, as_list=False):
    #     index = []
    #     for i, value in enumerate(self.rows):
    #         if match_string in value:
    #             index.append(i)
    #     if not index:
    #         return None
    #     if as_list:
    #         return index
    #     if len(index) == 1:
    #         return index[0]
    #     return index
    #
    # def replace_string_at_index(self, index, from_string, to_string, ignore_if_present=True):
    #     if index is None:
    #         return
    #     if type(index) == int:
    #         index = [index]
    #     for i in index:
    #         if to_string in self.rows[i] and ignore_if_present:
    #             continue
    #         self.rows[i] = self.rows[i].replace(from_string, to_string)
    #
    # def replace_row(self, index, new_value):
    #     self.rows[index] = new_value.strip()


class Parameter:
    def __init__(self, use_cnv_info_format=False, cnv_info_object=None, index=None, name=None):
        self.index = index
        self.name = name

        self.info = {}
        self.use_cnv_info_format = use_cnv_info_format
        self.cnv_info_object = cnv_info_object
        self._tot_value_length = 11
        self._value_format = 'd'
        self._nr_decimals = None
        self.sample_value = None
        self._data = []
        self.active = False

    def __repr__(self):
        return_list = [f'CNVparameter (dict): {self.info["name"]}']
        blanks = ' '*4
        for key, value in self.info.items():
            return_list.append(f'{blanks}{key:<20}{value}')

        if len(self._data):
            return_list.append(f'{blanks}{"Sample value":<20}{self.sample_value}')
            if self.use_cnv_info_format:
                form = f'{self.format} (from info file)'
            else:
                form = f'{self.format} (calculated from data)'
            return_list.append(f'{blanks}{"Value format":<20}{form}')
        return '\n'.join(return_list)

    def _set_nr_decimals(self, value_str):
        # Keeps the highest number och decimals in self._nr_decimals
        # Also saves sample_value
        if self._nr_decimals is None:
            self._nr_decimals = len(value_str.strip().split('e')[0].split('.')[-1])
            self.sample_value = float(value_str)
        else:
            nr = len(value_str.strip().split('e')[0].split('.')[-1])
            if nr > self._nr_decimals:
                self._nr_decimals = nr
                self.sample_value = float(value_str)

    @property
    def format(self):
        if self.use_cnv_info_format:
            return self.cnv_info_object.format
        if self._nr_decimals is None:
            form = f'{self._tot_value_length}{self._value_format}'
        else:
            form = f'{self._tot_value_length}.{self._nr_decimals}{self._value_format}'
        return form

    def set_value_length(self, length):
        self._tot_value_length = length

    def add_data(self, value_str):
        string = value_str.strip('+-')
        if '+' in string or '-' in string:
            self._value_format = 'e'
        elif '.' in value_str:
            self._value_format = 'f'
        if '.' in value_str:
            self._set_nr_decimals(value_str)
            value = float(value_str)
        else:
            value = int(value_str)
            self._value_format = 'd'

        self._data.append(value)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def change_name(self, new_name):
        self.info['name'] = new_name
        self.name = new_name

    def get_value_as_string_for_index(self, index):
        return '{:{}}'.format(self.data[index], self.format)

    def set_active(self, is_active):
        self.active = is_active


class Cnvfile(SeabirdFile):
    suffix = '.cnv'
    header_date_format = '%b %d %Y %H:%M:%S'
    _header_datetime = None
    _header_lat = None
    _header_lon = None
    _header_station = None
    _header_form = None
    _header_names = None
    _header_cruise_info = None
    _xml_tree = None
    _parameters = {}
    _sensor_info = None

    @property
    def datetime(self):
        return self._header_datetime or self._get_datetime_from_path()

    def _save_attributes(self):
        self._attributes.update(self._header_cruise_info)
        self._attributes['date'] = self.datetime.strftime('%Y%m%d')
        self._attributes['time'] = self.datetime.strftime('%H%M')
        self._attributes['lat'] = self._header_lat
        self._attributes['lon'] = self._header_lon
        self._attributes['station'] = self._header_station
        self._attributes['sensor_info'] = self._sensor_info

    def _save_info_from_file(self):
        self._header_form = {'info': []}
        self._header_names = []
        self._nr_data_lines = 0
        self._header_rows = Header()
        self._parameters = {}
        self._header_cruise_info = {}

        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>\n']
        is_xml = False

        header = True
        has_set_value_length = False
        with open(self.path) as fid:
            for line in fid:
                strip_line = line.strip()

                # General header info
                if line.startswith('* System UTC'):
                    self._header_datetime = datetime.datetime.strptime(line.split('=')[1].strip(), self.header_date_format)
                elif line.startswith('* NMEA Latitude'):
                    self._header_lat = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('* NMEA Longitude'):
                    self._header_lon = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('** Station'):
                    self._header_station = line.split(':')[-1].strip()
                elif line.startswith('** Cruise'):
                    self._header_cruise_info = get_cruise_match_dict(line.split(':')[-1].strip())

                # Header form
                if line.startswith('**'):
                    if line.count(':') == 1:
                        key, value = [part.strip() for part in line.strip().strip('*').split(':')]
                        self._header_form[key] = value
                    else:
                        self._header_form['info'].append(strip_line)

                # Parameters
                elif strip_line.startswith('# name'):
                    hn = HeaderName(line)
                    self._header_names.append(hn)
                    obj = Parameter(use_cnv_info_format=False,
                                    cnv_info_object=None,
                                    index=hn.index, name=hn.parameter)
                    # obj = Parameter(use_cnv_info_format=self.use_cnv_info_format,
                    #                 cnv_info_object=self.cnv_info_object[hn.index],
                    #                 index=hn.index, name=hn.parameter)
                    self._parameters[obj.index] = obj

                # XML
                if line.startswith('# <Sensors count'):
                    is_xml = True
                if is_xml:
                    xml_lines.append(line[2:])
                if line.startswith('# </Sensors>'):
                    is_xml = False
                    self._xml_tree = xmlcon_parser.get_parser_from_string(''.join(xml_lines))
                    self._sensor_info = xmlcon_parser.get_sensor_info(self._xml_tree)

                if '*END*' in line:
                    self._header_rows.add_row(line)
                    header = False
                    continue
                if header:
                    self._header_rows.add_row(line)
                else:
                    if not line.strip():
                        continue
                    self._nr_data_lines += 1
                    split_line = strip_line.split()
                    if not has_set_value_length:
                        tot_len = len(line.rstrip())
                        value_length = tot_len / len(split_line)
                        int_value_lenght = int(value_length)
                        if int_value_lenght != value_length:
                            raise ValueError('Something is wrong in the file!')
                        for i, value in enumerate(split_line):
                            self._parameters[i].set_value_length(int_value_lenght)
                        has_set_value_length = True
                    for i, value in enumerate(split_line):
                        self._parameters[i].add_data(value)

    def _get_datetime_from_path(self):
        if all([self._path_info.get(key) for key in ['year', 'day', 'minute', 'hour', 'minute']]):
            return datetime.datetime(int(self._path_info['year']),
                                     int(self._path_info['day']),
                                     int(self._path_info['minute']),
                                     int(self._path_info['hour']),
                                     int(self._path_info['minute']))

    def _check_time(self):
        pass

