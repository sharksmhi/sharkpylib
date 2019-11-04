# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import os

SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'settings_files')

class SettingsFiles(object):

    def __init__(self, file_type='json', *directories):
        self.file_type = file_type
        self.main_directory = SETTINGS_FILE_PATH
        self.external_directories = set()
        self.files = {}
        self.file_per_directory = {}

        for d in directories:
            self._add_directory(d)
        self._load_files()

    def __str__(self):
        all_dirs = self._get_directories()
        return 'Settings files listed in directories: {}\n\n{}'.format('\n'.join(all_dirs), '\n'.join(sorted(self.files)))

    def __repr__(self):
        return f'{self.__class__.__name__}'

    def _get_directories(self):
        return [self.main_directory] + list(self.external_directories)

    def _load_files(self, directory=None):
        if directory:
            dirs = [directory]
        else:
            dirs = self._get_directories()

        end = len(self.file_type) + 1
        for d in dirs:
            self.file_per_directory[d] = []
            for file_name in os.listdir(d):
                if file_name.endswith(self.file_type):
                    file_path = os.path.join(d, file_name)
                    self.files[file_name[:-end]] = file_path
                    self.file_per_directory[d].append(file_name[:-end])

    def _add_directory(self, directory):
        self.external_directories.add(directory)

    def add_directory(self, directory):
        self._add_directory(directory)
        self._load_files(directory)

    def get_list(self):
        return sorted(self.files)

    def get_path(self, file_base):
        return self.files.get(file_base, None)



