#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import codecs

from ...gismo.exceptions import *


class FlagAreas(object):
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.flag_object = FlagAreasFile(self.file_path)

    def run_qc(self, gismo_object, par_list=[], flag='4'):
        """
        Sets areas described in self.flag_area_file_object to flag

        :param df: pandas.DataFrame
        :param parameter_list: Parameters to flag.
        :param flag: flag to set in areas
        :return:
        """
        df = gismo_object.df
        flag = str(flag)
        areas = self.flag_object.get_areas()

        df.to_csv(r'D:\temp_gismo/before.txt', index=False, sep='\t')

        # Create boolean to flag
        combined_boolean = df['lat'] == ''
        for name, area in areas.items():
            lat_min = area.get('lat_min')
            lat_max = area.get('lat_max')
            lon_min = area.get('lon_min')
            lon_max = area.get('lon_max')

            boolean = (df['lat'].astype(float) >= lat_min) & \
                      (df['lat'].astype(float) <= lat_max) & \
                      (df['lon'].astype(float) >= lon_min) & \
                      (df['lon'].astype(float) <= lon_max)
            # print(len(np.where(boolean)))
            combined_boolean = combined_boolean | boolean
        # Flag data
        time_list = df.loc[combined_boolean, 'time'].values
        gismo_object.flag_data(flag, *par_list, time=time_list)

        df.to_csv(r'D:\temp_gismo/after.txt', index=False, sep='\t')


class FlagAreasFile(object):
    def __init__(self, file_path):
        if not os.path.exists(file_path):
            raise GISMOExceptionInvalidPath
        self.file_path = file_path

        self.areas = {}
        self._load_file()

    def _load_file(self, **kw):
        with codecs.open(self.file_path, 'r') as fid:
            for k, line in enumerate(fid):
                if not line.strip():
                    continue
                line = line.strip('\r\n')
                split_line = line.split('\t')
                if k==0:
                    header = split_line
                else:
                    line_dict = dict(zip(header, split_line))
                    self.areas[line_dict['name']] = {}
                    for key, value in line_dict.items():
                        if key == 'name':
                            continue
                        self.areas[line_dict['name']][key] = float(value)

    def get_areas(self):
        return self.areas