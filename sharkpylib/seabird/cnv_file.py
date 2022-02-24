from pathlib import Path
import datetime

from sharkpylib.seabird.file import InstrumentFile
from sharkpylib.seabird.patterns import get_cruise_match_dict

from sharkpylib.seabird import xmlcon_parser

from sharkpylib.seabird.modify_cnv import ModifyCnv


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
        self._lines = []

    @property
    def lines(self):
        return self._lines

    def add_line(self, row):
        self._lines.append(row.strip())


class Parameter:
    def __init__(self, use_cnv_info_format=False, cnv_info_object=None, index=None, name=None, **kwargs):

        self.info = {'index': index,
                     'name': name}
        self.info.update(kwargs)

        self.use_cnv_info_format = use_cnv_info_format
        self.cnv_info_object = cnv_info_object
        self._tot_value_length = 11
        self._value_format = 'd'
        self._nr_decimals = None
        self.sample_value = None
        self._data = []
        self.active = False

    def __getitem__(self, item):
        return self.info.get(item)

    def __getattr__(self, item):
        return self.info.get(item)

    def __repr__(self):
        return_list = [f'CNVparameter (dict): {self.info["name"]}']
        blanks = ' '*4
        for key, value in self.info.items():
            return_list.append(f'{blanks}{key:<20}{value}')

        if len(self._data):
            return_list.append(f'{blanks}{"Sample value":<20}{self.sample_value}')
            if self.use_cnv_info_format:
                form = f'{self.get_format()} (from info file)'
            else:
                form = f'{self.get_format()} (calculated from data)'
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

    def get_format(self, value=None):
        if self.use_cnv_info_format:
            return self.cnv_info_object.format
        if self._nr_decimals is None:
            form = f'{self._tot_value_length}{self._value_format}'
        else:
            if value and self._value_format == 'e' and str(value).startswith('-'):
                form = f'{self._tot_value_length}.{self._nr_decimals - 1}{self._value_format}'
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

    def get_value_as_string_for_index(self, index):
        if type(self.data[index]) == str:
            return self.data[index].rjust(self._tot_value_length)
        return '{:{}}'.format(self.data[index], self.get_format(self.data[index]))

    def set_active(self, is_active):
        self.active = is_active


class CnvFile(InstrumentFile):
    suffix = '.cnv'
    header_date_format = '%b %d %Y %H:%M:%S'
    header = None
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._save_columns()

    def get_save_name(self):
        if self('prefix') == 'd':
            return f'{self.key}{self.suffix}'
        return self.get_proper_name()

    def _get_datetime(self):
        return self._header_datetime or self._get_datetime_from_path()

    def _save_attributes(self):
        self._attributes.update(self._header_cruise_info)
        self._attributes['lat'] = self._header_lat
        self._attributes['lon'] = self._header_lon
        self._attributes['station'] = self._header_station
        self._attributes['sensor_info'] = self._sensor_info

    def _save_info_from_file(self):
        self._header_form = {'info': []}
        self._header_names = []
        self._nr_data_lines = 0
        self.header = Header()
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
                    self.header.add_line(line)
                    header = False
                    continue
                if header:
                    self.header.add_line(line)
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
                            print(self.path)
                            raise ValueError('Something is wrong in the file!')
                        for i, value in enumerate(split_line):
                            self._parameters[i].set_value_length(int_value_lenght)
                        has_set_value_length = True
                    for i, value in enumerate(split_line):
                        self._parameters[i].add_data(value)

    def _save_columns(self):
        self.col_pres = None
        self.col_dens = None
        self.col_dens2 = None
        self.col_depth = None
        self.col_sv = None

        for par in self._parameters.values():
            if 'Pressure, Digiquartz [db]' in par.name:
                self.col_pres = par.index
            elif 'Density [sigma-t' in par.name:
                self.col_dens = par.index
            elif 'Density, 2 [sigma-t' in par.name:
                self.col_dens2 = par.index
            elif 'Depth [fresh water, m]' in par.name:
                self.col_depth = par.index
            elif 'Depth [true depth, m]' in par.name:
                self.col_depth = par.index
            elif 'Sound Velocity [Chen-Millero, m/s]' in par.name:
                self.col_sv = par.index

    @property
    def parameters(self):
        return self._parameters

    @property
    def pressure_data(self):
        return self._parameters[self.col_pres].data

    @property
    def depth_data(self):
        return self._parameters[self.col_depth].data

    @property
    def sound_velocity_data(self):
        return self._parameters[self.col_sv].data

    @property
    def density_data(self):
        if self._parameters[self.col_dens].active:
            return self._parameters[self.col_dens].data
        elif self._parameters[self.col_dens2].active:
            return self._parameters[self.col_dens2].data
        else:
            return [ModifyCnv.missing_value]*self._nr_data_lines

    @property
    def header_lines(self):
        return self.header.lines

    @property
    def data_lines(self):
        data_rows = []
        for r in range(self._nr_data_lines):
            line_list = []
            for par, obj in self.parameters.items():
                value = obj.get_value_as_string_for_index(r)
                line_list.append(value)
            line_string = ''.join(line_list)
            data_rows.append(line_string)
        return data_rows

    def string_match_header_form(self, string):
        for value in self._header_form.values():
            if isinstance(value, list):
                for item in value:
                    if string in item:
                        return True
            else:
                if string in value:
                    return True
        return False


