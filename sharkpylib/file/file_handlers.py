# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import os
import re

from . import files

FILE_DIR = os.path.realpath(os.path.dirname(__file__))
# print(FILE_DIR)
DIRECTORIES = dict(mapping_files=os.path.join(FILE_DIR, 'mapping_files'),
                   synonym_files=os.path.join(FILE_DIR, 'synonym_files'),
                   list_files=os.path.join(FILE_DIR, 'list_files'),
                   multi_list_files=os.path.join(FILE_DIR, 'multilist_files'),
                   sampling_type_settings_files=os.path.join(FILE_DIR, 'sampling_type_settings_files'))

for d in DIRECTORIES.values():
    if not os.path.exists(d):
        os.mkdir(d)


class Directory(object):

    def __init__(self, main_directory, *directories, file_type='', match_string='', match_format='', prefix=''):
        self.main_directory = main_directory
        self.file_type = file_type.strip('.')
        self.match_string = match_string
        self.match_format = match_format
        self.prefix = prefix
        self.external_directories = set()
        self.files = {}
        self.file_per_directory = {}
        self.file_objects = {}

        for d in directories:
            self._add_directory(d)
        self._load_files()

    def __str__(self):
        all_dirs = self._get_directories()
        return '\nFiles listed in directories:\n{}\n\n{}\n'.format('\n'.join(all_dirs), '\n'.join(sorted(self.files)))

    def __repr__(self):
        return '{}\n{}'.format(self.__class__.__name__, '\n'.join(sorted(self.files)))

    def _get_directories(self):
        return [self.main_directory] + list(self.external_directories)

    def _load_files(self, directory=None):
        if directory:
            dirs = [directory]
        else:
            dirs = self._get_directories()

        if self.file_type:
            end = len(self.file_type) + 1
        else:
            end = 0
        for d in dirs:
            self.file_per_directory[d] = []
            for file_name in os.listdir(d):
                if not file_name.endswith(self.file_type):
                    continue
                if self.match_string not in file_name:
                    continue
                if self.match_format and not re.findall(self.match_format, file_name):
                    continue
                if not file_name.startswith(self.prefix):
                    continue
                file_path = os.path.join(d, file_name)
                if self.file_type:
                    self.files[file_name[:-end]] = file_path
                    self.file_per_directory[d].append(file_name[:-end])
                else:
                    self.files[file_name] = file_path
                    self.file_per_directory[d].append(file_name)

    def _add_directory(self, directory):
        self.external_directories.add(directory)

    def _add_file_object(self, file_id, file_object):
        self.file_objects[file_id] = file_object

    def add_directory(self, directory):
        self._add_directory(directory)
        self._load_files(directory)

    def get_list(self):
        return sorted(self.files)

    def get_file_list(self):
        return sorted(self.files)

    def get_path_list(self):
        return [self.get_path(f) for f in self.get_file_list()]

    def get_path(self, file_id):
        file_path = self.files.get(file_id, None)
        if not file_id:
            raise FileNotFoundError(f'Invalid file: {file_id}')
        return file_path

    def save_file(self, file_id):
        print(self.file_objects)
        print(file_id)
        if file_id not in self.file_objects:
            return
        if file_id in self.file_per_directory[self.main_directory]:
            raise FileExistsError(f'Not allowed to overwrite file in default directory: {self.main_directory}')

        self.file_objects[file_id].save()


class MappingDirectory(Directory):
    def __init__(self, *directories):
        """
        Class holds mapping files from the default mapping files directory. Also option to add additional directories in args.
        Mapping files has prefix "mapping_"

        :param directories: optional additional directories
        """
        super().__init__(DIRECTORIES.get('mapping_files'), *directories, prefix='mapping_')

    def get_columns_names_in_file(self, file_id):
        file_path = self.get_path(file_id)
        with open(file_path) as fid:
            line = fid.readline()
            return sorted([item.strip() for item in line.split('\t')])

    def get_file_object(self, file_id, **kwargs):
        file_path = self.get_path(file_id)
        file_object = files.MappingFile(file_path, **kwargs)
        self._add_file_object(file_id, file_object)
        return file_object


class SynonymDirectory(Directory):
    def __init__(self, *directories):
        """
        Class holds synonym files from the default synonym files directory. Also option to add additional directories in args.
        Synonym files has prefix "synonym_"

        :param directories: optional additional directories
        """
        super().__init__(DIRECTORIES.get('synonym_files'), *directories, prefix='synonym_')

    def get_file_object(self, file_id, **kwargs):
        file_path = self.get_path(file_id)
        file_object = files.SynonymFile(file_path, **kwargs)
        self._add_file_object(file_id, file_object)
        return file_object


class ListDirectory(Directory):
    def __init__(self, *directories):
        """
        Class holds list files from the default list files directory. Also option to add additional directories in args.
        List files has prefix "list_"

        :param directories: optional additional directories
        """
        super().__init__(DIRECTORIES.get('list_files'), *directories, prefix='list_')

    def get_file_object(self, file_id, **kwargs):
        file_path = self.get_path(file_id)
        file_object = files.ListFile(file_path, **kwargs)
        self._add_file_object(file_id, file_object)
        return file_object


class MultiListDirectory(Directory):
    def __init__(self, *directories):
        """
        Class holds list files from the default list files directory. Also option to add additional directories in args.
        List files has prefix "multilist_"

        :param directories: optional additional directories
        """
        super().__init__(DIRECTORIES.get('multilist_files'), *directories, prefix='multilist_')

    def get_file_object(self, file_id, **kwargs):
        file_path = self.get_path(file_id)
        file_object = files.MultiListFile(file_path, **kwargs)
        self._add_file_object(file_id, file_object)
        return file_object


class SamplingTypeSettingsDirectory(Directory):

    def __init__(self, *directories):
        super().__init__(DIRECTORIES.get('sampling_type_settings_files'), file_type='json', *directories)
        self.objects = {}

    def get_file_object(self, file_id, directory=None, use_class=None):
        file_path = self.get_path(file_id)
        file_object = use_class(file_path, directory=directory)
        self._add_file_object(file_id, file_object)
        return file_object
