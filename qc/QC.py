#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2018-2019 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).


import numpy as np
import seawater as sw

class QC(object):

    def __init__(self):

        pass

    def _convert_to_np_array(self, in_data):
        """
        Tries to convert iterable input to numpy array
        :param input: iterable
        :return: input as numpy array
        """
        try:
            data = np.array(in_data)
        except:
            try:
                iterator = iter(in_data)
                data = np.array([])
                for i in iterator:
                    data = np.append(data, i)
            except TypeError as te:
                print('input is not iterable:', in_data)

        return data



    def range_check(self, data=False, qf=False, lower_limit=0, upper_limit=40, depth=False, max_depth=False, min_depth=False, qf_ignore=['B','S','?']):

        """
        Range check routine for checking if data is below lower_limit or above upper_limit
        :param data: data input as a list or iterable that can be converted to a numpy array
        :param qf: quality flag as a list or iterable that can be converted to a numpy array
        :param lower_limit: lower value, flag data below this value
        :param upper_limit: upper value, flag data above this value
        :param depth: depth input as a list or iterable that can be converted to a numpy array
        :param max_depth: max depth, check only data above this depth
        :param min_depth: min depth, check only data below this depth
        :return: index for flag changes and the new flag array, also an array with numeric index positions for suggested flag changes
        """

        if data:
            data = self._convert_to_np_array(data)
        #     try:
        #         self.data = np.array(data)
        #     except:
        #         try:
        #             iterator = iter(data)
        #             self.data = np.array([])
        #             for i in iterator:
        #                 self.data = np.append(self.data, i)
        #         except TypeError as te:
        #             print('data is not iterable:', data)
        # else:
        #     raise ValueError('no data was supplied!')

        index_depth = np.full((len(data)), True)

        if depth:
            depth = self._convert_to_np_array(depth)
            # try:
            #     self.depth = np.array(depth)
            # except:
            #     try:
            #         iterator = iter(depth)
            #         self.depth = np.array([])
            #         for i in iterator:
            #             self.depth = np.append(self.depth, i)
            #     except TypeError as te:
            #         print('depth is not iterable:', depth)

            if len(depth) != len(data):
                raise ValueError('data and depth are not the same length, %s and %s' % (len(data), len(depth)))

            if max_depth:
                index_depth = index_depth & (depth <= max_depth)

            if min_depth:
                index_depth = index_depth & (depth >= min_depth)


        if qf:
            qf = self._convert_to_np_array(qf)
            # try:
            #     self.qf = np.array(qf)
            # except:
            #     try:
            #         iterator = iter(qf)
            #         self.qf = np.array([])
            #         for i in iterator:
            #             self.qf = np.append(self.qf, i)
            #     except TypeError as te:
            #         print('qf is not iterable:', qf)

            if qf_ignore:
                for i in qf_ignore:
                    index_depth = index_depth & (qf != i)



            index_below = data < lower_limit

            index_above = data > upper_limit

            qfindex = index_depth & (index_below | index_above)

            new_qf = qf
            new_qf[qfindex] = 'B'

            qfindex_numeric = np.arange(len(data))
            qfindex_numeric = qfindex_numeric[qfindex]


        return qfindex, new_qf, qfindex_numeric

    def increasing_dens(self, temperature=False, qtemp=[], salinity=False, qsalt=[], pressure=False, qpres=[], min_delta = 0.01, qf_ignore = ['B','S','?']):

        temp = self._convert_to_np_array(temperature)
        salt = self._convert_to_np_array(salinity)
        pres = self._convert_to_np_array(pressure)

        dens = sw.pden(salt, temp, pres, 0)


        dens_temp = False

        qfindex = np.full((len(temp)), False)
        new_qf = np.array(['']*len(temp))

        for i, d in enumerate(dens):
            if len(qtemp) > 0:
                if qtemp[i] in qf_ignore:
                    qfindex[i] = True
                    continue
            if len(qsalt) > 0:
                if qsalt[i] in qf_ignore:
                    qfindex[i] = True
                    continue
            if len(qpres) > 0:
                if qpres[i] in qf_ignore:
                    qfindex[i] = True
                    continue

            if dens_temp:
                if dens_temp > d: # not increasing = bad
                    if (dens_temp-d) >= min_delta:
                        qfindex[i] = True

            dens_temp = d

        new_qf[qfindex] = 'B'

        qfindex_numeric = np.arange(len(temp))
        qfindex_numeric = qfindex_numeric[qfindex]

        return qfindex, new_qf, qfindex_numeric

    def increasing(self, data=False, qf=[], min_delta = 0.01, qf_ignore = ['B','S','?']):

        data = self._convert_to_np_array(data)

        data_temp = False

        qfindex = np.full((len(data)), False)
        new_qf = np.array(['']*len(data))

        for i, d in enumerate(data):
            if len(qf) > 0:
                if qf[i] in qf_ignore:
                    continue


            if data_temp:
                if data_temp > d: # not increasing = bad
                    if (data_temp-d) >= min_delta:
                        qfindex[i] = True

            data_temp = d

        new_qf[qfindex] = 'B'

        qfindex_numeric = np.arange(len(data))
        qfindex_numeric = qfindex_numeric[qfindex]

        return qfindex, new_qf, qfindex_numeric

    def spike_check(self):
        pass

        # djupderivata

        # kolla mot punkt före och efter

    # std mot min/max utifrågn satta gränser (typ av klimatologi)
    # CMEMS har vissa gränser satta från data på stationer (och månad)

    # std mot hela profilen

    # delta mellan sensorer om flera finns

