import numpy as np
import pandas as pd
import logging
import glob
import os
import sys
import importlib
import datetime

lib_path = r'd:\git\sharkpylib'
print('lib_path is:', lib_path)

if lib_path not in sys.path:
    sys.path.append(lib_path)

#import gismo_object
import gismo
from gismo import GISMOsession
from gismo import sampling_types
from gismo import qc_routines

import gismo.libs.IOCFTP_QC as iocftpqc

class IocftpQC(object):

    def __init__(self):
        print('__init__')
        config_path = r'D:\git\sharkpylib\gismo\qc\iocftp\cfg\\'
        qc_path = r'D:\git\sharkpylib\gismo\qc\iocftp\qc\\'
        iocftpqc.set_config_path(config_path)
        iocftpqc.set_qc_path(qc_path)

    def run_qc(self, df, station_name='', station_nr=''):

        # converting data frame to np-array ==========================

        columns = []
        add_columns = []  # last columns in df, not used in qc, separate them in this loop
        for item in df.columns:
            if not item:
                continue
            if item in gismo_object.original_columns:
                columns.append(item)
            else:
                add_columns.append(item)

        columns = np.asarray(columns)  # header: converting list to nd array

        df_to_np = df[columns] # choose original cols (no '' or non-string)
        data_matrix_in = df_to_np.astype('float')  # converting to df with float
        data_matrix_in = data_matrix_in.values  # headers lost in conversion to array
        columns = np.asfarray(columns, float)  # converting columns to float
        columns = np.array([int(item) for item in columns])  # and then to integer

        # running qc script ===========================================================

        # station_name = 'TransPaper'
        # station_nr = '38003'
        # header_in = np.arange(47) # dftonp has 47 cols
        #header_in = columns.copy()

        data_matrix_out = iocftpqc.QC_CHECK_FERRYBOX(station_name,
                                                     station_nr,
                                                     data_matrix_in,
                                                     columns,
                                                     "QC_check_file.py",
                                                     '')

        # converting qc-out nparray to dataframe =======================================

        df_out = pd.DataFrame(data_matrix_out, columns=columns)

        for x in add_columns:  # adding back last columns from original dataframe
            df_out[x] = df[x]

        # change float back to str , not ready !!!!!!!!!!!!!!!!!!!!!!

        # float in df out, change to str
        df_out['88170'].astype(int).astype(str).values

        # change only cols with new qc-flags
        df_final = df.copy()
        df_final['88170'] = df_out['88170'].astype(int).astype(str)

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        return df_out



loadpath = r'D:\git\test'
savepath=r'D:\git\test'
loggpath=r'D:\git\test'
log = logging.getLogger("QC_check_file.py")
log.setLevel(logging.DEBUG)
handler = logging.FileHandler(os.path.join(loggpath, 'LOG_QC_check_file_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.log'))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
log.debug('Test debug')

root_directory = 'D:/utv_work_dir/gismo_session'
ferrybox_file = r'D:\git\sharkpylib\gismo\example_files/small_TransPaper_38003_20160222170325_20160502020012_OK.txt'
sharkweb_file = r'D:\git\sharkpylib\gismo\example_files/sharkweb_data_2016_feb-may.txt'
ferrybox_settings = r'D:\utv_work_dir\gismo_session\settings/cmems_ferrybox.ini'
sharkweb_settings = r'D:\utv_work_dir\gismo_session\settings/sharkweb_english.ini'

sampling_types_factory = sampling_types.PluginFactory()
qc_routines_factory = qc_routines.PluginFactory()

kw = dict(root_directory=root_directory,
          users_directory=os.path.join(root_directory, 'users'),
          log_directory=os.path.join(root_directory, 'log'),
          user='default',
          sampling_types_factory=sampling_types_factory,
          qc_routines_factory=qc_routines_factory,
          save_pkl=False)

session = GISMOsession(**kw)
session.get_sampling_types()

ferrybox_file_id = session.load_file(root_directory=root_directory,
                                     sampling_type='Ferrybox CMEMS',
                                     file_path=ferrybox_file,
                                     settings_file_path=ferrybox_settings)

gismo_object = session.get_gismo_object(ferrybox_file_id)
df = gismo_object.df.copy(deep=True)

# ===========================================================================

iocftp_qc = IocftpQC()

df_out = iocftp_qc.run_qc(df, station_name='TransPaper', station_nr='38003')