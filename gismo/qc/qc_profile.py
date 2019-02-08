#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).



import os
import pandas as pd
import numpy as np
import codecs
import datetime

import gismo
from gismo.exceptions import *
from gismo.qc import QCprofile

import logging
logger = logging.getLogger('gismo_session')


class ProfileQCrangeSimple(object):
    """
    Class to perform simple range check on a profile gismo object. This class does not take depth into consideration.
    """

    def __init__(self, **kwargs):
        self.qc_object = gismo.QCprofile.QC()
        self.range_files_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  'data', 'simple_range')

        self.subroutines = []
        self.options = ['ignore qf']

        self._load_data()

    def _load_data(self):
        self.limit_object = QCrangeDirectory(self.range_files_directory)

    def run_qc(self, gismo_object, parameter_list=[], options={}):
        if not parameter_list:
            logger.warning('No parameter list given in options while running qc. Qc not performed')
            return False

        data = gismo_object.get_data(*parameter_list)
        qf_data = gismo_object.get_qf_list(*parameter_list)
        t = gismo_object.get_time()[0]

        for par in qf_data:
            limit_par = par
            if limit_par not in self.limit_object.parameters:
                for alt_par in self.limit_object.parameters:
                    if alt_par in limit_par:
                        limit_par = alt_par
                        break

            qf_list = list(qf_data[par])
            limits = self.limit_object.get_limit(limit_par, 'range_min', 'range_max', time=t)
            if limits is not None:
                result = self.qc_object.range_check(data=list(data[par]),
                                                    qf=qf_list,
                                                    lower_limit=limits['range_min'],
                                                    upper_limit=limits['range_max'],
                                                    depth=list(data['depth']),
                                                    max_depth=False,
                                                    min_depth=False,
                                                    qf_ignore=options.get('ignore qf',  ['B', 'S', '?']))
                qfindex, new_qf, qfindex_numeric = result
                qf_list = list(new_qf)
                # Update qf list in df
                qf_par = gismo_object.get_qf_par(par)
                gismo_object.df[qf_par] = qf_list


class ProfileQCreportTXT(object):
    """
    Class to perform density checks on gismo object. Result is written to file.
    """

    def __init__(self):
        self.qc_object = gismo.QCprofile.QC()
        self.calc_dens_par_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  'data', 'calc_density_parameters.txt')

        self.subroutines = ['increasing density']
        self.options = ['ignore qf', 'min density delta', 'save directory', 'user', 'gismo version']
        self._load_data()


    def _load_data(self):
        self.calc_dens_par_info = QCdensityFile(self.calc_dens_par_file_path)

    def run_qc(self, gismo_objects, subroutines=[], options={}, save_directory=''):
        if not save_directory:
            raise GISMOExceptionMissingPath('No directory provided in options')

        # Loop subroutines
        if type(gismo_objects) != list:
            gismo_objects = [gismo_objects]

        objects = dict((item.file_id, item) for item in gismo_objects)
        t = datetime.datetime.now()
        time_str1 = t.strftime('%Y%m%d%H%M')
        time_str2 = t.strftime('%Y-%m-%d %H:%M')
        file_name = 'gismo_qc_report_{}.txt'.format(time_str1)
        file_path = os.path.join(save_directory, file_name)

        ignore_qf = list(options.get('ignore qf', ['B', 'S', '?']))

        line_len = 100

        with codecs.open(file_path, 'w') as fid:
            # Write header
            fid.write('Report on automatic quality control performed: {}\n'.format(time_str2))
            fid.write('User: {}\n'.format(options.get('user', '')))
            fid.write('GISMO version: {}\n'.format(options.get('gismo version', '')))
            fid.write('Ignoring quality flags: {}\n'.format(', '.join(ignore_qf)))
            fid.write('\nFiles controlled:\n{}\n'.format('\n'.join(sorted(objects))))
            fid.write('=' * line_len)
            fid.write('\n')

            for file_id in sorted(objects):
                gismo_object = objects.get(file_id)
                fid.write('\n\n')
                fid.write('-' * line_len)
                fid.write('\nFile id: {}\n'.format(file_id))
                for subroutine in subroutines:
                    # Increasing density
                    if subroutine.lower() == 'increasing density':
                        for item in self.calc_dens_par_info.get_parameters_from_list(gismo_object.get_parameter_list()):
                            parameters = list(item.values())
                            data = gismo_object.get_data(*parameters)
                            qf_data = gismo_object.get_qf_list(*parameters)
                            min_delta = options.get('min density delta', 0.01)
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

