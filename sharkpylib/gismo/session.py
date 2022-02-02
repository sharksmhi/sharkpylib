# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on Tue Mar 07 11:48:49 2017

@author:
"""

from .exceptions import *

from .gismo import GISMOdataManager
from .gismo import GISMOqcManager
from sharkpylib.file.file_handlers import SamplingTypeSettingsDirectory, MappingDirectory


import os 
import json 
import pickle
import shutil

# Setup logger
import logging
gismo_logger = logging.getLogger('gismo_session')
gismo_logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t%(module)s (row=%(lineno)d)\t%(message)s')

logger_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
if not os.path.exists(logger_directory):
    os.mkdir(logger_directory)
logger_file_path = os.path.join(logger_directory, 'gismo_session.log')
file_handler = logging.FileHandler(logger_file_path)
file_handler.setFormatter(formatter)

gismo_logger.addHandler(file_handler)

#==============================================================================
#==============================================================================
class FileInfo(dict):
    """
    Created 20180628       
    Updated 20180713       
    
    Holds file information. Source file and pkl file.
    """
    def __init__(self, 
                 file_path='', 
                 pkl_directory=''): 
        
        self.file_path = file_path 
        self.pkl_directory = pkl_directory
        
        file_name = os.path.basename(file_path) 
        name, ending = os.path.splitext(file_name)
        directory = os.path.dirname(file_path)
        pkl_file_path = os.path.join(pkl_directory, '{}.pkl'.format(name))
        
        self['file_id'] = name
        self['directory'] = directory 
        self['file_path'] = file_path 
        self['pkl_file_path'] = pkl_file_path

    def get_file_path(self):
        return self['file_path']
        
    

#==============================================================================
#==============================================================================
class UserInfo():
    """
    Created 20180627       
    """
    #==========================================================================
    def __init__(self, 
                 user='', 
                 user_directory=''): 
        """
        Created 20180627        
        Updated 20180627       
        
        Loads the json info file. 
        If non existing the file is created. 
        If existing the fields are updated with "update_data".
        The fields must be initiated here. No "creations" of keys are made in 
        this or other scripts. 
        
        The json info file will hold the following information: 
            user name
            loaded files and there origin 
            
        """
        assert all([user, user_directory])
        
        self.user = user 
        self.user_directory = user_directory
        self.pkl_directory = os.path.join(self.user_directory, 'pkl_files')

        update_data = {'user': self.user, 
                       'loaded_files': {}}
        
        self.file_id_sampling_type_mapping = {}

        if not os.path.exists(self.user_directory):
            os.makedirs(self.user_directory)
            
        if not os.path.exists(self.pkl_directory):
            os.makedirs(self.pkl_directory)
            
        self.info_file_path = os.path.join(self.user_directory, 'user_info.json') 
        
        self.content = {}
        # Load info file if existing
        if os.path.exists(self.info_file_path): 
            with open(self.info_file_path, "r") as fid:
                self.content = json.load(fid)
        
        # Update content with possibly new fields
        self.content.update(update_data)
        
        # Save info file
        self._save_file()
        
    
    #==========================================================================
    def _save_file(self):
        """
        Created 20180627        
        
        Save self to json file
        """  
        with open(self.info_file_path, "w") as fid: 
            json.dump(self.content, fid)
    
    
    #==========================================================================
    def add_file(self, 
                 sampling_type='', 
                 file_path='', 
                 settings_file_path=''): 
        """
        Created 20180627       
        Updated 20180713       
        
        Information to be added when adding a file. 
        returns a "file name dict" containing information about data file and settings file: 
            directory 
            file_path 
            pkl_file_path
        """
        assert all([sampling_type, file_path]) 
        
        
#        file_name = os.path.basename(file_path) 
#        name, ending = os.path.splitext(file_name)
#        directory = os.path.dirname(file_path)
#        pkl_file_path = os.path.join(self.pkl_directory, '{}.pkl'.format(name))
#        
#        info_dict = {file_name: {'directory': directory, 
#                                 'file_path': file_path}, 
#                                 'pkl_file_path': pkl_file_path} 
                
        self.content.setdefault('loaded_files', {}).setdefault(sampling_type, {})
        
        info_data = FileInfo(file_path=file_path, 
                             pkl_directory=self.pkl_directory)
        
        info_settings = FileInfo(file_path=settings_file_path, 
                                 pkl_directory=self.pkl_directory)
        
        file_id = info_data.get('file_id')
        self.content['loaded_files'][sampling_type][file_id] = {}
        self.content['loaded_files'][sampling_type][file_id]['file_id'] = file_id
        self.content['loaded_files'][sampling_type][file_id]['data_file'] = info_data
        
#        print('settings_file_path', settings_file_path)
        self.content['loaded_files'][sampling_type][file_id]['settings_file'] = info_settings
        
        self.file_id_sampling_type_mapping[file_id] = sampling_type
        
        self._save_file()
        
        return self.content['loaded_files'][sampling_type][file_id]

    
    #==========================================================================
    def delete_file(self, 
                    sampling_type='', 
                    file_id=''): 
        """
        Created 20180628        
        Updated 20180713       
        
        Deletes information about a file. 
        
        """
        files_dict = self.content['loaded_files'].get(sampling_type, {}) 
        if file_id in files_dict: 
            files_dict.pop(file_id)
            self.file_id_sampling_type_mapping.pop(file_id)
        return True 
        
    
    #==========================================================================
    def get_sampling_type_for_file_id(self, file_id):
        """
        Created 20180713        
        """
        return self.file_id_sampling_type_mapping.get(file_id, None)
    
    
    #==========================================================================
    def get_file_id_list(self, sampling_type):
        """
        Created 20180713       
        Updated 
        
        Returns a list of the loaded files (file_id) for the given sampling type. 
        """ 
        return sorted(self.content['loaded_files'].get(sampling_type, {}).keys())

    def get_file_path(self, file_id):
        sampling_type = self.get_sampling_type_for_file_id(file_id)
        return self.content['loaded_files'][sampling_type][file_id]['data_file'].get_file_path()


        
    
#==============================================================================
#==============================================================================        
class GISMOsession(object):
    """
    Created 20180625       
    """
    #==========================================================================
    def __init__(self,
                 root_directory='',
                 users_directory='',
                 log_directory='',
                 user='default',
                 sampling_types_factory=None,
                 qc_routines_factory=None,
                 **kwargs):

        """
        Created 20180625       
        Updated 20181003       

        root_directory is optional but needs to be provided if "root" is in the settings files.

        kwargs can include:
            save_pkl
        """
        gismo_logger.info('Start session')
        #if not all([users_directory, user, sampling_types_factory]):
        #    raise GISMOExceptionMissingInputArgument

        self.root_directory = root_directory
        self.users_directory = users_directory
        self.log_directory = log_directory
        self.save_pkl = kwargs.get('save_pkl', False)

        self.sampling_types_factory = sampling_types_factory
        self.qc_routines_factory = qc_routines_factory

        self.user = user
        self.user_directory = os.path.join(self.users_directory, self.user)

        self.data_manager = GISMOdataManager(factory=self.sampling_types_factory)
        self.qc_manager = GISMOqcManager(factory=self.qc_routines_factory)

        self.compare_objects = {}

        self._load_attributes()

        self._startup_session()

    def _load_attributes(self):
        # Settings files
        self.settings_files = SamplingTypeSettingsDirectory()

        # if not os.path.exists(self.settings_files_directory):
        #     os.makedirs(self.settings_files_directory)
        # self.settings_files = {}
        # for file_name in os.listdir(self.settings_files_directory):
        #     if not file_name.endswith('.json'):
        #         continue
        #     self.settings_files[file_name] = os.path.join(self.settings_files_directory, file_name)

        # Mapping files
        self.mapping_files = MappingDirectory()
        # if not os.path.exists(self.mapping_files_directory):
        #     os.makedirs(self.mapping_files_directory)
        # self.mapping_files = {}
        # for file_name in os.listdir(self.mapping_files_directory):
        #     if not file_name.endswith('txt'):
        #         continue
        #     self.mapping_files[file_name] = os.path.join(self.mapping_files_directory, file_name)
    
    # ==========================================================================
    def _startup_session(self):
        """
        Created 20180625       
        Updated 20180713       
        """

        # Create and load json info file
        self.user_info = UserInfo(self.user,
                                  self.user_directory)


        # # Initate Boxen that will hold all data
        # self.boxen = gtb_core.Boxen(controller=self,
        #                             root_directory=self.root_directory)

    def add_settings_directory(self, directory):
        self.settings_files.add_directory(directory)

    def add_mapping_directory(self, directory):
        self.mapping_files.add_directory(directory)

    def add_compare_object(self, main_file_id, compare_file_id, **kwargs):
        pass

    def get_valid_flags(self, file_id):
        """
        Returns the valid flags of the gismo object with the given file_id.
        :param file_id:
        :return:
        """
        return self.data_manager.get_valid_flags(file_id)

    def flag_data(self, file_id, flag, *args, **kwargs):
        """
        Method to manually flag data in given file.

        :param file_id:
        :param flag:
        :param args:
        :param kwargs:
        :return: None
        """
        self.data_manager.flag_data(file_id, flag, *args, **kwargs)

    # ==========================================================================
    def get_sampling_types(self):
        return self.sampling_types_factory.get_list()

    def get_station_list(self):
        return self.data_manager.get_station_list()

    def get_settings_files(self):
        return self.settings_files.get_list()

    # ==========================================================================
    def get_qc_routines(self):
        return self.qc_routines_factory.get_list()

    def get_valid_qc_routines(self, file_id):
        return self.data_manager.get_valid_qc_routines(file_id)

    # ==========================================================================
    def get_sampling_type_requirements(self, sampling_type):
        return self.sampling_types_factory.get_requirements(sampling_type)

    # ==========================================================================
    def get_qc_routine_requirements(self, routine):
        return self.qc_routines_factory.get_requirements(routine)

        # ==========================================================================
    def get_qc_routine_options(self, routine):
        return self.qc_manager.get_qc_options(routine)

    def get_file_path(self, file_id):
        """
        Returns the file path for the given file_id
        """
        gismo_object = self.get_gismo_object(file_id)
        return os.path.abspath(gismo_object.file_path)

    def get_filter_options(self, file_id, **kwargs):
        """
        Created 20181004       

        :param file_id:
        :param kwargs:
        :return: list of filter options
        """
        return self.data_manager.get_filter_options(file_id, **kwargs)

    def get_flag_options(self, file_id, **kwargs):
        """
        Created 20181005       

        :param file_id:
        :param kwargs:
        :return: list of flag options
        """
        return self.data_manager.get_flag_options(file_id, **kwargs)

    def get_flag_options_mandatory(self, file_id, **kwargs):
        """
        Created 20191130

        :param file_id:
        :param kwargs:
        :return: list of mandatory flag options
        """
        return self.data_manager.get_flag_options_mandatory(file_id, **kwargs)

    def get_filtered_file_id_list(self, **kwargs):
        """
        Returns a list of the loaded file_id:s that matches the given criteria.

        :param kwargs:
        :return: list of file_id matching given filter
        """
        return self.data_manager.get_filtered_file_id_list(**kwargs)

    def get_mask_options(self, file_id, **kwargs):
        """
        Created 20181005

        :param file_id:
        :param kwargs:
        :return: list of mask options
        """
        return self.data_manager.get_mask_options(file_id, **kwargs)

    def get_save_data_options(self, file_id, **kwargs):
        """
        Created 20181106

        :param file_id:
        :param kwargs:
        :return: list of mask options
        """
        return self.data_manager.get_save_data_options(file_id, **kwargs)

    def get_data(self, file_id, *args, **kwargs):
        """
        Created 20181004       

        :param file_id:
        :param args:
        :param kwargs:
        :return: data as list/array (if one args) or list of lists/arrays (if several args)
        """
        return self.data_manager.get_data(file_id, *args, **kwargs)

    def get_match_data(self, main_file_id, match_file_id, *args, **kwargs):
        return self.data_manager.get_match_data(main_file_id, match_file_id, *args, **kwargs)

    def get_merge_data(self, main_file_id, match_file_id, *args, **kwargs):
        return self.data_manager.get_merge_data(main_file_id, match_file_id, *args, **kwargs)

    def get_match_object(self, main_file_id, match_file_id, *args, **kwargs):
        return self.data_manager.get_match_object(main_file_id, match_file_id, *args, **kwargs)

    def match_files(self, main_file_id, match_file_id, **kwargs):
        self.data_manager.match_files(main_file_id, match_file_id, **kwargs)

    def get_metadata_tree(self, file_id):
        gismo_object = self.get_gismo_object(file_id)
        return gismo_object.get_metadata_tree()

    # ==========================================================================
    def load_file(self,
                  sampling_type='',
                  data_file_path='',
                  settings_file='',
                  **kwargs):
        """
        :param sampling_type:
        :param data_file_path:
        :param settings_file: must be found in self.settings_files_path
        :param kwargs:
        :return:
        """
        """
        Created 20180628       
        Updated 20181004       
        
        If reload==True the original file is reloaded regardless if a pkl file exists.
        sampling_type refers to SMTYP in SMHI codelist
        
        kwargs can be:
            file_encoding
        """
        print('kwargs 2', kwargs)
        if sampling_type not in self.data_manager.sampling_type_list:
            raise GISMOExceptionInvalidSamplingType(sampling_type)
        # print('=', self.settings_files)
        # print('-', settings_file)
        # if not settings_file.endswith('.json'):
        #     settings_file = settings_file + '.json'
        # settings_file_path = self.settings_files.get(settings_file, None)
        settings_file_path = self.settings_files.get_path(settings_file)

        if not settings_file_path:
            raise GISMOExceptionMissingSettingsFile

        kw = dict(data_file_path=data_file_path,
                  settings_file_path=settings_file_path,
                  # root_directory=self.root_directory,
                  # mapping_files_directory=self.mapping_files_directory,
                  )
        kw.update(kwargs)

        # Check sampling type requirements
        sampling_type_requirements = self.get_sampling_type_requirements(sampling_type)
        if not sampling_type_requirements:
            raise GISMOExceptionMissingRequirements
        for item in sampling_type_requirements:
            if not kw.get(item):
                raise GISMOExceptionMissingInputArgument(item)

        return self.data_manager.load_file(data_file_path=data_file_path,
                                           sampling_type=sampling_type,
                                           settings_file_path=settings_file_path,
                                           mapping_files=self.mapping_files)



    # if not all([sampling_type, file_path, settings_file_path]):
    #         raise GISMOExceptionMissingInputArgument
        
        # if not all([os.path.exists(file_path), os.path.exists(settings_file_path)]):
        #     raise GISMOExceptionInvalidPath


        # Add file path to user info 
        file_path = os.path.abspath(kw.get('data_file_path'))
        settings_file_path = os.path.abspath(kw.get('settings_file_path'))
        file_paths = self.user_info.add_file(sampling_type=sampling_type, 
                                             file_path=file_path,
                                             settings_file_path=settings_file_path)
        
        # Get file paths         
        data_file_path = file_paths.get('data_file', {}).get('file_path', '')
        data_file_path_pkl = file_paths.get('data_file', {}).get('pkl_file_path', '')
        data_file_path_settings = file_paths.get('settings_file', {}).get('file_path', '')

        # Get file_id
        file_id = file_paths.get('data_file', {}).get('file_id', '')
        if not file_id:
            raise GISMOExceptionMissingKey

        # print(data_file_path)
        # print(data_file_path_settings)

        # Check type of file and load
        if kwargs.get('reload') or not os.path.exists(data_file_path_pkl):
            # Load original file
            self.data_manager.load_file(data_file_path=data_file_path,
                                        sampling_type=sampling_type,
                                        settings_file_path=data_file_path_settings,
                                        # root_directory=self.root_directory, # Given in kwargs
                                        save_pkl=self.save_pkl,
                                        pkl_file_path=data_file_path_pkl,
                                        mapping_files=self.mapping_files,
                                        # mapping_files_directory=self.mapping_files_directory,
                                        **kwargs)

        else:
            # Check if sampling_type is correct
            # file_name = os.path.basename(file_path)
            # expected_sampling_type = self.user_info.get_sampling_type_for_file_id(file_id)
            # if expected_sampling_type != sampling_type:
            #     return False

            # Load buffer pickle file
            self.data_manager.load_file(sampling_type=sampling_type,
                                       load_pkl=self.save_pkl,
                                       pkl_file_path=data_file_path_pkl)

        return file_id

    def load_files(self,
                   sampling_type='',
                   data_file_paths=[],
                   settings_file='',
                   **kwargs):
        """
        Load several files using the same settings_file. Calls self.load_file with every path in data_file_paths

        :param sampling_type:
        :param data_file_paths:
        :param settings_file:
        :param kwargs:
        :return:
        """
        file_id_list = []
        for data_file_path in data_file_paths:
            file_id = self.load_file(sampling_type=sampling_type,
                                     data_file_path=data_file_path,
                                     settings_file=settings_file,
                                     **kwargs)
            file_id_list.append(file_id)
        return file_id_list

    def has_file_id(self):
        return self.data_manager.has_file_id()

    def has_metadata(self, file_id):
        return self.data_manager.has_metadata(file_id)

    def remove_file(self, file_id):
        """
        Removes the given file_id from the session.
        :param file_id:
        :return:
        """
        self.data_manager.remove_file(file_id)
    
    #==========================================================================
    def _load_pickle_file(self, data_file_path_pkl):
        """
        Created 20180828        

        Loads a pickle file that contains data and settings information. 
        Returns a gismo object.
        """
        with open(data_file_path_pkl, "rb") as fid: 
            gismo_object = pickle.load(fid)
    
        return gismo_object

    def save_file(self, file_id, **kwargs):
        """
        Created 20181106

        :param file_id:
        :param kwargs:
        :return: None
        """
        self.data_manager.save_file(file_id, **kwargs)

    # ==========================================================================
    def get_file_id_list(self, sampling_type=None):
        """
        Created 20180713
        Updated

        Returns a list of the loaded files (file_id) for the given sampling type.
        """
        return self.data_manager.get_file_id_list(sampling_type=sampling_type)

    # ==========================================================================
    def get_gismo_object(self, file_id=''):
        """
        Created 20180713       
        Updated 20181022
        
        Returns a the gismo object marked with the given file_id
        """
        if not file_id:
            raise GISMOExceptionMissingInputArgument('file_id')
        return self.data_manager.get_data_object(file_id)

        # ==========================================================================
    def get_parameter_list(self, file_id='', **kwargs):
        if not file_id:
            raise GISMOExceptionMissingInputArgument
        return self.data_manager.get_parameter_list(file_id, **kwargs)

    def get_position(self, file_id, **kwargs):
        """
        :param file_id:
        :param kwargs:
        :return: List with position(s). Two options:
        fixed position: [lat, lon]
        trajectory: [[lat, lat, lat, ...], [lon, lon, lon, ...]]
        """
        return self.data_manager.get_position(file_id, **kwargs)

    def get_unit(self, file_id='', unit='', **kwargs):
        if not file_id:
            raise GISMOExceptionMissingInputArgument
        return self.data_manager.get_unit(file_id, unit, **kwargs)

    # ==========================================================================
    def print_list_of_gismo_objects(self):
        """
        Created 20180926       
        Updated 20180927     

        Prints a list of all loaded gismo object. sorted by sampling_type.
        """
        for st in sorted(self.gismo_objects):
            print('Sampling type:', st)
            for file_id in sorted(self.gismo_objects[st]):
                print('   {}'.format(file_id))

    def run_automatic_qc(self, file_id=None, qc_routine=None, **kwargs):
        """
        Runs automatic qc controls on the given gismo object. All routines in qc_routines ar run.
        :param qismo_object:
        :param qc_routines:
        :param kwargs:
        :return: True if successful
        """
        if not file_id:
            raise GISMOExceptionMissingInputArgument
        if type(file_id) != list:
            file_id = [file_id]

        gismo_objects = [self.get_gismo_object(f) for f in file_id]

        # Check qc requirements
        qc_requirements = self.get_qc_routine_requirements(qc_routine)
        if qc_requirements is None:
            raise GISMOExceptionMissingRequirements
        for item in qc_requirements:
            if not kwargs.get(item):
                raise GISMOExceptionMissingInputArgument(item)
        return self.qc_manager.run_automatic_qc(gismo_objects=gismo_objects, qc_routine=qc_routine, **kwargs)


if __name__ == '__main__':
    from sharkpylib.gismo.session import GISMOsession
    from sharkpylib.gismo import sampling_types
    from sharkpylib.gismo import qc_routines
    from sharkpylib.odv.create import SimpleODVfile
    from sharkpylib.odv.spreadsheet import SpreadsheetFile

    d = r'C:\mw\temp_odv'
    sampling_types_factory = sampling_types.PluginFactory()
    qc_routines_factory = qc_routines.PluginFactory()
    session = GISMOsession(root_directory=d,
                            users_directory=d,
                            log_directory=d,
                            user='temp_user',
                            sampling_types_factory=sampling_types_factory,
                            qc_routines_factory=qc_routines_factory,
                            save_pkl=False)
    # file_path = r'C:\mw\temp_odv/TransPaper_38003_20120601001612_20120630235947_OK.txt'
    # session.load_file('Ferrybox CMEMS', file_path, 'cmems_ferrybox')
    #
    # g = session.data_manager.objects[session.get_file_id_list()[0]]
    #
    # s = SimpleODVfile.from_gismo_object(g)
    #
    # s.create_file(r'C:\mw\temp_odv/transpaper_odv.txt')
    #
    # file_path = r'C:\mw\temp_odv/data_from_asko_odv(5).txt'
    #
    # sp = SpreadsheetFile(file_path)
    # data = sp.get_edited_flags(qf_prefix='8')

