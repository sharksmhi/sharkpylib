#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import os
import shutil

import numpy as np
import logging
import datetime
import pandas as pd

from .gismo import GISMOqc
from .exceptions import *

from .qc import IOCFTP_QC

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
        self.classes = {'iocftp_qc0': QCiocftp,
                        'ferrybox_test': TestQCFerrybox}

        self.required_arguments = {'iocftp_qc0': [],
                                   'ferrybox_test': ['local_config_directory',
                                                     'source_config_directory']}

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
        return self.required_arguments.get(routine)


class TestQCFerrybox(GISMOqc):
    """
    Created 20181005     

    Class to perform QC on gismo ferrybox data
    """
    def __init__(self,
                 local_config_directory=None,
                 source_config_directory=None,):
        pass

    def update_config_files(self):
        """ Call to update config files needed to run qc """
        pass

    def run_qc(self, gismo_object):
        """ Call to run qc on GISMO-object """
        pass


class QCiocftp(GISMOqc):
    """
    Created 20180928     
    Updated 20181001

    Class handles quality control based on QC from IOCFTP.
    """

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        gismo_root_path = os.path.dirname(os.path.abspath(__file__))
        # Paths must end with /
        self.cfg_directory = os.path.join(gismo_root_path, 'qc/iocftp/cfg/')
        self.qc_directory = os.path.join(gismo_root_path, 'qc/iocftp/qc/')
        self.log_directory = kwargs.get('log_directory', os.path.join(gismo_root_path, 'qc/iocftp/log/'))
        if not os.path.exists(self.log_directory):
            os.mkdir(self.log_directory)

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

        self._set_config_paths()

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



