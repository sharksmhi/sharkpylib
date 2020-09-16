# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import re
import os
import socket
from collections import Mapping
import json
import codecs
import pathlib
import datetime
import platform


try:
    import matplotlib.colors as mcolors
    from matplotlib import markers
except:
    pass


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


def sorted_int(list_to_sort):
    """
    Sorts the given list interpreting the digits as integers.
    Code based on:
    https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside

    :param list_to_sort:
    :return: sorted list
    """
    def atoi(text):
        return int(text) if text.isdigit() else text

    def natural_keys(text):
        '''
        alist.sort(key=natural_keys) sorts in human order
        http://nedbatchelder.com/blog/200712/human_sorting.html
        (See Toothy's implementation in the comments)
        '''
        return [atoi(c) for c in re.split('(\d+)', text)]

    return sorted(list_to_sort, key=natural_keys)


def get_computer_name():
    return socket.gethostname()


def get_employee_name():
    return os.path.expanduser('~').split('\\')[-1]


def get_time_as_format(**kwargs):
    d = None
    if kwargs.get('now'):
        d = datetime.datetime.now()
    elif kwargs.get('timestamp'):
        raise NotImplementedError

    if not d:
        raise ValueError

    if kwargs.get('fmt'):
        return d.strftime(kwargs.get('fmt'))
    else:
        raise NotImplementedError


def recursive_dict_update(d, u):
    """ Recursive dictionary update using
    Copied from:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        via satpy
    """
    if isinstance(u, dict):
        for k, v in u.items():
            if isinstance(v, Mapping):
                r = recursive_dict_update(d.get(k, {}), v)
                d[k] = r
                # d.setdefault(k, r)
            else:
                d[k] = u[k]
                # d.setdefault(k, u[k])
    return d


def save_json(data, *args, **kwargs):
    """
    :param data:
    :param args: file path or parts of file path.
    :param kwargs: Options for json output format.
    :return:
    """
    file_path = os.path.join(*args)
    if not file_path.endswith('.json'):
        raise ValueError

    encoding = kwargs.pop('encoding', 'utf-8')

    kw = dict(sort_keys=True,
              indent='\t',
              separators=(',', ': '))
    kw.update(**kwargs)
    with codecs.open(file_path, 'w', encoding=encoding) as fid:
        json.dump(data, fid, **kw)


def load_json(*args, **kwargs):
    """
    :param args: file path or parts of file path.
    :return:
    """
    data = None
    file_path = os.path.join(*args)
    if not file_path.endswith('.json'):
        raise ValueError
    if kwargs.get('create_if_missing'):
        if not os.path.exists(file_path):
            save_json({}, file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError

    encoding = kwargs.pop('encoding', 'utf-8')
    with codecs.open(file_path, encoding=encoding) as fid:
        data = json.load(fid)
    return data


class PathInfo(object):
    def __init__(self, file_path):
        self.directory = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.file_base, self.extension = self.file_name.split('.')


def git_version():
    """
    Return current version of this github-repository
    :return: str
    """
    wd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    version_file = os.path.join(wd, '.git', 'FETCH_HEAD')
    if os.path.exists(version_file):
        f = open(version_file, 'r')
        version_line = f.readline().split()
        version = version_line[0][:7]  # Is much longer but only the first 7 letters are presented on Github
        repo = version_line[-1]
        return 'github version "{}" of repository {}'.format(version, repo)
    else:
        return ''


def get_windows_bit_version():
    return platform.architecture()[0][:2]


if __name__ == "__main__":
    v = git_version()
    print(v)
