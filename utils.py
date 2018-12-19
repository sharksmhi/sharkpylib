# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import matplotlib.colors as mcolors
from matplotlib import markers


class ColorsList(list):

    def __init__(self):
        list.__init__(self)
        for color in sorted(self.get_base_colors() + self.get_tableau_colors() + self.get_css4_colors()):
            self.append(color)

    def _filter_color_list(self, color_list):
        new_color_list = []
        for color in color_list:
            if color.startswith('tab:'):
                continue
            if len(color) == 1:
                continue
            new_color_list.append(color)
        return sorted(new_color_list)

    def get_base_colors(self):
        return self._filter_color_list(mcolors.BASE_COLORS)

    def get_tableau_colors(self):
        return self._filter_color_list(mcolors.TABLEAU_COLORS)

    def get_css4_colors(self):
        return self._filter_color_list(mcolors.CSS4_COLORS)


class MarkerList(list):
    def __init__(self):
        list.__init__(self)
        temp_list = markers.MarkerStyle.markers.keys()
        self.marker_to_description = {}
        self.description_to_marker = {}
        for marker in temp_list:
            description = str(markers.MarkerStyle.markers[marker])
            marker = str(marker)
            self.marker_to_description[marker] = description
            self.description_to_marker[description] = marker

        for marker in sorted(self.marker_to_description.keys()):
            self.append(marker)

    def get_description(self, marker):
        return self.marker_to_description.get(marker, marker)

    def get_marker(self, description):
        return self.description_to_marker.get(description, description)

