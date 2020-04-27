#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import codecs
import datetime

try:
    import pandas as pd
    import numpy as np
except:
	pass

from . import QCprofile
from ...gismo.exceptions import *
from ...import utils
from sharkpylib.file.file_handlers import MappingDirectory

import logging
gismo_logger = logging.getLogger('gismo_session')


class ProfileQCrangeSimple(object):
    """
    Class to perform simple range check on a profile gismo object. This class does not take depth into consideration.
    """
    def __init__(self, **kwargs):
        self.qc_object = QCprofile.QC()
        self.range_files_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  'data', 'simple_range')

        self.limit_object = QCrangeDirectory(self.range_files_directory)
        self.options = {'ignore_qf': ['B', 'S', '?'],
                        'parameter_list': self.limit_object.get_parameter_list()}

    def run_qc(self, gismo_objects, **kwargs):
        parameter_list = kwargs.get('parameter_list')
        if not parameter_list:
            gismo_logger.warning('No parameter list given in options while running qc. Qc not performed')
            return False

        invalid_pars = [par for par in parameter_list if par not in self.options['parameter_list']]
        if invalid_pars:
            raise GISMOExceptionInvalidParameter(invalid_pars)

        if type(gismo_objects) != list:
            gismo_objects = [gismo_objects]

        for gismo_object in gismo_objects:
            # Parameter list does not need to exactly match tha parameter names in gismo object.
            par_mapping = gismo_object.get_dict_with_matching_parameters(parameter_list)

            # print('par_mapping', par_mapping)
            par_list = list(par_mapping) + ['depth']

            data = gismo_object.get_data(*par_list)
            qf_data = gismo_object.get_qf_list(*par_list)
            t = gismo_object.get_time()[0]


            for par in qf_data:
                limit_par = par_mapping.get(par)
                # limit_par = par
                # if limit_par not in self.limit_object.parameters:
                #     for alt_par in self.limit_object.parameters:
                #         if alt_par in limit_par:
                #             limit_par = alt_par
                #             break

                qf_list = list(qf_data[par])
                limits = self.limit_object.get_limit(limit_par, 'range_min', 'range_max', time=t)
                all_depths = list(data['depth'])
                if limits is not None:
                    result = self.qc_object.range_check(data=list(data[par]),
                                                        qf=qf_list,
                                                        lower_limit=limits['range_min'],
                                                        upper_limit=limits['range_max'],
                                                        depth=all_depths,
                                                        max_depth=False,
                                                        min_depth=False,
                                                        qf_ignore=kwargs.get('ignore_qf',  ['B', 'S', '?']))
                    qfindex, new_qf, qfindex_numeric = result

                    kw = dict()
                    for k in kwargs:
                        if k in gismo_object.flag_data_options:
                            kw[k] = kwargs[k]

                    # Flag each flag
                    for qf in set(new_qf):
                        flag_boolean = np.array(new_qf) == qf
                        flag_depth = np.array(all_depths)[flag_boolean]
                        # Flag data
                        gismo_object.flag_data(qf, par, depth=flag_depth, **kw)
                        # gismo_object.df[qf_par] = qf_list


