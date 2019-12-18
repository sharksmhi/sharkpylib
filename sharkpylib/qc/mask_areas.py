#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import numpy as np
from sharkpylib.file.file_handlers import Directory
from sharkpylib.geography import latlon_distance


class MaskAreasDirectory(object):
    def __init__(self):
        self.files_object = Directory(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data'), prefix='mask_areas')

    def get_file_object(self, file_id):
        file_path = self.files_object.get_path(file_id)
        return MaskAreas(file_path)


class MaskAreas(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = []

        self._load_file()

    def _load_file(self):
        with open(self.file_path) as fid:
            for r, line in enumerate(fid):
                line = line.strip()
                if not line:
                    continue
                split_line = [item.strip() for item in line.split('\t')]
                if r == 0:
                    header = split_line
                else:
                    self.data.append(dict(zip(header, map(float, split_line))))

    def get_masked_boolean(self, lat_list, lon_list):
        if len(lat_list) != len(lon_list):
            raise ValueError('Input lists son the same length!')
        combined_boolean = np.zeros(len(lat_list), dtype=bool)
        dist = []  # save distance in meters
        for item in self.data:
            for la, lo in zip(lat_list, lon_list):
                dist.append(latlon_distance((item['lat'], item['lon']), (la, lo))*1000)
            boolean = np.array(dist) <= float(item['radius'])
            combined_boolean = combined_boolean | boolean
        return combined_boolean


if __name__ == '__main__':
    mask_dir = MaskAreasDirectory()
    mask_obj = mask_dir.get_file_object('mask_areas_tavastland.txt')

    lat_list = [63.41, 66.31, 63.36, 63.11, 63.61, 65.31]
    lon_list = [19.1, 19.2, 19.14, 19.3, 18.14, 19.9]
    b = mask_obj.get_masked_boolean(lat_list, lon_list)
    print(b)
