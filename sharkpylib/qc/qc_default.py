# -*- coding: utf-8 -*-
"""
Created on 2020-02-26 15:23

@author: a002028

"""
import pandas as pd
from sharkpylib.qc.settings import Settings
from sharkpylib.utils import get_time_as_format


class Qflag:
    """
    """
    def __init__(self, df_or_serie, **kwargs):
        super().__init__()
        try:
            assert type(df_or_serie) == pd.DataFrame or pd.Series
            assert type(kwargs.get('parameter')) == str or type(None)
            assert type(kwargs.get('boolean')) == list or pd.Series
        except AssertionError:
            #TODO Fix Logging..
            assertionerror_tuple = (self.__class__.__name__,
                                    type(df_or_serie),
                                    type(kwargs.get('parameter')),
                                    type(kwargs.get('acceptable_error')))
            raise AssertionError('Input types to class {} are no good: data ({}), parameter ({}), '
                                 'acceptable error ({})'.format(*assertionerror_tuple))

        if type(df_or_serie) == pd.DataFrame:
            self.serie = df_or_serie[kwargs.get('parameter')].astype(float)
        else:
            self.serie = df_or_serie.astype(float)

        self.boolean = kwargs.get('boolean')

    def __call__(self):
        """
        :param args:
        :param kwargs:
        :return:
        """
        self.serie.loc[self.boolean] = self.qflag


