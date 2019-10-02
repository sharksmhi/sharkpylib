# -*- coding: utf-8 -*-
# Copyright (c) 2019 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import pandas as pd
import os
import numpy as np

import mappinglib
import exceptionlib


class CreateIOCFTPfile(object):

    def __init__(self, data_file_path='', mapping_file_path='', mapping_file_name='', from_col='', to_col='', **kwargs):
        """
        Class to create (and save) a dataframe that fits the iocftp format for QC0.
        to_col is also the list of columns that will be included in the final dataframe.
        :param df:
        """
        assert data_file_path
        assert (mapping_file_path or mapping_file_name)
        assert from_col
        assert to_col

        self.data_file_path = data_file_path
        self.mapping_file_path = mapping_file_path
        self.mapping_file_name = mapping_file_name
        self.from_col = from_col
        self.to_col = to_col

        self.df = pd.DataFrame()
        self.mapping_object = None

        save_file = kwargs.pop('save_file', None)
        save_directory = kwargs.pop('save_directory', None)
        self._load_data_file()
        self._load_mapping_object(**kwargs)
        self._map_dataframe()
        self._filter_dataframe()
        self._add_qc0_columns()

        if save_file:
            self.save_iocftp_file(directory=save_directory)

    def _load_data_file(self):
        self.df = pd.read_csv(self.data_file_path, sep='\t', dtype=str)

    def _load_mapping_object(self, **kwargs):
        if self.mapping_file_name:
            mapping_directory = mappinglib.MappingDirectory()
            self.mapping_file_path = mapping_directory.get_file_path(self.mapping_file_name)

        self.mapping_object = mappinglib.MapAndFilterPandasDataframe(self.df)
        self.mapping_object.set_mapping_file(self.mapping_file_path, from_col=self.from_col, to_col=self.to_col, **kwargs)
        self.mapping_object.set_filter_list_from_column_file(self.mapping_file_path, self.to_col, **kwargs)

    def _map_dataframe(self):
        self.mapping_object.map()

    def _filter_dataframe(self):
        self.mapping_object.filter()

    def _add_qc0_columns(self):
        """
        Adds qc columns for all columns in filtered dataframe that has four digits. QC columns has an 8 an prefix.
        :return:
        """
        df = self.mapping_object.df_filtered.copy().fillna('')
        added_columns = []
        parent_added_column = []
        new_columns_in_order = []
        for col in df.columns:
            col = str(col)
            new_columns_in_order.append(col)
            if len(col) == 4:
                qc_col = '8'+col
                new_columns_in_order.append(qc_col)
                added_columns.append(qc_col)
                parent_added_column.append(col)

        # Add qc columns to df
        qc0_flag_series = np.zeros(len(df)).astype(int).astype(str)
        for col, parent_col in zip(added_columns, parent_added_column):
            boolean = df[parent_col] == ''
            add_series = qc0_flag_series.copy()
            add_series[boolean] = ''  # Check if this should be included
            df[col] = add_series

        # Reorder columns in df
        df = df[new_columns_in_order]

        # Save df
        self.df_iocftp = df.fillna('')

    def save_iocftp_file(self, directory=None):
        """
        If directory is not given the file is saved in tha same directory as the data file.
        File name is set according to data_file_name.
        :param directory:
        :return:
        """
        if directory is None:
            directory = os.path.dirname(self.data_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        data_file_name = os.path.basename(self.data_file_path)
        file_base = data_file_name.strip('merge_')
        split_file_base = file_base.split('_')

        mapping_directory_object = mappinglib.MappingDirectory()
        mapping_object = mapping_directory_object.get_mapping_object('mapping_iocftp_platforms')
        iocftp_name = mapping_object.get(split_file_base[0], from_col='standard_file_prefix', to_col='iocftp_name')
        iocftp_number = mapping_object.get(split_file_base[0], from_col='standard_file_prefix', to_col='iocftp_number')

        file_name = '_'.join([iocftp_name, iocftp_number] + split_file_base[1:])

        file_path = os.path.join(directory, file_name)

        # Save file
        self.df_iocftp.to_csv(file_path, sep='\t', index=False)

def add_QC0_columns_to_df(df, **kwargs):
    """
    Adds QCO_columns to the given dataframe. parameters that already has QC0 column will not added again.
    :param df:
    :param kwargs:
    :return:
    """
    pass
    # QC0_columns = []
    # added_columns = []
    # parent_added_column = []
    # new_columns_in_order = []
    # for col in df.columns:
    #     col = str(col)
    #     new_columns_in_order.append(col)
    #     if len(col) == 4:
    #         qc_col = '8' + col
    #         new_columns_in_order.append(qc_col)
    #         added_columns.append(qc_col)
    #         parent_added_column.append(col)
    #
    # # Add qc columns to df
    # qc0_flag_series = np.zeros(len(df)).astype(int).astype(str)
    # for col, parent_col in zip(added_columns, parent_added_column):
    #     boolean = df[parent_col] == ''
    #     add_series = qc0_flag_series.copy()
    #     add_series[boolean] = ''  # Check if this should be included
    #     df[col] = add_series
    #
    # # Reorder columns in df
    # df = df[new_columns_in_order]




