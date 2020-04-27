# -*- coding: utf-8 -*-
"""
Created on 2020-02-20 13:29

@author: a002028

"""


def qc_fail_message(obj, spec):
    print('QC-{} failed for {}'.format(obj.__class__.__name__, spec))


def qc_pass_message(obj, spec):
    print('QC-{} passed for {}'.format(obj.__class__.__name__, spec))