class ProfileQCreportTXT(object):
    """
    Class to perform density checks on gismo object. Result is written to file.
    """

    def __init__(self):
        self.qc_object = QCprofile.QC()
        self.calc_dens_par_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  'data', 'calc_density_parameters.txt')

        self.options = {'ignore_qf': ['B', 'S', '?'],
                        'min_density_delta': 0.01,
                        'save_directory': str,
                        'user': str,
                        'gismo_version': str,
                        'subroutines': ['increasing density']}
        self._load_data()


    def _load_data(self):
        self.calc_dens_par_info = QCdensityFile(self.calc_dens_par_file_path)

    def run_qc(self, gismo_objects, **kwargs):
        if not kwargs.get('save_directory'):
            raise GISMOExceptionMissingPath('No directory provided in options')

        # Loop subroutines
        if type(gismo_objects) != list:
            gismo_objects = [gismo_objects]

        objects = dict((item.file_id, item) for item in gismo_objects)
        t = datetime.datetime.now()
        time_str1 = t.strftime('%Y%m%d%H%M')
        time_str2 = t.strftime('%Y-%m-%d %H:%M')
        file_name = 'gismo_qc_report_{}.txt'.format(time_str1)
        directory = kwargs.get('save_directory')
        try:
            file_path = os.path.join(directory, file_name)
        except TypeError as e:
            raise GISMOExceptionInvalidOption(e)

        ignore_qf = list(kwargs.get('ignore_qf', ['B', 'S', '?']))

        line_len = 100

        if not os.path.exists(directory):
            os.makedirs(directory)

        with codecs.open(file_path, 'w') as fid:
            # Write header
            fid.write('Report on automatic quality control performed: {}\n'.format(time_str2))
            fid.write('Employee: {}\n'.format(utils.get_employee_name()))
            fid.write('User: {}\n'.format(kwargs.get('user', '')))
            fid.write('GISMO version: {}\n'.format(kwargs.get('gismo_version', '')))
            fid.write('Ignoring quality flags: {}\n'.format(', '.join(ignore_qf)))
            fid.write('\nFiles controlled:\n{}\n'.format('\n'.join(sorted(objects))))
            fid.write('=' * line_len)
            fid.write('\n')

            for file_id in sorted(objects):
                gismo_object = objects.get(file_id)
                fid.write('\n\n')
                fid.write('-' * line_len)
                fid.write('\nFile id: {}\n'.format(file_id))
                for subroutine in kwargs.get('subroutines'):
                    # Increasing density
                    if subroutine.lower() == 'increasing density':
                        for item in self.calc_dens_par_info.get_parameters_from_list(gismo_object.get_parameter_list()):
                            parameters = list(item.values())
                            data = gismo_object.get_data(*parameters)
                            qf_data = gismo_object.get_qf_list(*parameters)
                            min_delta = float(kwargs.get('min_density_delta', 0.01))
                            result = self.qc_object.increasing_dens(temperature=data[item.get('temperature')],
                                                                    qtemp=qf_data[item.get('temperature')],
                                                                    salinity=data[item.get('salinity')],
                                                                    qsalt=qf_data[item.get('salinity')],
                                                                    pressure=data[item.get('pressure')],
                                                                    qpres=qf_data[item.get('pressure')],
                                                                    min_delta=min_delta,
                                                                    qf_ignore=ignore_qf)
                            qfindex, new_qf, qfindex_numeric = result

                            nr_err = len(np.where(qfindex)[0])
                            if any(qfindex):
                                fid.write('Density not increasing with depth: {} '
                                          'values out of delta range {}. '
                                          'Parameters used for calculation are {}\n'.format(nr_err,
                                                                                            min_delta,
                                                                                            ', '.join(sorted(item.values()))))
            return True


