#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import datetime
import shutil
from pathlib import Path

from sharkpylib.odv.spreadsheet import SpreadsheetFile

try:
    import numpy as np
    import pandas as pd
except:
    pass

from sharkpylib.gismo.gismo import GISMOqc
from sharkpylib.gismo.exceptions import *

from sharkpylib.gismo.qc import IOCFTP_QC
from sharkpylib.gismo.qc.qc_trajectory import FlagAreas

from sharkpylib.gismo.qc.qc_profile import ProfileQCrangeSimple, ProfileQCreportTXT


# This is for Profile DV QC§
try:
    from ctdpy.core.session import Session
    from ctdpy.core.utils import generate_filepaths, get_reversed_dictionary
except:
    pass
from sharkpylib.qc.qc_default import QCBlueprint

import logging
gismo_logger = logging.getLogger('gismo_session')

"""
========================================================================
========================================================================
"""
class PluginFactory(object):
    """
    Created 20181003     

    Class hold information about active classes in module.
    Also contains method to return an object of a mapped class.

    New class in module is activated by adding class name to self.classes.

    Also make sure to add required input arguments (for __init__) to self.required_arguments.

    """
    def __init__(self):
        # Add key and class to dict if you want to activate it
        self.classes = {QCprofileRangeSimple.name: QCprofileRangeSimple,
                        QCprofileReport.name: QCprofileReport,
                        QCprofileDV.name: QCprofileDV,
                        QCfromODVSpreadsheet.name: QCfromODVSpreadsheet}
        # self.classes = {'Mask areas': QCmaskArea}

        self.required_arguments = {QCprofileRangeSimple.name: ['parameter_list'],
                                   QCprofileReport.name: ['subroutines', 'save_directory'],
                                   QCprofileDV.name: [],
                                   QCfromODVSpreadsheet.name:['odv_spreadsheet_file_path']}

        # self.required_arguments = {'Mask areas': ['file_path', 'par_to_flag']}


#        self.classes = {'iocftp_qc0': QCiocftp,
#                        'Mask areas': QCmaskArea}
#        self.required_arguments = {'iocftp_qc0': []}

    def __str__(self):
        return '\nQC factory. Available qc routines are:\n{}\n'.format('\n'.join(sorted(self.classes)))

    def get_list(self):
        return sorted(self.classes)

    def get_object(self, routine, *args, **kwargs):
        """

        :param routine:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.classes.get(routine):
            raise GISMOExceptionInvalidClass
        return self.classes.get(routine)(*args, **kwargs)

    def get_requirements(self, routine):
        """
        Created 20181005     

        Returns the required arguments needed for the initialisation of the object
        :param routine:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.classes.get(routine):
            raise GISMOExceptionInvalidClass
        return self.required_arguments.get(routine, None)


class QCmaskArea(GISMOqc):
    """

    Class to perform masking within areas
    """
    def __init__(self, file_path=None, par_to_flag='all'):

        super().__init__()
        self.name = 'Mask areas'
        self.file_path = file_path
        self.par_to_flag = par_to_flag
        if not self.file_path:
            gismo_root_path = os.path.dirname(os.path.abspath(__file__))
            self.file_path = os.path.join(gismo_root_path, 'qc/trajectory/flag_areas.txt')

        if not os.path.exists(self.file_path):
            raise GISMOExceptionInvalidPath

        self.flag_areas_object = FlagAreas(self.file_path)
        self.flag = '4'

    def get_information(self):
        info_dict = dict()
        info_dict['Name'] = self.name
        info_dict['file_path'] = self.file_path
        info_dict['par_to_flag'] = self.par_to_flag
        info_dict['areas'] = self.flag_areas_object.get_areas()
        return info_dict

    def run_qc(self, gismo_object, **kwargs):
        """
        Call to run qc on a gismo_object. If return_copy=True a copy of the dataframe is returnd and no data is changed
        in the gismo_object.

        :param gismo_object:
        :param return_copy:
        :return:
        """
        if self.flag not in gismo_object.valid_flags:
            raise GISMOExceptionInvalidFlag('Invalid flag {} in QC routine "{}" '
                                            'for file with id "{}"'.format(self.flag, self.name, gismo_object.file_id))

        # All parameters with flags should be flagged
        if self.par_to_flag == 'all':
            par_list = []
            for par in gismo_object.get_parameter_list():
                qpar = gismo_object.get_qf_par(par)
                if qpar:
                    par_list.append(par)

        self.flag_areas_object.run_qc(gismo_object, par_list=par_list, flag=self.flag)


