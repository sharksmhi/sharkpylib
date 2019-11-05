# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import os

SETTINGS_FILES_DIRECTORY = os.path.join(os.path.dirname(__file__), 'settings_files')
MAPPING_FILES_DIRECTORY = os.path.join(os.path.dirname(__file__), 'mapping_files')


class Files(object):

    def __init__(self, main_directory, file_type, *directories):
        self.main_directory = main_directory
        self.file_type = file_type
        self.external_directories = set()
        self.files = {}
        self.file_per_directory = {}

        for d in directories:
            self._add_directory(d)
        self._load_files()

    def __str__(self):
        all_dirs = self._get_directories()
        return 'Settings files listed in directories:\n{}\n\n{}'.format('\n'.join(all_dirs), '\n'.join(sorted(self.files)))

    def __repr__(self):
        return '{}\n{}'.format(self.__class__.__name__, '\n'.join(sorted(self.files)))

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

    def get_path(self, file_name):
        file_base = file_name.split('.')[0]
        return self.files.get(file_base, None)


class SettingsFiles(Files):

    def __init__(self, *directories):
        Files.__init__(self, SETTINGS_FILES_DIRECTORY, 'json', *directories)


class MappingFiles(Files):

    def __init__(self, *directories):
        Files.__init__(self, MAPPING_FILES_DIRECTORY, 'txt', *directories)


