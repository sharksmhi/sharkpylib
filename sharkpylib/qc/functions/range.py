# -*- coding: utf-8 -*-
"""
Created on 2020-02-20 11:45

@author: a002028

"""
import numpy as np
import pandas as pd
from sharkpylib.qc.boolean_base import BooleanBaseSerie
from sharkpylib.qc.messages import *


class Range(BooleanBaseSerie):
    """

    """
    # def __init__(self, df, parameter=None, min_range_value=None, max_range_value=None):
    def __init__(self, df_or_serie, **kwargs):
        super().__init__()
        try:
            assert type(df_or_serie) == pd.DataFrame or pd.Series
            assert type(kwargs.get('parameter')) == str
            assert type(kwargs.get('min_range_value')) == int or float
            assert type(kwargs.get('max_range_value')) == int or float
        except AssertionError:
            #TODO Fix Logging..
            type_tuple = (self.__class__.__name__,
                          type(df_or_serie),
                          type(kwargs.get('parameter')),
                          type(kwargs.get('min_range_value')),
                          type(kwargs.get('max_range_value')))
            raise AssertionError('Input types to class {} are no good: data ({}), parameter ({}), range values ({}, {})'.format(*type_tuple))

        self.qc_passed = False
        if type(df_or_serie) == pd.DataFrame:
            self.serie = df_or_serie[kwargs.get('parameter')].astype(float)
        else:
            self.serie = df_or_serie.astype(float)
        self.min = kwargs.get('min_range_value')
        self.max = kwargs.get('max_range_value')

    def __call__(self):
        """
        :param args:
        :param kwargs:
        :return:
        """
        self.add_boolean_less_or_equal(self.max)
        self.add_boolean_greater_or_equal(self.min)

        if all(self.boolean):
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            qc_fail_message(self, self.serie.name)

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
        flag_serie[~self.boolean_return] = 'B'
        return flag_serie


if __name__ == "__main__":
    # df = pd.DataFrame({'TEMP': [3, 4, 6, 87, 3]})
    # r = Range(df, parameter='TEMP', min_range_value=2, max_range_value=540)
    # r()
    import time

    df = pd.DataFrame({'TEMP': ['AAAA']*100000 })

    start_timeit = time.time()
    df['TEMP'].apply(tuple)
    print("Timed: --apply(tuple) in %.9f sec" % (time.time() - start_timeit))

    start_timeit = time.time()
    li = df['TEMP'].apply(list)
    # tup.apply(''.join)
    print("Timed: --apply(list) in %.9f sec" % (time.time() - start_timeit))

    def set_flag(value, i, flag):
        value[i] = flag
        return value

    start_timeit = time.time()
    li = li.apply(lambda x: set_flag(x, 1, 'Bb'))
    print("Timed: --set_flag in %.9f sec" % (time.time() - start_timeit))

    start_timeit = time.time()
    li.apply(''.join)
    print("Timed: --join in %.9f sec" % (time.time() - start_timeit))

    a = [[1, 2, 3]] * 1000000
    a = pd.Series(a)
    b = [6] * 100

    start_timeit = time.time()
    index = 1
    # def ff(i, j):
    #     i[index] = j
    #     return i
    # generator = (ff(i, j) for i, j in zip(a, b))
    # a = list(generator)

    for i, j in zip(a, b):
        i[index] = j
    print("Timed: --generator in %.9f sec" % (time.time() - start_timeit))