class QCrangeDirectory(object):
    """
    Base class to handle ranges for qc for profile data.
    """
    def __init__(self, qc_file_directory):
        self.qc_file_directory = qc_file_directory

        self.parameters = {}
        self.file_objects = {}

        self._list_files()

    def _list_files(self):
        """
        List files in directory.
        :return:
        """
        all_files = os.listdir(self.qc_file_directory)
        for file_name in all_files:
            par = os.path.splitext(file_name)[0]
            self.parameters[par] = os.path.join(self.qc_file_directory, file_name)

    def _add_file(self, par, **kwargs):
        if not self.parameters.get(par):
            return None
        self.file_objects[par] = QCrangeFile(self.parameters.get(par), **kwargs)

    def get_limit(self, par, *args, **kwargs):
        """
        Returns the limit for items in args specified for parameter par. Filter is given as kwargs, options are:
        time (datetime objects)
        lat
        lon
        depth

        If not limit found None is returned.

        :param par:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.parameters.get(par):
            return None

        if not self.file_objects.get(par):
            self._add_file(par)

        file_object = self.file_objects.get(par)

        return file_object.get_limit(*args, **kwargs)

    def get_parameter_list(self):
        return sorted(self.parameters)


class QCrangeFile(object):
    """
    Class to read and hold information from a column ascii file containing information about limits for QC.
    a water column profile.

    File name should be equal to parameter name!

    File must have the following columns:
    month
    lat_min
    lat_max
    lon_min
    lon_max
    (depth_min)
    (depth_max)

    """
    def __init__(self, file_path, **kwargs):
        self.file_path = file_path
        self.par = os.path.splitext(os.path.basename(self.file_path))[0]

        # Load file
        kw = dict(sep='\t',
                  encoding='cp1252')
        kw.update(kwargs)
        self.df = pd.read_csv(file_path, **kw)

    def _get_boolean_for_datetime_object(self, datetime_object):
        """
        Checks month in datetime object.

        :param value:
        :return:
        """
        datetime_object = pd.to_datetime(datetime_object)
        return self.df['month'] == datetime_object.month

    def _get_boolean_for_lat(self, lat):
        """
        :param lat:
        :return:
        """
        return (lat >= self.df['lat_min']) & (lat < self.df['lat_max'])

    def _get_boolean_for_lon(self, lon):
        """
        :param lon:
        :return:
        """
        return (lon >= self.df['lon_min']) & (lon < self.df['lon_max'])

    def _get_boolean_for_depth(self, depth):
        """
        :param depth:
        :return:
        """
        depth = abs(depth)
        return  (depth >= self.df['depth_min']) & (depth < self.df['depth_max'])


    def get_limit(self, *args, **kwargs):
        """
        Returns the float value of items in args based on the filter given in kwargs.
        :param item:
        :param kwargs:
        :return:
        """

        tot_boolean = np.ones(len(self.df), dtype=bool)

        # Time
        if kwargs.get('time'):
            tot_boolean = tot_boolean & self._get_boolean_for_datetime_object(kwargs.get('time'))

        # Position
        if kwargs.get('lat'):
            tot_boolean = tot_boolean & self._get_boolean_for_lat(kwargs.get('lat'))
        if kwargs.get('lon'):
            tot_boolean = tot_boolean & self._get_boolean_for_lon(kwargs.get('lon'))

        # Depth
        if kwargs.get('depth'):
            tot_boolean = tot_boolean & self._get_boolean_for_depth(kwargs.get('depth'))

        # Check that only one value is found
        len_match = len(np.where(tot_boolean)[0])
        if len_match == 0:
            return {}
        elif len_match > 1:
            raise GISMOExceptionQCmissingInformation

        # Find match
        return_dict = {}
        for item in args:
            if item in self.df.columns:
                return_dict[item] = self.df.loc[tot_boolean, item].values[0]
        return return_dict


class QCdensityFile(object):
    """
    Reads a column ascii file containing combinations of parameters that should be used to calculate density.
    columns should be:
    salinity_parameter
    temperatur_parameter
    pressure_parameter
    """

    def __init__(self, file_path, **kwargs):
        self.file_path = file_path

        # Load file
        self.data_list = []
        with codecs.open(self.file_path, encoding=kwargs.get('encoding', 'cp1252')) as fid:
            for k, line in enumerate(fid):
                line = line.strip()
                if not line:
                    continue
                split_line = line.split(kwargs.get('sep', '\t'))
                if k == 0:
                    header = split_line
                else:
                    line_dict = dict(zip(header, split_line))
                    self.data_list.append(line_dict)

    def get_parameters_from_list(self, parameter_list):
        """
        Returns a list och dicts. Each dict is a match of the parameters that can be used for calculating density.
        :param parameter_list:
        :return:
        """
        return_list = []
        for item in self.data_list:
            if all([value in parameter_list for value in item.values()]):
                return_list.append(item.copy())
        return return_list

