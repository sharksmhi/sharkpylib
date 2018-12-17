# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import matplotlib.colors as mcolors


class ColorsList(list):

    def __init__(self):
        list.__init__(self)
        for color in sorted(self.get_base_colors() + self.get_tableau_colors() + self.get_css4_colors()):
            self.append(color)

    def _filer_collor_list(self, color_list):
        new_color_list = []
        for color in color_list:
            if color.startswith('tab:'):
                continue
            if len(color) == 1:
                continue
            new_color_list.append(color)
        return sorted(new_color_list)

    def get_base_colors(self):
        return self._filer_collor_list(mcolors.BASE_COLORS)

    def get_tableau_colors(self):
        return self._filer_collor_list(mcolors.TABLEAU_COLORS)

    def get_css4_colors(self):
        return self._filer_collor_list(mcolors.CSS4_COLORS)

