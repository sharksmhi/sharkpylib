# -*- coding: utf-8 -*-
"""
Created on 2020-02-25 14:16

@author: a002028

"""
import numpy as np
import pandas as pd
from sharkpylib.qc.boolean_base import BooleanBaseDataFrame
from sharkpylib.qc.messages import *


class DiffBase(BooleanBaseDataFrame):
    """
    """
    # def __init__(self, df, parameters=None, acceptable_error=None):
    def __init__(self, df, **kwargs):
        super().__init__()
        try:
            assert type(df) == pd.DataFrame or pd.Series
            assert type(kwargs.get('parameters')) == list
            assert type(kwargs.get('acceptable_error')) == int or float
        except AssertionError:
            #TODO Fix Logging..
            assertionerror_tuple = (self.__class__.__name__,
                                    type(df),
                                    type(kwargs.get('parameters')),
                                    type(kwargs.get('acceptable_error')))
            raise AssertionError('Input types to class {} are no good: data ({}), parameter ({}), '
                                 'acceptable error ({})'.format(*assertionerror_tuple))

        self.qc_passed = False
        self.parameters = kwargs.get('parameters')
        self.data = df[self.parameters].astype(float)
        self.acceptable_error = kwargs.get('acceptable_error')

    @property
    def boolean_return(self):
        """
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
        flag_serie = np.array(['A'] * self.data.__len__())
        flag_serie[~self.boolean_return] = 'B'
        return flag_serie


class DataDiff(DiffBase):
    """
    We check how values for x number of parameters differ from one another
    """
    def __call__(self):
        """
        :param args:
        :param kwargs:
        :return:
        """
        self.add_boolean_diff(self.parameters, self.acceptable_error)
        # TODO handle QC failure.. boolean? report?
        if all(self.boolean):
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.parameters)
        else:
            qc_fail_message(self, self.parameters)


if __name__ == "__main__":

    import numpy as np
    df = pd.DataFrame({'a': [1, 2, 3, 7.2, 5, 6],
                       'b': [2, 3, 4, 5, 6, 7],
                       'c': [4., 5., 6., 7., 8., 9.]})

    diff = DataDiff(df, parameters=['a', 'b'], acceptable_error=2.2)
    diff()
    # diffing = df[['a', 'b']].astype(float).diff(axis=1).abs()
    # # print(diffing['b'])
    # print(diffing['b'])


