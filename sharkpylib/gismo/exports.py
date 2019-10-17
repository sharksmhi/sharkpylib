#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).


from .exceptions import *


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
        self.classes = {'CMEMS_gridded': CMEMSgridded}

        self.required_arguments = {'CMEMS_gridded': ['file_path']}

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


class CMEMSgridded(object):
    """
    Created 20181005     

    Class to perform QC on gismo ferrybox data
    """
    def __init__(self, file_path):
        pass

    def export(self):
        pass






