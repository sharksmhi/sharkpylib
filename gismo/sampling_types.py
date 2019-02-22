#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import numpy as np
import datetime
import pandas as pd
import codecs
import re
import matplotlib.dates as dates

from .mapping import StationMapping, ParameterMapping
from .gismo import GISMOdata

from .exceptions import *


import logging
logger = logging.getLogger('gismo_session')

class PluginFactory(object):
    """
    Class hold information about active classes in module.
    Also contains method to return an object of a mapped class.

    New class in module is activated by adding class name to self.classes.

    Also make sure to add required input arguments (for __init__) to self.required_arguments.
    """
    def __init__(self):
        # Add key and class to dict if you want to activate it
        self.classes = {'Ferrybox CMEMS': CMEMSferrybox,
                        'Fixed platforms CMEMS': CMEMSFixedPlatform,
                        'PhysicalChemical SHARK': SHARKfilePhysicalChemichal,
                        'CTD SHARK': SHARKfileStandardCTD}

        # ferrybox_requirements = ['data_file_path', 'settings_file_path', 'root_directory']
        ferrybox_requirements = ['data_file_path', 'settings_file_path']
        fixed_platform_requirements = ferrybox_requirements + ['depth']
        shark_requirements = ferrybox_requirements
        self.required_arguments = {'Ferrybox CMEMS': ferrybox_requirements,
                                   'Fixed platforms CMEMS': fixed_platform_requirements,
                                   'PhysicalChemical SHARK': shark_requirements,
                                   'CTD SHARK': shark_requirements}



    def get_list(self):
        return sorted(self.classes)

    def get_object(self, sampling_type, *args, **kwargs):
        if not self.classes.get(sampling_type):
            raise GISMOExceptionInvalidClass
        kwargs['sampling_type'] = sampling_type
        return self.classes.get(sampling_type)(*args, **kwargs)

    def get_requirements(self, sampling_type):
        """
        Created 20181005     

        Returns the required arguments needed for the initialisation of the object
        :param sampling_type:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.classes.get(sampling_type):
            raise GISMOExceptionInvalidClass
        return self.required_arguments.get(sampling_type)

    # ==============================================================================


# ==============================================================================
class GISMOfile(GISMOdata):
    """
    Updated 20181005     

    Base class for a GISMO data file.
    A GISMO-file only has data from one sampling type.
    """
    # TODO: filter_data, flag_options, flag_data
    # ==========================================================================
    def __init__(self, data_file_path=None, settings_file_path=None, root_directory=None, mapping_files_directory=None, **kwargs):

        GISMOdata.__init__(self, **kwargs)
        # super().__init__()

        self.file_path = data_file_path
        self.file_id, ending = os.path.splitext(os.path.basename(data_file_path))
        self.settings_file_path = settings_file_path
        self.export_df = None
        self.root_directory = root_directory
        self.mapping_files_directory = mapping_files_directory

        self.sampling_type = kwargs.get('sampling_type', '')

        self._find_mapping_files()
        self._load_settings_file()
        self._load_station_mapping()
        self._load_parameter_mapping()

        self.comment_id = self.settings.info.get('comment_id', None)
        self.file_encoding = self.settings.info.get('encoding', 'cp1252')
        self.column_separator = self.settings.info.get('column_separator', '\t')
        if self.column_separator == 'tab':
            self.column_separator = '\t'

        self._load_data()
        self._do_import_changes(**kwargs)

        self.parameter_list = []

        self.parameter_list = ['time', 'lat', 'lon', 'depth', 'visit_id', 'visit_depth_id'] + self.qpar_list
        # self.parameter_list = ['time', 'lat', 'lon', 'depth'] + self.qpar_list
        self.filter_data_options = []
        self.flag_data_options = ['flags']
        self.mask_data_options = ['include_flags', 'exclude_flags']

        self.save_data_options = ['file_path', 'overwrite']

        self.valid_flags = self.settings.flag_list[:]

        self.valid_qc_routines = []

    # ==========================================================================
    def _load_settings_file(self):
        self.settings = SamplingTypeSettings(self.settings_file_path, root_directory=self.root_directory)

        self.missing_value = str(self.settings.info.missing_value)

        nr_decimals = self.settings.info.number_of_decimals_for_float
        if nr_decimals:
            self.nr_decimals = '%s.%sf' % ('%', nr_decimals)
        else:
            self.nr_decimals = None

        # self.file_encoding = self.settings

    def _find_mapping_files(self):
        # Mapping files
        if not os.path.exists(self.mapping_files_directory):
            os.makedirs(self.mapping_files_directory)
        self.mapping_files = {}
        for file_name in os.listdir(self.mapping_files_directory):
            if not file_name.endswith('txt'):
                continue
            self.mapping_files[file_name] = os.path.join(self.mapping_files_directory, file_name)

    # ==========================================================================
    def _load_station_mapping(self):
        self.station_mapping = StationMapping(settings_object=self.settings,
                                              mapping_files=self.mapping_files)

    # ==========================================================================
    def _load_parameter_mapping(self):
        self.parameter_mapping = ParameterMapping(settings_object=self.settings,
                                                  mapping_files=self.mapping_files)


    # ==========================================================================
    def _load_data(self, **kwargs):
        """
        Updated 20181005     

        All comment lines are stored in attribute metadata.

        :param kwargs:
        :return:
        """

        logger.info('Loading file {}'.format(self.file_id))
        logger.info('    encoding {}'.format(self.file_encoding))
        logger.info('         sep {}'.format(self.column_separator))
        logger.info('  comment_id {}'.format(self.comment_id))

        # Looping through the file seems to be faster then pd.read_csv regardless if there are comment lines or not.
        # Note that all values are of type str.
        self.metadata_raw = []
        header = []
        data = []
        with codecs.open(self.file_path, encoding=self.file_encoding) as fid:
            for line in fid:
                if self.comment_id is not None and line.startswith(self.comment_id):
                    # We have comments and need to load all lines in file
                    self.metadata_raw.append(line)
                else:
                    split_line = re.split(self.column_separator, line.strip('\n\r'))
                    # split_line = line.strip('\n\r').split(self.column_separator)
                    split_line = [item.strip() for item in split_line]
                    if not header:
                        header = split_line
                    else:
                        data.append(split_line)

        self.original_columns = header[:]
        self.df = pd.DataFrame(data, columns=header)

        # Remove columns with no column name
        try:
            self.df.drop('', axis=1, inplace=True)
            self.original_columns = [col for col in self.original_columns if col]
        except KeyError:
            pass

        self.df.fillna('', inplace=True)


#        metadata_raw = []
#        if kwargs.get('comment_id'):
#            with codecs.open(self.file_path, encoding=kwargs.get('encoding', 'cp1252')) as fid:
#                for line in fid:
#                    if line.startswith(kwargs.get('comment_id')):
#                        metadata_raw.append(line.strip())  # remove newline
#                    else:
#                        # No more comments
#                        break
#
#        self.df = pd.read_csv(self.file_path, sep='\t', skipinitialspace=True, dtype={0: str},
#                              encoding=self.file_encoding, comment=kwargs.get('comment_id', None))

        # Find station id (platform type)
        station = self.settings.column.station
        if 'index' in station:
            col = int(station.split('=')[-1].strip())
            self.external_station_name = self.df.columns[col]
            self.internal_station_name = self.station_mapping.get_internal(self.external_station_name)
        else:
            self.external_station_name = 'Unknown'
            self.internal_station_name = 'Unknown'

        #        self.platform_type = self.station_mapping.get_platform_type(self.external_station_name)

        # Save parameters
        self.parameters_external = [external for external in self.df.columns if 'Unnamed' not in external]
        self.parameters_internal = [self.parameter_mapping.get_internal(external) for external in
                                    self.parameters_external]

        self.internal_to_external = dict(zip(self.parameters_internal, self.parameters_external))
        self.external_to_internal = dict(zip(self.parameters_external, self.parameters_internal))

        self.qpar_list = sorted([par for par in self.parameters_external if self.get_qf_par(par) not in [None, False]])
        self.mapped_parameters = [self.parameter_mapping.get_internal(par) for par in self.qpar_list]

        # Set type of flags to str
#        for qpar in self.qpar_list:
#            self.df[qpar] = self.df[qpar].astype(str)

    # ==========================================================================
    def _do_import_changes(self, **kwargs):
        self._add_columns(**kwargs)
        self.df.replace(self.missing_value, '', inplace=True)

    # ==========================================================================
    def _prepare_export(self):
        # Make a copy to be used for export
        self.export_df = self.df[self.original_columns].copy()
        try:
            self.export_df.replace(np.nan, float(self.missing_value), inplace=True)
        except:
            pass

    def _get_argument_list(self, arg):
        """
        Updated 20181004     

        Returns a list. If type(arg) != list/array/tuple, [arg] is returned
        :param arg:
        :return: list
        """
        if type(arg) in [list, tuple, np.array, np.ndarray]:
            return list(arg)
        else:
            return [arg]

    def _get_pandas_series(self, value):
        """
        Created 20181005     

        :param value: boolean or value
        :return: a  pandas series of length len(self.df) with the given value.
        """
        if type(value) == bool:
            if value:
                return pd.Series(np.ones(len(self.df), dtype=bool))
            else:
                return pd.Series(np.zeros(len(self.df), dtype=bool))
        else:
            return pd.Series([value]*len(self.df))


    # ==========================================================================
    def _add_columns(self, **kwargs):
        """
        Add columns for time, lat, lon and depth.
        Information about parameter name should be in settings.
        """
        #         print '='*30
        #         for c in sorted(self.df.columns):
        #             print c
        #         print '-'*30
        # ----------------------------------------------------------------------
        # Time
        time_formats = ['%Y%m%d%H%M',
                        '%Y%m%d%H:%M',
                        '%Y%m%d%H.%M',
                        '%Y-%m-%d%H%M',
                        '%Y-%m-%d%H:%M',
                        '%Y-%m-%d%H.%M']
        self.time_format = None
        datetime_list = []
        time_par = self.settings.column.time
        if 'index' in time_par:
            # At this moment mainly for CMEMS-files
            time_par = self.df.columns[int(time_par.split('=')[-1].strip())]
            self.df['time'] = pd.to_datetime(self.df[time_par], format=self.time_format)
        else:
            time_pars = self.settings.column.get_list('time')

            self.df['time'] = self.df[time_pars].apply(apply_datetime_object_to_df, axis=1)
            # print(time_pars)
            # for i in range(len(self.df)):
            #     # First look in settings and combine
            #     value_list = []
            #     for par in time_pars:
            #         value_list.append(self.df.ix[i, par])
            #
            #     value_str = ''.join(value_list)
            #
            #     if not self.time_format:
            #         for tf in time_formats:
            #             try:
            #                 datetime.datetime.strptime(value_str, tf)
            #                 self.time_format = tf
            #                 break
            #             except:
            #                 pass
            #
            #     datetime_list.append(datetime.datetime.strptime(value_str, self.time_format))
            #
            # self.df['time'] = pd.Series(datetime_list)

        # ----------------------------------------------------------------------
        # Position
        lat_par = self.parameter_mapping.get_external(self.settings.column.lat)
        lon_par = self.parameter_mapping.get_external(self.settings.column.lon)

        self.df['lat'] = self.df[lat_par]
        self.df['lon'] = self.df[lon_par]

        # ----------------------------------------------------------------------
        # Station ID
        self.df['visit_id'] = self.df['lat'].astype(str) + self.df['lon'].astype(str) + self.df['time'].astype(str)
        print(kwargs.get('depth'))

        if kwargs.get('depth', None) is not None:
            self.df['depth'] = kwargs.get('depth')
        else:
            depth_par = self.parameter_mapping.get_external(self.settings.column.depth)
            self.df['depth'] = self.df[depth_par].astype(float)
        self.df['visit_depth_id'] = self.df['lat'].astype(str) + self.df['lon'].astype(str) + self.df['time'].astype(
            str) + self.df['depth'].astype(str)


    def flag_data(self, flag, *args, **kwargs):
        """
        Created 20181005     

        :param flag: The flag you want to set for the parameter
        :param args: parameters that you want to flag.
        :param kwargs: conditions for flagging. Options are listed in self.flag_data_options
        :return: None
        """
        flag = str(flag)
        if flag not in self.valid_flags:
            raise GISMOExceptionInvalidFlag('"{}", valid flags are "{}"'.format(flag, ', '.join(self.valid_flags)))

        if flag == 'no flag':
            flag = ''

        # Check dependent parameters
        all_args = []
        for arg in args:
            all_args.append(arg)
            all_args.extend(self.get_dependent_parameters(arg))

        print('===================len(args)', len(all_args))
        print(all_args)
        # Work on external column names
        args = [self.internal_to_external.get(arg, arg) for arg in all_args]
        # args = dict((self.internal_to_external.get(key, key), key) for key in args)

        # if not all([arg in self.df.columns for arg in args]):
        #     raise GISMOExceptionInvalidInputArgument


        # kwargs contains conditions for flagging. Options are listed in self.flag_data_options.
        boolean = self._get_pandas_series(True)

        for key, value in kwargs.items():
            # Check valid option
            if key not in self.flag_data_options:
                raise GISMOExceptionInvalidOption
            if key == 'time':
                value_list = self._get_argument_list(value)
                boolean = boolean & (self.df.time.isin(value_list))
            elif key == 'time_start':
                boolean = boolean & (self.df.time >= value)
            elif key == 'time_end':
                boolean = boolean & (self.df.time <= value)
            elif key == 'depth':
                value_list = self._get_argument_list(value)
                boolean = boolean & (self.df.depth.isin(value_list))
            elif key == 'depth_min':
                boolean = boolean & (self.df.depth >= value)
            elif key == 'depth_max':
                boolean = boolean & (self.df.depth <= value)

        print(np.where(boolean)[0])
        # Flag data
        for par in args:
            if par not in self.df.columns:
                print('par', par)
                print()
                print('\n'.join(sorted(self.df.columns)))
                raise GISMOExceptionInvalidParameter('Parameter {} not in data'.format(par))
            qf_par = self.get_qf_par(par)
            if not qf_par:
                raise GISMOExceptionMissingQualityParameter('for parameter "{}"'.format(par))
            flag_list = kwargs.get('flags', None)
            if flag_list:
                if type(flag_list) != list:
                    flag_list = [flag_list]
                if 'no flag' in flag_list:
                    flag_list.pop(flag_list.index('no flag'))
                    flag_list.append('')
                par_boolean = boolean & (self.df[qf_par].isin(flag_list))
            else:
                par_boolean = boolean.copy(deep=True)
                print(par, qf_par, flag)
            self.df.loc[par_boolean, qf_par] = flag

    # ==========================================================================
    def old_get_boolean_for_time_span(self, start_time=None, end_time=None, invert=False):
        """

        :param start_time:
        :param end_time:
        :param invert:
        :return:
        """

        if start_time and end_time:
            boolean_array = np.array((self.df.time >= start_time) & (self.df.time <= end_time))
        elif start_time:
            boolean_array = np.array(self.df.time >= start_time)
        elif end_time:
            boolean_array = np.array(self.df.time <= end_time)
        else:
            boolean_array = np.ones(len(self.df.time), dtype=bool)

        if invert:
            return np.invert(boolean_array)
        else:
            return boolean_array

    def get_data(self, *args, **kwargs):
        """
        Created 20181024
        Updated 20181106

        :param args: parameters that you want to have data for.
        :param kwargs: specify filter. For example profile_id=<something>. Only = if implemented at the moment.
        :return: dict with args as keys and list(s) as values.
        """
        # Always return type float if possible
        kw = {'type_float': True}
        kw.update(kwargs)
        return self._get_data(*args, **kw)

    # ===========================================================================
    def _get_data(self, *args, **kwargs):
        """
        Created 20181004     
        Updated 20181024

        :param args: parameters that you want to have data for.
        :param kwargs: specify filter.
        :return: dict with args as keys and list(s) as values.
        """
        if not args:
            raise GISMOExceptionMissingInputArgument

        # Work on external column names
        args = dict((self.internal_to_external.get(key, key), key) for key in args)

        for arg in args:
            if arg not in self.df.columns:
                raise GISMOExceptionInvalidInputArgument(arg)
            elif arg not in self.parameter_list:
                raise GISMOExceptionInvalidInputArgument(arg)


        # Create filter boolean
        boolean = self._get_pandas_series(True)
        for key, value in kwargs.get('filter_options', {}).items():
            if value in [None, False]:
                continue
            if key not in self.filter_data_options:
                raise GISMOExceptionInvalidOption('{} not in {}'.format(key, self.filter_data_options))
            if key == 'time':
                value_list = self._get_argument_list(value)
                boolean = boolean & (self.df.time.isin(value_list))
            elif key == 'time_start':
                boolean = boolean & (self.df.time >= value)
            elif key == 'time_end':
                boolean = boolean & (self.df.time <= value)
            elif key == 'visit_depth_id':
                value_list = self._get_argument_list(value)
                boolean = boolean & (self.df.visit_depth_id.isin(value_list))
            elif key == 'visit_id':
                value_list = self._get_argument_list(value)
                boolean = boolean & (self.df.visit_id.isin(value_list))
            elif key == 'depth':
                value_list = self._get_argument_list(value)
                boolean = boolean & (self.df.depth.isin(value_list))
            elif key == 'depth_min':
                boolean = boolean & (self.df.depth >= value)
            elif key == 'depth_max':
                boolean = boolean & (self.df.depth <= value)

        # Extract filtered dataframe
        # filtered_df = self.df.loc[boolean, sorted(args)].copy(deep=True)
        filtered_df = self.df.loc[boolean].copy(deep=True)

        mask_options = kwargs.get('mask_options', {})
        # Create return dict and return
        return_dict = {}
        for par in args:
            par_array = filtered_df[par].values
            # if par == 'time':
            #     par_array = filtered_df[par].values
            # elif
            # try:
            #     par_array = filtered_df[par].astype(float).values
            # except:


            # Check mask options
            for opt, value in mask_options.items():
                if opt not in self.mask_data_options:
                    raise GISMOExceptionInvalidOption
                if opt == 'include_flags':
                    qf_par = self.get_qf_par(par)
                    if not qf_par:
                        continue
                    # print('\n'.join(sorted(filtered_df.columns)))
                    qf_list = []
                    for v in value:
                        if v == 'no flag':
                            v = ''
                        else:
                            v = str(v)
                        qf_list.append(v)
                    keep_boolean = filtered_df[qf_par].astype(str).isin(qf_list)
                    par_array[~keep_boolean] = ''
                elif opt == 'exclude_flags':
                    qf_par = self.get_qf_par(par)
                    if not qf_par:
                        continue
                    qf_list = []
                    for v in value:
                        if v == 'no flag':
                            v = ''
                        else:
                            v = str(v)
                        qf_list.append(v)
                    nan_boolean = filtered_df[qf_par].astype(str).isin(qf_list)
                    par_array[nan_boolean] = ''

            # Check output type
            if par == 'time':
                pass
            elif kwargs.get('type_float') is True or par in kwargs.get('type_float', []):
                float_par_list = []
                for value in par_array:
                    try:
                        if value:
                            float_par_list.append(float(value))
                        else:
                            float_par_list.append(np.nan)
                    except:
                        float_par_list.append(value)
                        #raise ValueError
                par_array = np.array(float_par_list)

            elif kwargs.get('type_int') is True or par in kwargs.get('type_int', []):
                float_par_list = []
                for value in par_array:
                    try:
                        if value:
                            float_par_list.append(float(value))
                        else:
                            float_par_list.append(np.nan)
                    except:
                        float_par_list.append(value)
                        # raise ValueError
                par_array = np.array(float_par_list)

            # Map to given column name
            return_dict[args[par]] = par_array
        return return_dict

    # ==========================================================================
    def get_dependent_parameters(self, par):

        if not self.settings:
            return None

        par = self.parameter_mapping.get_external(par)
        # print('FLAG, dependent', par, type(par))
        return self.settings['dependencies'].get(par, [])

    def get_parameter_list(self, **kwargs):
        if kwargs.get('external'):
            par_list = sorted(self.parameter_list)
        else:
            par_list = sorted([self.parameter_mapping.get_internal(par) for par in self.parameter_list])

        return par_list

    def get_position(self, **kwargs):
        data = self.get_data('lat', 'lon')
        if 'lat' in self.df:
            return [data['lat'], data['lon']]
        else:
            raise GISMOExceptionMethodNotImplemented

    def get_dict_with_matching_parameters(self, match_parameter):
        """
        Returns a dictionary for the parameters that matches the parameters in matchparameters.
        key is name in self.df, values is name in match_parameter.
        :param match_parameter:
        :return:
        """
        print('TYPE', type(match_parameter), match_parameter)
        return_dict = {}
        par_list = list(set(self.get_parameter_list(internal=True) + self.get_parameter_list(external=True)))
        for par in par_list:
            for m_par in match_parameter:
                if m_par.lower() in par.lower():
                    return_dict[self.get_internal_parameter_name(par)] = m_par
                    continue
        return return_dict

    def get_internal_parameter_name(self, parameter):
        """
        :param parameter:
        :return: internal name of the given parameter.
        """
        return self.parameter_mapping.get_internal(parameter)

    def get_external_parameter_name(self, parameter):
        """
        :param parameter:
        :return: external name of the given parameter.
        """
        return self.parameter_mapping.get_external(parameter)

    def get_unit(self, par='', **kwargs):
        """
        Returns the unit of the given parameter in found.
        :param par:
        :return:
        """
        return self.parameter_mapping.get_unit(par)

    def get_qf_list(self, *args, **kwargs):
        """
        Returns a list och quality flags for the parameter par.
        :param par:
        :return:
        """
        not_valid_par = []
        for par in args:
            if par not in self.df.columns:
                not_valid_par.append(par)
        if not_valid_par:
            raise GISMOExceptionInvalidParameter('; '.join(not_valid_par))

        return_dict = {}
        for par in args:
            qf_par = self.get_qf_par(par)
            if not qf_par:
                continue
            return_dict[par] = list(self.df[qf_par])
        return return_dict

    # ==========================================================================
    def get_qf_par(self, par):
        """
        Updated 20181004
        :param par:
        :return:
        """
        prefix = self.settings.parameter_mapping.qf_prefix
        suffix = self.settings.parameter_mapping.qf_suffix
        # First check if prefix and/or suffix is given
        if not any([prefix, suffix]):
            print('No prefix or suffix given to this QF parameter')
            return

        if par in self.parameters_internal:
            par = self.internal_to_external[par]

        #         print 'par=', par
        if self.settings.parameter_mapping.unit_starts_with:
            par = par.split(self.settings.parameter_mapping.unit_starts_with)[0].strip()
        #             print 'par-', par

        # QF parameter is found whenever prefix or suffix matches the given par.
        # This means that if prefix="QF_" and par="TEMP", not only "QF_TEMP" is recognised but also "QF_TEMP (C)"
        for ext_par in self.parameters_external:
            if par in ext_par and ext_par.startswith(prefix) and ext_par.endswith(suffix):
                if ext_par != par:
                    #                     print 'ext_par', ext_par, par, prefix, suffix
                    return ext_par
        return False

    def get_metadata_tree(self):
        if self.metadata:
            return self.metadata.get_metadata_tree()
        else:
            raise GISMOExceptionMethodNotImplemented

    # ==========================================================================
    def _get_extended_qf_list(self, qf_list):
        """
        The pandas datafram may contain both str and int value in the qf-columns.
        This method adds both str and int versions of the given qf_list.
        """

        if not type(qf_list) == list:
            qf_list = [qf_list]

        # Add both int ans str versions of the flags
        extended_qf_list = []
        for qf in qf_list:
            extended_qf_list.append(qf)
            if type(qf) == int:
                extended_qf_list.append(str(qf))
            elif qf.isdigit():
                extended_qf_list.append(int(qf))

        return extended_qf_list

    # ===========================================================================
    def save_file(self, **kwargs):
        file_path = kwargs.get('file_path', None)
        if not file_path:
            file_path = self.file_path
        if os.path.exists(file_path) and not kwargs.get('overwrite', False):
            raise GISMOExceptionFileExcists(file_path)
        # write_kwargs = {'index_label': False,
        #                 'index': False,
        #                 'sep': '\t',
        #                 'float_format': self.nr_decimals,
        #                 'decimal': '.'}
        #
        # write_kwargs.update(kwargs)

        self._prepare_export()

        data_dict = self.export_df.to_dict('split')

        with codecs.open(file_path, 'w', encoding=self.file_encoding) as fid:
            if self.metadata and self.metadata.has_data:
                fid.write('\n'.join(self.metadata.get_lines()))
                fid.write('\n')
            # Write column header
            fid.write(self.column_separator.join(data_dict['columns']))
            fid.write('\n')
            for line in data_dict['data']:
                fid.write(self.column_separator.join(line))
                fid.write('\n')


# ==============================================================================
# ==============================================================================
class CMEMSferrybox(GISMOfile):
    """
    A GISMO-file only has data from one platform.
    """

    # ==========================================================================
    def __init__(self, data_file_path=None, settings_file_path=None, root_directory=None, **kwargs):
        """
        Updated 20181005     

        :param data_file_path:
        :param settings_file_path:
        :param root_directory:
        :param kwargs:
        """
        kwargs.update(dict(data_file_path=data_file_path,
                           settings_file_path=settings_file_path,
                           root_directory=root_directory))

        for key in sorted(kwargs):
            print(key, kwargs[key])

        GISMOfile.__init__(self, **kwargs)

        self.filter_data_options = self.filter_data_options + ['time', 'time_start', 'time_end']
        self.flag_data_options = self.flag_data_options + ['time', 'time_start', 'time_end']
        self.mask_data_options = self.mask_data_options + []

        self.valid_qc_routines = ['Mask areas']


# ==============================================================================
class CMEMSFixedPlatform(GISMOfile):
    """
    A GISMO-file only has data from one platform.
    """

    # ==========================================================================
    def __init__(self, data_file_path=None, settings_file_path=None, root_directory=None, depth=None, **kwargs):
        """
        Updated 20181022
        B

        :param data_file_path:
        :param settings_file_path:
        :param root_directory:
        :param kwargs:
        """
        kwargs.update(dict(data_file_path=data_file_path,
                           settings_file_path=settings_file_path,
                           root_directory=root_directory,
                           depth=depth))
        GISMOfile.__init__(self, **kwargs)

        # self.parameter_list = ['time', 'lat', 'lon', 'depth'] + self.qpar_list

        self.filter_data_options = self.filter_data_options + ['time', 'time_start', 'time_end']
        self.flag_data_options = self.flag_data_options + ['time', 'time_start', 'time_end']
        self.mask_data_options = self.mask_data_options + []

    def get_station_name(self, external=False):
        if external:
            return self.df.columns[0]
        else:
            return self.station_mapping.get_internal(self.df.columns[0])

# ==============================================================================
# ==============================================================================
class SHARKfileStandardCTD(GISMOfile):
    """
    A DATA-file has data from several platforms. Like SHARKweb Physical/Chemical columns.
    """

    # ==========================================================================
    def __init__(self, file_path=None, settings_file_path=None, root_directory=None, **kwargs):
        """
        Updated 20181005     

        :param file_path:
        :param settings_file_path:
        :param root_directory:
        :param kwargs:
        """

        kwargs.update(dict(file_path=file_path,
                           settings_file_path=settings_file_path,
                           root_directory=root_directory))
        GISMOfile.__init__(self, **kwargs)

        self.filter_data_options = self.filter_data_options + ['depth', 'depth_min', 'depth_max']
        self.flag_data_options = self.flag_data_options + ['depth', 'depth_min', 'depth_max']
        self.mask_data_options = self.mask_data_options + []

        self.metadata = SHARKmetadataStandardBase(self.metadata_raw, **kwargs)

        self.valid_qc_routines = ['Profile range simple', 'Profile report']

    def get_position(self, *kwargs):
        return [float(self.df['lat'].values[0]), float(self.df['lon'].values[0])]

    def get_time(self):
        return [self.df['time'].values[0]]

    def get_station_name(self, **kwargs):
        """
        Station can be found in metadata or self.df['station']
        :return:
        """
        return self.metadata.data['METADATA'].get_statn()


# ==============================================================================
# ==============================================================================
class SHARKmetadataStandardBase(object):
    """
    Created 20180928     
    Updated 20181003     

    Class holds metadata information of a GISMO file.
    """

    class FileInfo(object):
        """ Class to handle the file info found at the top of the file """
        def __init__(self, **kwargs):
            self.has_data = False
            self.metadata_string = ''
            self.data = []
            self.column_sep = '='
            self.comment_id = kwargs.get('comment_id', '//')
            self.metadata_id = ''

        def add(self, line):
            """ Whole line is given in line """
            self.data.append(line)

        def set(self, **kwargs):
            pass

        def get_rows(self):
            return self.data

        def get_metadata_tree(self):
            return_dict = {}
            for line in self.data:
                split_line = line.strip().strip('//').split(self.column_sep)
                return_dict[split_line[0]] = {'value': split_line[1]}
            return return_dict

    class Metadata(object):
        """ Class to handle the METADATA """
        def __init__(self, **kwargs):
            self.has_data = False
            self.metadata_string = 'METADATA'
            self.data = {}
            self.column_sep = kwargs.get('column_sep', ';')
            self.comment_id = kwargs.get('comment_id', '//')
            self.metadata_id = '{}METADATA'.format(self.comment_id)
            self.item_order = []

        def add(self, item_list, **kwargs):
            """
            item is expected to be a list of length 2:
                item_list[0] = metadata variable
                item_list[1] = value of the metadata variable
            """
            if item_list[0] != self.metadata_id:
                raise GISMOExceptionMetadataError('Non matching metadata string')
            self.data[item_list[1]] = item_list[2]
            self.item_order.append(item_list[1])
            self.has_data = True

        def set(self, **kwargs):
            for key, value in kwargs.items():
                self.data[key] = value

        def get_rows(self):
            return_list = []
            for key in self.item_order:
                line_list = [self.metadata_id, key, self.data[key]]
                return_list.append(self.column_sep.join(line_list))

            return return_list

        def get_metadata_tree(self):
            return_dict = {}
            for key, value in self.data.items():
                return_dict[key] = {'value': value}
            return return_dict

        def get_statn(self):
            return self.data.get('STATN')

    class SensorInfo(object):
        def __init__(self, **kwargs):
            self.has_data = False
            self.metadata_string = 'SENSORINFO'
            self.data = None
            self.column_sep = kwargs.get('column_sep', ';')
            self.metadata_id = '{}SENSORINFO'.format(kwargs.get('comment_id', '//'))

        def add(self, item_list, **kwargs):
            """
            If self.data is empty item_list is the header to the dataframe.
            """
            if item_list[0] != self.metadata_id:
                raise GISMOExceptionMetadataError('Non matching metadata string')

            row_list = item_list[1:]

            if self.data is None:
                self.header = row_list
                self.data = pd.DataFrame([], columns=row_list)
            else:
                df = pd.DataFrame([row_list], columns=self.header)
                self.data = self.data.append(df)
                self.data.reset_index(inplace=True)
                self.data.pop('index')
                self.has_data = True

        def set(self, **kwargs):
            pass

        def get_rows(self):
            return_list = []
            line_list = [self.metadata_id] + self.header
            return_list.append(self.column_sep.join(line_list))
            for i in self.data.index:
                line_list = [self.metadata_id] + list(self.data.iloc[i].values)
                return_list.append(self.column_sep.join(line_list))

            return return_list

        def get_metadata_tree(self):
            par_key = 'PARAM_SIMPLE'
            columns = [item for item in self.data.columns if item != par_key]
            return_dict = {}
            level_dict = return_dict
            for k in self.data.index:
                line_dict = dict(zip(self.data.columns, self.data.iloc[k].values))
                par = line_dict[par_key]
                return_dict.setdefault(par, {'children': {}})
                for item in columns:
                    return_dict[par]['children'][item] = {'value': line_dict[item]}
            return return_dict


    class Information(object):
        """ Class to handle the INFORMATION """
        def __init__(self, **kwargs):
            self.has_data = False
            self.metadata_string = 'INFORMATION'
            self.data = []
            self.column_sep = kwargs.get('column_sep', ';')
            self.metadata_id = '{}INFORMATION'.format(kwargs.get('comment_id', '//'))

        def add(self, item_list, **kwargs):
            """
            """
            if self.metadata_string not in item_list[0]:
                raise GISMOExceptionMetadataError('Non matching metadata string')
            self.data.append(self.column_sep.join(item_list[1:]))
            self.has_data = True

        def set(self, **kwargs):
            pass

        def get_rows(self):
            return_list = []
            for item in self.data:
                return_list.append(self.column_sep.join([self.metadata_id, item]))

            return return_list

        def get_metadata_tree(self):
            return_dict = {}
            for k, item in enumerate(self.data):
                return_dict['Comment nr {}'.format(k+1)] = {'value': item}
            return return_dict

    class InstrumentMetadata(object):
        """ Class to handle the INFORMATION """

        def __init__(self, **kwargs):
            self.has_data = False
            self.metadata_string = 'INSTRUMENT_METADATA'
            self.data = []
            self.column_sep = kwargs.get('column_sep', ';')
            self.metadata_id = '{}INSTRUMENT_METADATA'.format(kwargs.get('comment_id', '//'))

        def add(self, item_list, **kwargs):
            """
            """
            if item_list[0] != self.metadata_id:
                raise GISMOExceptionMetadataError('Non matching metadata string')
            self.data.append(kwargs.get('original_line').strip('\r\n'))
            self.has_data = True

        def set(self, **kwargs):
            pass

        def get_rows(self):
            return self.data

        def get_metadata_tree(self):
            return_dict = {}
            for k, item in enumerate(self.data):
                return_dict['line {}'.format(k + 1)] = {'value': item}
            return return_dict

    # ==========================================================================
    def __init__(self, metadata_raw_lines, **kwargs):
        super().__init__()
        self.metadata_raw_lines = metadata_raw_lines

        self.column_sep = kwargs.get('metadata_column_sep', ';')
        self.comment_id = kwargs.get('comment_id', '//')

        self._load_meatadata()

    # ==========================================================================
    def _load_meatadata(self):
        """
        Updated 20181003     
        """
        kw = dict(column_sep=self.column_sep,
                  comment_id=self.comment_id)

        self.file_info = self.FileInfo(**kw)

        self.data = {'METADATA': self.Metadata(**kw),
                     'SENSORINFO': self.SensorInfo(**kw),
                     'INFORMATION': self.Information(**kw),
                     'INSTRUMENT_METADATA': self.InstrumentMetadata(**kw)}

        self.metadata_order = []

        for k, original_line in enumerate(self.metadata_raw_lines):
            line = original_line.strip()

            # First line is FORMAT id line
            if k <= 2:
                if 'FORMAT' in line:
                    self.file_format = line.split('=')[-1]

                self.file_info.add(line)

            else:
                split_line = line.split(self.column_sep)
                metadata_type = split_line[0].strip(self.comment_id)

                if metadata_type not in self.data:
                    raise GISMOExceptionMetadataError('New field in metadata is not handled properly: {}'.format(metadata_type))

                if self.data.get(metadata_type):
                    self.data[metadata_type].add(split_line, original_line=original_line)
                # else:
                #     self.data['unhandled'].add(line)
                if metadata_type not in self.metadata_order:
                    self.metadata_order.append(metadata_type)
            self.has_data = True

    def get_metadata(self):
        metadata_dict = {}
        for metadata_type in self.metadata_order:
            metadata_dict[metadata_type] = self.data[metadata_type].get_metadata()

    def get_lines(self):
        all_lines = self.file_info.get_rows()
        for metadata_type in self.metadata_order:
            all_lines.extend(self.data[metadata_type].get_rows())
        return all_lines

    def get_metadata_tree(self):
        return_dict = {}
        for key in self.metadata_order:
            return_dict[key] = {'children': self.data[key].get_metadata_tree()}
        return return_dict


# ==============================================================================
# ==============================================================================
class SamplingTypeSettings(dict):
    """
    Reads and stores information from a "GISMO" Settings file.
    """

    # ==========================================================================
    # ==========================================================================
    class MappingObject(dict):
        def __init__(self, data, root_directory=None):
            for line in data:
                split_line = [item.strip() for item in line.split('\t')]
                if len(split_line) == 1:
                    header = split_line[0]
                    value = ''
                else:
                    header, value = split_line[:2]
                header = header.lower().replace(' ', '_')

                if 'root' in value:
                    if not root_directory:
                        raise GISMOExceptionMissingPath('Must provide root_directory')
                    value = value.replace('root', root_directory)
                    if not os.path.exists(value):
                        raise GISMOExceptionMissingPath(value)

                if ';' in value:
                    value = [item.strip() for item in value.split(';')]

                self[header] = value
                setattr(self, header, value)

        # ======================================================================
        def get_list(self, item):
            value = getattr(self, item)
            if not isinstance(value, list):
                value = [value]
            return value

    # ==========================================================================
    def __init__(self, file_path=None, root_directory=None):
        self.file_path = file_path
        self.root_directory = root_directory
        dict.__init__(self)
        if self.file_path:
            self._load_file()
            self._save_data()

    # ==========================================================================
    def _load_file(self):

        self.data = {}
        current_header = None
        fid = codecs.open(self.file_path, 'r', encoding='cp1252')

        for line in fid:
            line = line.strip('\r\n')
            # Blank line or comment line
            if not line or line.startswith('#'):
                continue

            # Find header
            if line.startswith('='):
                current_header = line.strip('= ')
                self.data[current_header] = []
            else:
                self.data[current_header].append(line)

        fid.close()

    # ==========================================================================
    def _save_data(self):
        for key in self.data:
            # ------------------------------------------------------------------
            if key.lower() == 'flags':
                self['flags'] = {}
                self.description_to_flag = {}
                for i, line in enumerate(self.data[key]):
                    split_line = [item.strip() for item in line.split('\t')]
                    if i == 0:
                        header = [item.lower() for item in split_line]
                    else:
                        qf = split_line[header.index('qf')]
                        if qf == '':
                            qf = 'no flag'
                        self['flags'][qf] = {}
                        for par, item in zip(header, split_line):
                            if par == 'markersize':
                                item = int(item)
                            elif par == 'description':
                                self.description_to_flag[item] = qf

                            self['flags'][qf][par] = item

                self.flag_list = sorted(self['flags'])

            # ------------------------------------------------------------------
            elif key.lower() == 'dependent parameters':
                self['dependencies'] = {}
                for line in self.data[key]:
                    split_line = [item.strip() for item in line.split(';')]
                    primary_parameter = split_line[0]
                    dependent_parameters = []
                    for item in split_line[1:]:
                        if ':' in item:
                            # Range of integers
                            from_par, to_par = [int(par.strip()) for par in item.split(':')]
                            dependent_parameters.extend(list(map(str, range(from_par, to_par+1))))
                        else:
                            dependent_parameters.append(item)

                    #                    # Map parameters
                    #                    split_line = [CMEMSparameters().get_smhi_code(par) for par in split_line]
                    # print(primary_parameter, type(primary_parameter))
                    # print('dependent_parameters'.upper(), dependent_parameters)
                    self['dependencies'][primary_parameter] = dependent_parameters

            # ------------------------------------------------------------------
            elif key.lower() == 'ranges':
                self['ranges'] = {}
                for i, line in enumerate(self.data[key]):
                    split_line = [item.strip() for item in line.split(u'\t')]
                    if i == 0:
                        header = [item.lower() for item in split_line]
                    else:
                        limit_dict = dict(zip(header, split_line))
                        par = split_line[header.index('parameter')]
                        self['ranges'][par] = {}
                        #                        print header
                        for limit in [item for item in header if item != 'parameter']:
                            if limit_dict[limit]:
                                value = float(limit_dict[limit])
                                self['ranges'][par][limit] = value

            # ------------------------------------------------------------------
            elif key.lower() == 'parameter mapping':
                self.parameter_mapping = self.MappingObject(self.data[key], self.root_directory)

            # ------------------------------------------------------------------
            elif key.lower() == 'station mapping':
                self.station_mapping = self.MappingObject(self.data[key], self.root_directory)
            # ------------------------------------------------------------------
            elif key.lower() == 'info':
                self.info = self.MappingObject(self.data[key], self.root_directory)

            # ------------------------------------------------------------------
            elif key.lower() == 'column':
                self.column = self.MappingObject(self.data[key], self.root_directory)

            # ------------------------------------------------------------------
            elif key.lower() == 'matching criteria':
                self.matching_criteria = self.MappingObject(self.data[key], self.root_directory)

            # ------------------------------------------------------------------
            elif key.lower() == 'map':
                self.map = self.MappingObject(self.data[key], self.root_directory)

    # ==================================================================
    def get_flag_list(self):
        return self.flag_list

    # ==================================================================
    def get_flag_description(self, flag):
        return self['flags'][flag]['description']

    # ==================================================================
    def get_flag_description_list(self):
        return [self.get_flag_description(flag) for flag in self.flag_list]

    # # ==================================================================
    # def get_flag_color(self, flag):
    #     return self['flags'][flag]['color']
    #
    # # ==================================================================
    # def get_flag_color_list(self):
    #     return [self.get_flag_color(flag) for flag in self.flag_list]
    #
    # # ==================================================================
    # def get_flag_markersize(self, flag):
    #     return self['flags'][flag]['markersize']
    #
    # # ==================================================================
    # def get_flag_markersize_list(self):
    #     return [self.get_flag_markersize(flag) for flag in self.flag_list]
    #
    # # ==================================================================
    # def get_flag_marker(self, flag):
    #     return self['flags'][flag]['marker']
    #
    # # ==================================================================
    # def get_flag_marker_list(self):
    #     return [self.get_flag_marker(flag) for flag in self.flag_list]

    # ==================================================================
    def get_flag_from_description(self, description):
        return self.description_to_flag[description]

    # ==================================================================
    def get_flag_prop_dict(self, flag):
        flag = str(flag)
        if self:
            dont_include = ['qf', 'description']
            # print('='*50)
            # print(self['flags'][flag])
            # print('=' * 50)
            return {par: item for par, item in self['flags'][flag].items() if par not in dont_include}
        else:
            return {}

    # ==================================================================
    def _get_default_dict(self):
        pass


# ==============================================================================
# ==============================================================================
class SHARKfilePhysicalChemichal(GISMOfile):
    """
    Class to hold data from SHARK (Svenskt HAvsaRKiv).
    """

    # ==========================================================================
    def __init__(self, data_file_path=None, settings_file_path=None, root_directory=None, **kwargs):
        """
        Updated 20181005

        :param data_file_path:
        :param settings_file_path:
        :param root_directory:
        :param kwargs:
        """
        kwargs.update(dict(data_file_path=data_file_path,
                           settings_file_path=settings_file_path,
                           root_directory=root_directory))
        GISMOfile.__init__(self, **kwargs)

        self.filter_data_options = self.filter_data_options + ['time', 'time_start', 'time_end', 'visit_id', 'visit_depth_id']
        self.flag_data_options = []
        self.mask_data_options = self.mask_data_options + []


# ==============================================================================
def latlon_distance_array(lat_point, lon_point, lat_array, lon_array):
    '''
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    '''

    # convert decimal degrees to radians
    lat_point = np.radians(lat_point)
    lon_point = np.radians(lon_point)
    lat_array = np.radians(lat_array)
    lon_array = np.radians(lon_array)

    # haversine formula
    dlat = lat_array - lat_point
    dlon = lon_array - lon_point
    a = np.sin(dlat / 2.) ** 2 + np.cos(lat_point) * np.cos(lat_array) * np.sin(dlon / 2.) ** 2

    c = 2 * np.arcsin(np.sqrt(a))
    # km = 6367 * c
    km = 6363 * c  # Earth radius at around 57 degrees North
    return km


# ==============================================================================
# ==============================================================================
def latlon_distance(origin, destination):
    '''
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    '''
    from math import radians, cos, sin, asin, sqrt
    lat1, lon1 = origin
    lat2, lon2 = destination
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2.) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2.) ** 2
    c = 2 * asin(sqrt(a))
    # km = 6367 * c
    km = 6363 * c  # Earth radius at around 57 degrees North
    return km


# ==============================================================================
# ==============================================================================
def old_get_matching_sample_index(sample_object=None,
                                  gismo_object=None,
                                  modulus=None,
                                  diffs=None):
    if not all([sample_object, gismo_object]):
        return

    time_diff = diffs['time']
    dist_diff = diffs['dist']
    depth_diff = diffs['depth']

    # First reduce gismo dataframe.
    # This can be done by only inluding data that is close enough to the sample stations.
    #    unique_positions

    all_index = []
    # Loop values
    for i, [t, la, lo, d] in enumerate(zip(gismo_object.df.time,
                                           gismo_object.df.lat,
                                           gismo_object.df.lon,
                                           gismo_object.df.depth)):
        #        if i < 20:
        #            continue
        if modulus and i % modulus:
            continue

        #        print i

        # Depth: Get index for matching depth criteria to reduce loop length
        df = sample_object.df.ix[(sample_object.df.depth >= d - depth_diff) & \
                                 (sample_object.df.depth <= d + depth_diff), :]

        #        index_list = np.array(df.index)
        #        print 'len(df)', len(df)

        # Loop index and and save index
        for index in df.index:
            if index in all_index:
                #                print 'Index already added'
                continue

            time = df.ix[index, 'time']
            lat = df.ix[index, 'lat']
            lon = df.ix[index, 'lon']
            #            print abs((time-t).total_seconds() / 60)
            #            print time_diff
            #            print abs((time-t).total_seconds() / 60) > time_diff
            if abs((time - t).total_seconds() / 60) > time_diff:
                # Continue if no match
                #                print 'No match for time'
                continue

            if (latlon_distance([la, lo], [lat, lon]) * 1000) > dist_diff:
                # Continue if no match
                #                print 'No match for distance'
                continue

            # If this line i reached we have a match. Add this to all_index
            print('Match for index:', index)
            all_index.append(index)

    return sorted(all_index)


# ==============================================================================
# ==============================================================================
def old_get_matching_sample_index(sample_object=None,
                              gismo_object=None,
                              diffs=None):
    if not all([sample_object, gismo_object]):
        return

    time_diff = diffs['time']
    dist_diff = diffs['dist']
    depth_diff = diffs['depth']

    # --------------------------------------------------------------------------
    # First reduce sample dataframe.
    # Make new column in sample dataframe to get position string
    df = sample_object.df

    df['pos_str'] = df['lat'].map(str) + df['lon'].map(str)
    pos_list = list(set(df['pos_str']))

    all_index = []

    # Loop position list
    for pos in pos_list:
        pos_df = df.ix[df.pos_str == pos, :]
        pos_index = pos_df.index[0]
        la = pos_df.ix[pos_index, 'lat']
        lo = pos_df.ix[pos_index, 'lon']
        t = pos_df.ix[pos_index, 'time']

        # Check distanse to all points in gismo_object.df
        distance = latlon_distance_array(la, lo, gismo_object.df.lat, gismo_object.df.lon) * 1000

        # Get boolean index for valid distance
        boolean_distance = distance <= dist_diff

        # Check if any point in distance is within reach
        if not np.any(boolean_distance):
            continue

        ### Getting this far garantees that staton is within distance.

        # Check time to all points in gismo_object.df
        time_delta = np.array(map(datetime.timedelta.total_seconds, np.abs(gismo_object.df.time - t))) / 60

        # Get boolean index for valid time
        boolean_time = time_delta <= time_diff

        # Check if any point in time is within reach
        if not np.any(boolean_time):
            continue

        ### If we gotten this far we have match for both time and distance.
        ### But it migth not be the same match. Check this now.

        boolean_dist_time = boolean_distance & boolean_time

        # Check if any point match in both time and distance
        if not np.any(boolean_dist_time):
            continue

        ### We have a match for both time and distance
        ### Now we check agains depth

        for i, d in pos_df.depth.iteritems():
            depth_difference = abs(gismo_object.df.depth - d)
            boolean_depth = depth_difference <= depth_diff

            # Save index if any match for depth
            if np.any(boolean_depth):
                if i not in all_index:
                    all_index.append(i)

    return sorted(all_index)


def apply_datetime_object_to_df(x):
    """
    Used to apply datetime object to a pandas dataframe.
    :param x:
    :return:
    """
    time_formats = ['%Y%m%d%H%M%S',
                    '%Y%m%d%H%M',
                    '%Y%m%d%H:%M',
                    '%Y%m%d%H.%M',
                    '%Y-%m-%d%H%M',
                    '%Y-%m-%d%H:%M',
                    '%Y-%m-%d%H.%M',
                    '%Y%m%d',
                    '%Y-%m-%d']
    if type(x) == str:
        x = [x]
    time_string = ''.join([str(item) for item in x])
    d_obj = None
    for tf in time_formats:
        try:
            d_obj = datetime.datetime.strptime(time_string, tf)
            return d_obj
        except:
            pass

    raise GISMOExceptionInvalidTimeFormat('Could not find matching time format for "{}"'.format(time_string))