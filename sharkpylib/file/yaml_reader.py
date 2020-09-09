# -*- coding: utf-8 -*-
"""
Created on Thu Jul 05 10:29:30 2018

@author: a002028
"""
import os
from sharkpylib import utils
import numpy as np
import yaml


class YAMLreader(object):
    """
    """
    def __init__(self):
        super().__init__()

        self.config = {}

    def load_yaml(self, config_files, file_names_as_key=False, return_config=False, encoding='utf8'):
        """
        :param config_files:
        :param file_names_as_key:
        :param return_config:
        :param encoding:
        :return:
        """
        for config_file in config_files:
            with open(config_file, encoding=encoding) as fd:
                file = yaml.load(fd)
                # try:
                #     file = yaml.load(fd)
                # except yaml.YAMLError:
                #     file = yaml.safe_load(fd)
                if file_names_as_key:
                    file_name = self.get_file_name(config_file)
                    self.config[file_name] = file
                else:
                    self.config = utils.recursive_dict_update(self.config, file)

        if return_config:
            return self.config

    @staticmethod
    def get_file_name(file_path):
        """
        :param file_path: str, complete path to file
        :return: filename without extension
        """
        filename = os.path.basename(file_path)
        return os.path.splitext(filename)[0]
