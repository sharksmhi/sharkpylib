# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import os
import codecs

class ODVdirectory(object):
    def __init__(self, directory, **kwargs):
        self.directory = directory
        self.file_paths = []
        self._load_file_paths()

    def _load_file_paths(self):
        print('yes')
        self.file_paths = [os.path.join(self.directory, file_name) for file_name in os.listdir(self.directory) if file_name.endswith('.txt')]

    def get_files_with_string(self, string):
        return [file_path for file_path in self.file_paths if ODVfile(file_path).has_string(string)]

    def get_mapping_of_primary_variable(self, **kwargs):
        mapping = dict()
        for file_path in self.file_paths:
            file_object = ODVfile(file_path, **kwargs)
            primary_variable = file_object.get_primary_variable()
            mapping.setdefault(primary_variable, [])
            if kwargs.get('whole_path'):
                mapping[primary_variable].append(file_path)
            else:
                mapping[primary_variable].append(os.path.basename(file_path))
        return mapping


class ODVfile(object):
    def __init__(self, file_path, **kwargs):
        self.file_path = file_path
        self.header_locator = kwargs.get('header_locator', 'Cruise')
        self.last_metadata_variable = kwargs.get('last_metadata_variable', 'Bot. Depth [m]')

    def has_string(self, string):
        with codecs.open(self.file_path) as fid:
            text = fid.read()
            # print(text)
            # Check old P011
            if 'P011' in text:
                print('Old p-code P011 found in file {}'.format(self.file_path))
            if string in text:
                return True
            return False

    def get_primary_variable(self):
        """
        Primary variable is the first variable after the last metadata variable. Last metadata variable is by default
        self.last_metadata_variable.

        :return: primary variable of the file
        """
        with codecs.open(self.file_path) as fid:
            for line in fid:
                if line.startswith(self.header_locator):
                    split_line = line.split('\t')
                    for k, col in enumerate(split_line):
                        if col == self.last_metadata_variable:
                            return split_line[k+1]