class QCmaskArea(GISMOqc):
    """

    Class to perform masking within areas
    """
    def __init__(self, file_path=None, par_to_flag='all'):

        super().__init__()
        self.name = 'Mask areas'
        self.file_path = file_path
        self.par_to_flag = par_to_flag
        if not self.file_path:
            gismo_root_path = os.path.dirname(os.path.abspath(__file__))
            self.file_path = os.path.join(gismo_root_path, 'qc/trajectory/flag_areas.txt')

        if not os.path.exists(self.file_path):
            raise GISMOExceptionInvalidPath

        self.flag_areas_object = FlagAreas(self.file_path)
        self.flag = '4'

    def get_information(self):
        info_dict = dict()
        info_dict['Name'] = self.name
        info_dict['file_path'] = self.file_path
        info_dict['par_to_flag'] = self.par_to_flag
        info_dict['areas'] = self.flag_areas_object.get_areas()
        return info_dict

    def run_qc(self, gismo_object, **kwargs):
        """
        Call to run qc on a gismo_object. If return_copy=True a copy of the dataframe is returnd and no data is changed
        in the gismo_object.

        :param gismo_object:
        :param return_copy:
        :return:
        """
        if self.flag not in gismo_object.valid_flags:
            raise GISMOExceptionInvalidFlag('Invalid flag {} in QC routine "{}" '
                                            'for file with id "{}"'.format(self.flag, self.name, gismo_object.file_id))

        # All parameters with flags should be flagged
        if self.par_to_flag == 'all':
            par_list = []
            for par in gismo_object.get_parameter_list():
                qpar = gismo_object.get_qf_par(par)
                if qpar:
                    par_list.append(par)

        self.flag_areas_object.run_qc(gismo_object, par_list=par_list, flag=self.flag)