class QCBlueprint:
    """

    SHARK Qulity Control flags:
        0: No QC was performed
        A: Accepted/Good value
        B: Bad value
        S: Suspicious value

    """
    def __init__(self, data_item, **kwargs):
        try:
            assert type(data_item.get('data')) == pd.DataFrame
            assert type(data_item.get('metadata')) == pd.Series
        except AssertionError:
            assertion_error_tuple = (self.__class__.__name__,
                                     type(data_item.get('data')),
                                     type(data_item.get('metadata')))
            raise AssertionError('Input type to class {} should be pd.DataFrame and pd.Series not {} and {}'.format(
                *assertion_error_tuple))
        # self.qflag = kwargs.get('qflag')
        self.parameter_mapping = kwargs.get('parameter_mapping')

        self.df = data_item.get('data')
        self.meta = data_item.get('metadata')

        self.settings = Settings()

    def initialize_qc_object(self, setting, name, item):
        """
        :param setting:
        :param name:
        :param item:
        :return:
        """
        return setting['functions'][name].get('function')(self.df, **item)

    def __call__(self):
        """
        :param args:
        :param kwargs:
        :return:
        """
        self._open_up_flag_fields()

        for qc_routine, qc_index in self.settings.qc_routines.items():
            qc_setting = getattr(self.settings, qc_routine)

            for dataset, item in qc_setting['datasets'].items():

                # Check if parameters exists
                if not self.parameters_available(item):
                    continue

                # Check if data exists
                if not self.data_available(item):
                    continue

                # Get QC routine
                qc_func = self.initialize_qc_object(qc_setting, qc_routine, item)

                # Run QC routine
                qc_func()

                # Check results and execute appropriate action (flag the data)
                self.add_qflag(qc_func.flag_return,
                               item.get('q_parameters'),
                               qc_index)

        self._close_flag_fields()
        self.synchronize_flag_fields()
        self.append_qc_comment()

    def synchronize_flag_fields(self):
        """
        Auto-QC corresponds to flag field "Q0_{parameter}", when calling synchronize_flag_fields() we import flags from
        this field into the primary q-flag field "Q_{parameter}".
        Example:
            Q0_TEMP_CTD             Q_TEMP_CTD
            A00BA       ------>     B
            A00AS       ------>     S
            A00BS       ------>     B
            A00AA                     (A-flags will not be visible in primary flag field)

        ( during the manual quality control we only change the primary flag field )
        :return:
        """
        q0_fields = iter(q for q in self.df.columns if q.startswith('Q0_'))

        for q0_key in q0_fields:
            primary_q_key = q0_key.replace('Q0_', 'Q_')
            for f in ['S', 'B']:
                self._sync_flag(q0_key, primary_q_key, f)

    def _sync_flag(self, q0_key, q_key, flag):
        boolean = self.df[q0_key].str.contains(flag, regex=False)
        if boolean.any():
            self.df.loc[boolean, q_key] = flag

    def add_qflag(self, flag_field, q_flag_keys, qc_index):
        """
        :param flag_field:
        :param q_flag_keys:
        :param qc_index:
        :return:
        """
        for flag_key in q_flag_keys:
            if flag_key not in self.df:
                continue

            for qf_list, qf in zip(self.df[flag_key], flag_field):
                if qf_list[qc_index] == '0' or qf_list[qc_index] == 'A':
                    qf_list[qc_index] = qf
                elif qf_list[qc_index] == 'S' and qf == 'B':
                    qf_list[qc_index] = qf
                elif qf == 'S': # qf_list[qc_index] != 'B'
                    qf_list[qc_index] = qf

    def set_qc0_standard_format(self, key=None):
        """
        :param length:
        :return:
        """
        self.df[key] = ['0' * self.settings.number_of_routines] * self.df.__len__()

    def _open_up_flag_fields(self):
        """
        :return:
        """
        for key in self.df:
            key = key.split(' ')[0]
            if key not in ['YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND',
                           'CRUISE', 'STATION', 'LATITUDE_DD', 'LONGITUDE_DD']:
                if not key.startswith('Q'):
                    if 'Q0_'+key not in self.df:
                        self.set_qc0_standard_format(key='Q0_'+key)
                elif key.startswith('Q0_'):
                    if not type(self.df[key][0]) == str:
                        # In case we have a column for the QC-0 flags but not the correct format ('xxxxx')
                        self.set_qc0_standard_format(key=key)
                    elif not len(self.df[key][0]):
                        self.set_qc0_standard_format(key=key)

        for q_key in self.df:
            if q_key.startswith('Q0_'):
                self.df[q_key] = self.df[q_key].apply(list)

    def _close_flag_fields(self):
        """
        :return:
        """
        for q_key in self.df:
            if q_key.startswith('Q0_'):
                self.df[q_key] = self.df[q_key].apply(''.join)

    def parameters_available(self, item):
        """
        :param item:
        :return:
        """
        if item.get('parameter'):
            if item.get('parameter') in self.df:
                return True
            if self.parameter_mapping.get(item['parameter']):
                new_param = self.parameter_mapping.get(item['parameter'])
                if new_param in self.df:
                    item['parameter'] = new_param
                    return True

        if item.get('parameters'):
            if all(x in self.df for x in item.get('parameters')):
                return True
            mapped = [self.parameter_mapping.get(p) for p in item.get('parameters')]
            if all(mapped):
                if all(x in self.df for x in mapped):
                    item['parameters'] = mapped
                    return True

    def data_available(self, item):
        """
        :param item:
        :return:
        """
        if item.get('parameter'):
            if self.df[item.get('parameter')].any():
                return True

        if item.get('parameters'):
            if all(self.df[p].any() for p in item.get('parameters')):
                return True

    def append_qc_comment(self):
        """
        :param metadata:
        :return:
        """
        time_stamp = get_time_as_format(now=True, fmt='%Y%m%d%H%M')
        self.meta[len(self.meta) + 1] = '//COMNT_QC; AUTOMATIC QC PERFORMED BY {}; TIMESTAMP {}; {}'.format(
            self.settings.user, time_stamp, self.settings.repo_version)


if __name__ == "__main__":
    df = {'metadata': pd.Series([1, 2, 3, 4, 5]),
          'data': pd.DataFrame({'a': [1,2,3,4,5]})}
    qcb = QCBlueprint(df)
