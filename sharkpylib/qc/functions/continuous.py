# -*- coding: utf-8 -*-
"""
Created on 2020-02-20 13:34

@author: a002028

"""
import numpy as np
import pandas as pd
from sharkpylib.qc.boolean_base import BooleanBaseSerie
from sharkpylib.qc.messages import *


class ContinuousBase(BooleanBaseSerie):
    # FIXME if we need a boolean return (in order to say which values are causing the QC-routine to fail) we use
    #  BooleanBaseSerie. However, if we don´t need this, we can exclude the base inheritance..
    """
    """
    # def __init__(self, df_or_serie, parameter=None, acceptable_error=None):
    def __init__(self, df_or_serie, **kwargs):
        super().__init__()
        try:
            assert type(df_or_serie) == pd.DataFrame or pd.Series
            assert type(kwargs.get('parameter')) == str or type(None)
            assert type(kwargs.get('acceptable_error')) == int or float
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

        self.qc_passed = False
        self.acceptable_error = kwargs.get('acceptable_error')

    @property
    def boolean_return(self):
        """
        We append one "True" for the last value because these types of QC-routines check value 1
        against value 2. Therefor the last value cannot be False. However! it can in fact be value 2 that is BAD..

        :return: boolean list
                 True means that the corresponding value has passed the test
                 False means that the value has NOT passed and should be flagged
        """
        boolean = list(self.generator)
        boolean.append(True)
        return pd.Series(boolean)

    @property
    def flag_return(self):
        """
        #TODO add more flexibility to flag assignment
        :return:
        """
        flag_serie = np.array(['A'] * self.serie.__len__())
        flag_serie[~self.boolean_return] = 'B'
        return flag_serie

    @property
    def generator(self):
        raise NotImplementedError

    @property
    def error_magnitude_accepted(self):
        """
        :return: True or False
        """
        return all(self.generator)


class Decreasing(ContinuousBase):
    """
    QC-routine check if value 1 >= value 2 and so on..
    - If not passed: position 1 is flagged as False
    """
    def __call__(self):
        """
        :param args:
        :param kwargs:
        :return:
        """
        # TODO handle QC failure.. boolean? report?
        if self.serie.is_monotonic_decreasing:
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            if self.error_magnitude_accepted:
                # Data passed with acceptable error!
                self.qc_passed = True
                # qc_pass_message(self, self.serie.name)
            else:
                qc_fail_message(self, self.serie.name)

    @property
    def generator(self):
        """"""
        return (i >= j for i, j in zip(self.serie, self.control_serie[1:]))

    @property
    def control_serie(self):
        """"""
        return self.serie - self.acceptable_error


class Increasing(ContinuousBase):
    """
    QC-routine check if value 1 <= value 2 and so on..
    - If not passed: position 1 is flagged as False
    """
    def __call__(self):
        """
        :param args:
        :param kwargs:
        :return:
        """
        # TODO handle QC failure.. boolean? report?
        if self.serie.is_monotonic_increasing:
            # Data passed with distinction!
            self.qc_passed = True
            # qc_pass_message(self, self.serie.name)
        else:
            if self.error_magnitude_accepted:
                # Data passed with acceptable error!
                self.qc_passed = True
                # qc_pass_message(self, self.serie.name)
            else:
                qc_fail_message(self, self.serie.name)

    @property
    def generator(self):
        """"""
        return (i <= j for i, j in zip(self.serie, self.control_serie[1:]))

    @property
    def control_serie(self):
        """"""
        return self.serie + self.acceptable_error


if __name__ == "__main__":
    test_4 = [0, 1, 0.9, 2, 3]

    df = pd.DataFrame({
        'test_1': [3, 4, 6, 87, 3],
        'test_2': list(range(5)),
        'test_3': list(range(5))[::-1],
        'test_4': test_4})
    increasing = Increasing(df, parameter='test_4', acceptable_error=0.01)
    increasing()
    decreasing = Decreasing(df, parameter='test_3', acceptable_error=0.01)
    decreasing()
    # import operator
    # import itertools
    # from functools import reduce
    # import time
    #


    # test_list[4] = 1
    # ser = pd.Series(test_list)
    # start_timeit = time.time()
    # isinc = ser.is_monotonic_increasing
    # print("Timed: --is_monotonic_increasing in %.9f sec" % (time.time() - start_timeit))
    # print(isinc)
    #
    # start_timeit = time.time()
    # res = all(itertools.starmap(operator.le, zip(test_list, test_list[1:])))
    # print("Timed: --itertools.starmap in %.9f sec" % (time.time() - start_timeit))
    # print(res)
    #
    # # start_timeit = time.time()
    # # res = bool(lambda test_list: reduce(lambda i, j: j if i < j else 9999, test_list) != 9999)
    # # # res = lambda test_list: lambda i, j: True if i < j else False
    # # # ser.apply(lambda x: lambda i, j: True if i < j else False)
    # # print("Timed: --data loaded in %.3f sec" % (time.time() - start_timeit))
    # # print(res)
    # start_timeit = time.time()
    # res = all(i < j for i, j in zip(test_list, test_list[1:]))
    # print("Timed: --zip in %.9f sec" % (time.time() - start_timeit))
    # print(res)