class QCiocftp(GISMOqc):
    """
    Created 20180928     
    Updated 20181001

    Class handles quality control based on QC from IOCFTP.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'iocftp_qc0'

        gismo_root_path = os.path.dirname(os.path.abspath(__file__))
        # Paths must end with /
        self.cfg_directory = os.path.join(gismo_root_path, 'qc/iocftp/cfg/')
        self.qc_directory = os.path.join(gismo_root_path, 'qc/iocftp/qc/')
        self.log_directory = kwargs.get('log_directory', os.path.join(gismo_root_path, 'qc/iocftp/log/'))
        if not os.path.exists(self.log_directory):
            os.mkdir(self.log_directory)

        self._set_config_paths()

    def _set_config_paths(self):
        # Set global path to config files
        IOCFTP_QC.set_config_path(self.cfg_directory)
        IOCFTP_QC.set_qc_path(self.qc_directory)

    # ==================================================================
    def run_qc(self, gismo_object):
        """
        Run QC. gismo_object must have attribute df for qc to work.
        """

        def _to_float(value):
            try:
                return float(value)
            except:
                # print('value is "{}" of type {}'.format(value, type(value)))
                return np.nan

        if not hasattr(gismo_object, 'df'):
            raise GISMOExceptionInvalidInputArgument


        # Setup log
        log = logging.getLogger("QC_check_file.py")
        log.setLevel(logging.DEBUG)
        log_path = os.path.join(self.log_directory, 'LOG_QC_check_file_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.log')

        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        log.debug('Test debug')

        # Create copy of df so we can compare later
        df = gismo_object.df.copy(deep=True)

        columns = []
        # add_columns = []  # last columns in df, not used in qc, separate them in this loop
        for item in df.columns:
            if not item:
                continue
            if item in gismo_object.original_columns:
                columns.append(item)
                # if item in [8181, '8181']:
                #     # print('TYPE', type(df[item].values[0]))
                #     df[item].astype(float)
                # try:
                #     # df[item].astype(float)
                #     columns.append(item)
                # except:
                #     print('ITEM', item)
            # else:
            #     add_columns.append(item)

        columns = np.asarray(columns)  # header: converting list to nd array
        # print()
        # print('='*50)
        # print('COLUMNS')
        # print('-' * 50)
        # for col in columns:
        #     print(col, type(col))
        # print('-' * 50)
        df_to_np = df[columns]  # choose original cols (no '' or non-string)
        # data_matrix_in = df_to_np.astype('float')  # converting to df with float
        # data_matrix_in = data_matrix_in.values  # headers lost in conversion to array
        for col in df_to_np.columns:
            df_to_np[col] = df_to_np[col].apply(_to_float)
        data_matrix_in = df_to_np.values  # headers lost in conversion to array

        columns = np.asfarray(columns, float)  # converting columns to float
        columns = np.array([int(item) for item in columns])  # and then to integer

        # running qc script ===========================================================

        station_name = str(gismo_object.internal_station_name)
        station_nr = str(gismo_object.external_station_name)

        try:
            data_matrix_out = IOCFTP_QC.QC_CHECK_FERRYBOX(station_name,
                                                          station_nr,
                                                          data_matrix_in,
                                                          columns,
                                                          "QC_check_file.py",
                                                          '')
        except NameError as e:
            raise

        # converting qc-out nparray to dataframe =======================================

        df_out = pd.DataFrame(data_matrix_out, columns=columns)

        # for x in add_columns:  # adding back last columns from original dataframe
        #     df_out[x] = df[x]

        # Create final df and replace qf columns
        df_final = df.copy(deep=True)
        for par in columns:
            qpar = gismo_object.get_qpar(par)
            if qpar:
                df_final[qpar] = df_out[qpar].astype(int).astype(str)

        # Print diff as a test
        for col in df.columns:
            array_before = df[col].values
            array_after = df_final[col].values
            diff = np.where(array_before != array_after)[0]
            if len(diff):
                print(col, diff)


class QCprofileDV(GISMOqc):
    """
    """
    name = 'Profile DV Standard format'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parent_dir = Path(__file__).parent
        self.add_info_to_metadata = False

        self.temp_dir = Path(parent_dir, '_temp_data')
        self.gismo_objects = None
        self.ctdpy_datasets = None
        self.ctdpy_session = None

    def run_qc(self, gismo_objects, **kwargs):
        """
        Data is generally in a pandas dataframe that can be reach under gismo_object.df.

        To manipulate (flag) data in a gismo_object use method gismo_object.flag_data()!!!
        Since the data structure is quit different this will not be the routine in this case.
        Instead the following steps will be made:
        1. A temporary file will be saved from the gismo object
        2. This file will be loaded using the cdtpy package
        3. QC will be performed
        4. Data will be copied from the ctdpy object to the gismo object.
           Only columns starting with "Q0_" will be copied.

        :param gismo_objects: gismo objects or objects as a list.
        :return:
        """
        self.gismo_objects = gismo_objects

        try:
            print(1)
            self._create_temp_directory()
            print(2)
            self._save_gismo_files()
            print(3)
            self._load_ctdpy_files()
            print(4)
            self._run_dv_qc_and_merge()
            print(5)
        except:
            pass
        finally:
            self._delete_temp_directory()
            print(6)

    def _create_temp_directory(self):
        if not self.temp_dir.exists():
            os.makedirs(self.temp_dir)

    def _delete_temp_directory(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _save_gismo_files(self):
        for gismo_object in self.gismo_objects:
            gismo_object.save_file(file_path=Path(self.temp_dir, gismo_object.file_id + '.txt'))

    def _load_ctdpy_files(self):
        files = generate_filepaths(self.temp_dir,
                                   endswith='.txt',  # Presumably CTD-standard format
                                   only_from_dir=False)

        self.ctdpy_session = Session(filepaths=files,
                                     reader='ctd_stdfmt')
        self.ctdpy_datasets = self.ctdpy_session.read()

    def _run_dv_qc_and_merge(self):
        for gismo_object in self.gismo_objects:
            key = gismo_object.file_id + '.txt'
            item = self.ctdpy_datasets[0].get(key)
            parameter_mapping = get_reversed_dictionary(self.ctdpy_session.settings.pmap, item['data'].keys())
            qc_run = QCBlueprint(item, parameter_mapping=parameter_mapping)
            qc_run()

            # Merge
            source_df = item['data']
            target_df = gismo_object.df
            for col in source_df:
                if not col.startswith('Q0_'):
                    continue
                print(col)
                target_df[col] = source_df[col]

            # Add metadata
            metadata_index = qc_run.meta.index[-1]
            metadata_string = qc_run.meta[metadata_index]
            gismo_object.add_qc_comment(metadata_string, as_is=True)

    def get_information(self):
        """
        Should return a dict with information about the QC routine.
        :return:
        """
        return {'General': 'QC routine developed and used by Datavärdskapet at SMHI'}

    def get_options(self):
        """
        Should return a dict with options available for the qc routine.
        Key is the option itself.
        Values are the available choices for the corresponding option. Choices can be of the following types:

        list: multi select
        empty list: free nr of inputs (ex. list of quality flags)
        tuple: single select
        string: free text
        float: free float number
        int: free int number

        :return:
        """
        return {}


class QCprofileRangeSimple(GISMOqc):
    name = 'Profile range simple'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qc_object = ProfileQCrangeSimple()

    def get_options(self):
        return self.qc_object.options

    def run_qc(self, gismo_objects, **kwargs):
        gismo_logger.info('Running QCprofileRangeSimple')
        return self.qc_object.run_qc(gismo_objects, **kwargs)


class QCprofileReport(GISMOqc):
    name = 'Profile report'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qc_object = ProfileQCreportTXT()

    def get_options(self):
        return self.qc_object.options

    def run_qc(self, gismo_objects, **kwargs):
        gismo_logger.info('Running QCprofileReport')
        return self.qc_object.run_qc(gismo_objects, **kwargs)


class QCfromODVSpreadsheet(GISMOqc):
    name = 'QC from ODV Spreadsheet'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.options = {'odv_spreadsheet_file_path': 'file path'}

    def get_options(self):
        return self.options

    def run_qc(self, gismo_objects, **kwargs):
        qf_prefix = list(set([g.qf_prefix for g in gismo_objects]))
        qf_suffix = list(set([g.qf_suffix for g in gismo_objects]))
        if len(qf_prefix) > 1:
            raise GISMOException('Files have different QF prefix')
        if len(qf_suffix) > 1:
            raise GISMOException('Files have different QF suffix')
        qf_prefix = qf_prefix[0]
        qf_suffix = qf_suffix[0]

        spreadsheet_file_path = kwargs.get('odv_spreadsheet_file_path')
        s_object = SpreadsheetFile(spreadsheet_file_path)
        data = s_object.get_edited_flags(qf_prefix=qf_prefix, qf_suffix=qf_suffix)

        for gismo_object in gismo_objects:
            for par in data.keys():
                for qf, keys in data[par].items():
                    print(qf, par, keys[0][0])
                    time_list = [item[0] for item in keys]
                    gismo_object.flag_data(qf, par, time=time_list)


if __name__ == '__main__':
    QCprofileDV()


