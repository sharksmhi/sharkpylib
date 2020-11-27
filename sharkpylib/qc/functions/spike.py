# -*- coding: utf-8 -*-
"""
Created on 2020-04-14 12:20

@author: a002028

"""
import numpy as np
import pandas as pd
from sharkpylib.qc.boolean_base import BooleanBaseSerie
from sharkpylib.qc.messages import *


class Spike(BooleanBaseSerie):
    """
    ----------  A very informative description of this class, and its purpose  ----------
    """
    def __init__(self, df_or_serie, **kwargs):
        super().__init__()
        try:
            assert type(df_or_serie) == pd.DataFrame or pd.Series
            assert type(kwargs.get('parameter')) == str
            assert type(kwargs.get('acceptable_stddev_factor')) == int or float
            assert type(kwargs.get('min_stddev_value')) == int or float
        except AssertionError:
            #TODO Fix Logging..
            type_tuple = (self.__class__.__name__,
                          type(df_or_serie),
                          type(kwargs.get('parameter')),
                          type(kwargs.get('acceptable_stddev_factor')),
                          type(kwargs.get('min_stddev_value')))
            raise AssertionError('Input types to class {} are no good: data ({}), parameter ({}), '
                                 'acceptable_stddev_factor ({}), min_stddev_value ({})'.format(*type_tuple))

        self.qc_passed = False
        self.q_flag = kwargs.get('q_flag') or 'B'

        if type(df_or_serie) == pd.DataFrame:
            self.serie = df_or_serie[kwargs.get('parameter')].astype(float)
        else:
            self.serie = df_or_serie.astype(float)
        self.acceptable_stddev_factor = kwargs.get('acceptable_stddev_factor')
        self.min_stddev_value = kwargs.get('min_stddev_value')

        # self.index_window = 7  # ok window? user can control the outcome with acceptable_stddev_factor
        # self.min_periods = 3  # or np.floor(self.index_window / 2)
        self.rolling = self.serie.rolling(7, min_periods=3, center=True)

    def __call__(self):
        """
        :param args:
        :param kwargs:
        :return:
        """
        self.add_boolean_less_than_other(self.max)
        self.add_boolean_greater_than_other(self.min)

        if all(self.boolean):
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            qc_fail_message(self, self.serie.name)

    @property
    def min(self):
        """
        :return:
        """
        return self._mean - self._std

    @property
    def max(self):
        """
        :return:
        """
        return self._mean + self._std

    @property
    def _mean(self):
        """"""
        return self.rolling.mean()

    @property
    def _std(self):
        """"""
        std_serie = self.rolling.std()
        boolean = std_serie < self.min_stddev_value
        std_serie[boolean] = self.min_stddev_value
        return std_serie * self.acceptable_stddev_factor

    @property
    def boolean_return(self):
        """
        :param reversed:
        :return: boolean list
                 True means that the corresponding value has passed the test
                 False means that the value has NOT passed and should be flagged
        """
        return self.boolean

    @property
    def flag_return(self):
        """
        :return:
        """
        flag_serie = np.array(['A'] * self.serie.__len__())
        flag_serie[~self.boolean_return] = self.q_flag
        return flag_serie
