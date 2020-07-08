# -*- coding: utf-8 -*-
"""
Created on 2020-02-26 10:20

@author: a002028

"""
import os
from sharkpylib.file.yaml_reader import YAMLreader
from sharkpylib.utils import git_version


class Settings(object):
    """
    """
    qc_routines = {}

    def __init__(self):
        self.base_directory = os.path.dirname(os.path.realpath(__file__))
        self._load_settings(os.path.abspath(os.path.join(self.base_directory, 'etc')))
        self.user = os.path.expanduser('~').split('\\')[-1]
        self.repo_version = git_version()
        print('QC - USER: {}'.format(self.user))

    @classmethod
    def update_routines(cls, value):
        """
        :param value:
        :return:
        """
        for key, func in value['functions'].items():
            cls.qc_routines.setdefault(func.get('name'),
                                       func.get('qc_index'))

    def __setattr__(self, name, value):
        """
        Defines the setattr for object self
        :param name: str
        :param value: any kind
        :return:
        """
        #TODO copied from ctdpy.. needs an update / corr
        if name == 'dir_path':
            pass
        elif isinstance(value, str) and 'path' in name:
            name = ''.join([self.base_directory, value])
        elif isinstance(value, dict) and 'paths' in name:
            self._check_for_paths(value)
        super().__setattr__(name, value)

    def _check_local_paths(self):
        """
        Checks paths in settings_paths..
        :return:
        """
        for path in self.settings_paths:
            if not os.path.exists(self.settings_paths.get(path)) and '.' not in self.settings_paths.get(path):
                os.makedirs(self.settings_paths.get(path))

    def _check_for_paths(self, dictionary):
        """
        Since default path settings are set to ctdpy base folder
        we need to add that base folder to all paths
        :param dictionary: Dictionary with paths as values and keys as items..
        :return: Updates dictionary with local path (self.dir_path)
        """
        for item, value in dictionary.items():
            if isinstance(value, dict):
                self._check_for_paths(value)
            elif 'path' in item:
                dictionary[item] = ''.join([self.base_directory, value])

    def _load_settings(self, etc_path):
        """
        :param etc_path: str, local path to settings
        :return: Updates attributes of self
        """
        paths = self.generate_filepaths(etc_path, pattern='.yaml')
        settings = YAMLreader().load_yaml(paths, file_names_as_key=True, return_config=True)
        self.set_attributes(self, **settings)

    def set_attributes(self, obj, **kwargs):
        """
        #TODO Move to utils?
        With the possibility to add attributes to an object which is not 'self'
        :param obj: object
        :param kwargs: Dictionary
        :return: sets attributes to object
        """
        for key, value in kwargs.items():
            if 'functions' in value and 'datasets' in value:
                self.update_routines(value)
            setattr(obj, key, value)

    @staticmethod
    def generate_filepaths(directory, pattern=''):
        """
        #TODO Move to utils?
        :param directory: str, directory path
        :param pattern: str
        :return: generator
        """
        for path, subdir, fids in os.walk(directory):
            for f in fids:
                if pattern in f:
                    yield os.path.abspath(os.path.join(path, f))

    @staticmethod
    def get_subdirectories(directory):
        """
        :param directory: str, directory path
        :return: list of existing directories (not files)
        """
        return [subdir for subdir in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, subdir))]

    @staticmethod
    def get_filepaths_from_directory(directory):
        """
        :param directory: str, directory path
        :return: list of files in directory (not sub directories)
        """
        return [''.join([directory, fid]) for fid in os.listdir(directory)
                if not os.path.isdir(directory+fid)]

    @property
    def number_of_routines(self):
        return len(self.qc_routines)
