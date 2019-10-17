# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on Tue Mar 07 11:48:49 2017

@author:
"""

try:
    import pandas as pd
    import numpy as np
except:
    pass

from .exceptions import *
from .. import utils


import pickle


# ==============================================================================
# ==============================================================================
class GISMOdataManager(object):
    """
    Created 20181003     

    Class manager to handle qc of GISMO-objects.
    """

    def __init__(self, factory, *args, **kwargs):
        self.factory = factory
        self.sampling_type_list = factory.get_list()
        self.objects = {}
        self.objects_by_sampling_type = dict((item, {}) for item in self.sampling_type_list)

        self.match_objects = {}

    def has_file_id(self, *arg, **kwargs):
        try:
            self._check_file_id()
            return True
        except:
            return False

    def has_metadata(self, file_id):
        self._check_file_id(file_id)
        gismo_object = self.objects.get(file_id)
        return gismo_object.has_metadata

    def _check_file_id(self, file_id):
        """
        Raises GISMOExceptionInvalidFileId if file_id not in loaded data.
        :param file_id:
        :return: None
        """
        if file_id not in self.objects:
            raise GISMOExceptionInvalidFileId(file_id)

    def load_file(self, sampling_type='', **kwargs):

        if sampling_type not in self.sampling_type_list:
            raise GISMOExceptionInvalidSamplingType
            # This might not be necessary if pkl file is loaded

        # Check if we should load pkl file
        if kwargs.get('load_pkl') and kwargs.get('pkl_file_path'):
            with open(kwargs.get('pkl_file_path'), "rb") as fid:
                gismo_object = pickle.load(fid)
        else:
            gismo_object = self.factory.get_object(sampling_type=sampling_type, **kwargs)
            if kwargs.get('save_pkl') and kwargs.get('pkl_file_path'):
                # Save pkl file of the object
                with open(kwargs.get('pkl_file_path'), "wb") as fid:
                    pickle.dump(gismo_object, fid)

        self.objects[gismo_object.file_id] = gismo_object
        self.objects_by_sampling_type[sampling_type][gismo_object.file_id] = gismo_object

    def remove_file(self, file_id):
        if file_id in self.objects:
            self.objects.pop(file_id)
            for sampling_type in self.objects_by_sampling_type.keys():
                if file_id in self.objects_by_sampling_type[sampling_type]:
                    self.objects_by_sampling_type[sampling_type].pop(file_id)
                    break


    def flag_data(self, file_id, flag, *args, **kwargs):
        """
        Created 20181004     

        Flags data in file_id.
        :param file_id:
        :param args:
        :param kwargs:
        :return:
        """
        self._check_file_id(file_id)
        gismo_object = self.objects.get(file_id)

        flag = str(flag)
        if flag not in gismo_object.valid_flags:
            raise GISMOExceptionInvalidFlag('"{}", valid flags are "{}"'.format(flag, ', '.join(gismo_object.valid_flags)))

        # Check if valid options
        for key in kwargs:
            if key not in gismo_object.flag_data_options:
                raise GISMOExceptionInvalidOption('{} is not a valid filter option'.format(key))

        return self.objects.get(file_id).flag_data(flag, *args, **kwargs)

    def get_data_object(self, file_id, *args, **kwargs):
        """ Should not be used """
        self._check_file_id(file_id)
        return self.objects.get(file_id)

    def get_filter_options(self, file_id, **kwargs):
        """
        Created 20181004     

        :return: list of filter options
        """
        self._check_file_id(file_id)
        return self.objects.get(file_id).filter_data_options

    def get_flag_options(self, file_id, **kwargs):
        """

        :param file_id:
        :param kwargs:
        :return:
        """
        self._check_file_id(file_id)
        return self.objects.get(file_id).flag_data_options

    def get_filtered_file_id_list(self, **kwargs):
        """

        :param kwargs:
        :return: list of file_id matching filter options in kwargs.
        """

        # List options in kwargs to check
        #----------------------------------

        # Station
        station = kwargs.get('stations', [])
        if station and type(station) != list:
            station = [station]
        if not kwargs.get('case_sensitive', True):
            station = [item.lower() for item in station]

        # print('kwargs', kwargs)
        # Position
        check_pos = False
        for pos in ['lat_min', 'lat_max', 'lon_min', 'lon_max']:
            if kwargs.get(pos, None) is not None:
                check_pos = True
                break
        lat_min = kwargs.get('lat_min', 0.)
        lat_max = kwargs.get('lat_max', 90.)
        lon_min = kwargs.get('lon_min', -180.)
        lon_max = kwargs.get('lon_max', 180.)

        # ----------------------------------

        matching_file_id_list = []
        for file_id in self.get_file_id_list():
            gismo_object = self.objects.get(file_id)

            if not file_id.startswith(kwargs.get('startswith', '')):
                continue
            # Check station
            if station:
                try:
                    statn = gismo_object.get_station_name()
                    if not kwargs.get('case_sensitive', True):
                        statn = statn.lower()
                    if statn not in station:
                        continue
                except GISMOExceptionMethodNotImplemented:
                    pass

            # Check position
            if check_pos:
                pos = gismo_object.get_position()
                lat, lon = pos
                if type(lat) in [float, int]:
                    lat = np.array([lat])
                    lon = np.array([lon])
                else:
                    lat = np.array(lat)
                    lon = np.array(lon)
                if not any((lat >= lat_min) & (lat <= lat_max) & (lon >= lon_min) & (lon <= lon_max)):
                    continue

            # Check time
            time_array = np.array([pd.to_datetime(item) for item in gismo_object.get_time()])
            if kwargs.get('time_from') and all(time_array < kwargs.get('time_from')):
                continue
            if kwargs.get('time_to') and all(time_array > kwargs.get('time_to')):
                continue
            if type(kwargs.get('season', None)) == dict:
                season = kwargs.get('season')
                for time_object in time_array:
                    if season['month_from'] < time_object.month < season['month_to']:
                        break
                    elif time_object.month == season['month_from'] == season['month_to']:
                        if season['day_from'] <= time_object.day <= season['day_to']:
                            break
                    elif time_object.month == season['month_from'] and time_object.day >= season['day_from']:
                        break
                    elif time_object.month == season['month_to'] and time_object.day <= season['day_to']:
                        break
                else:
                    continue

                # if season.get('month_from') and all([item.month < season.get('month_from') for item in time_array]):
                #     continue
                # if season.get('month_to') and all([item.month > season.get('month_to') for item in time_array]):
                #     continue
                # if season.get('day_from') and all([item.day < season.get('day_from') for item in time_array]):
                #     continue
                # if season.get('day_to') and all([item.day > season.get('day_to') for item in time_array]):
                #     continue


            # If file_id passes every test it will be included in the return list
            matching_file_id_list.append(file_id)

        return matching_file_id_list


    def get_mask_options(self, file_id, **kwargs):
        """

        :param file_id:
        :param kwargs:
        :return:
        """
        self._check_file_id(file_id)
        return self.objects.get(file_id).mask_data_options

    def get_save_data_options(self, file_id, **kwargs):
        """

        :param file_id:
        :param kwargs:
        :return:
        """
        self._check_file_id(file_id)
        return self.objects.get(file_id).save_data_options

    def get_station_list(self):
        station_list = []
        for file_id in self.get_file_id_list():
            gismo_object = self.objects.get(file_id)
            try:
                station_list.append(gismo_object.get_station_name())
            except GISMOExceptionMethodNotImplemented:
                pass
        return sorted(set(station_list))

    def get_file_id_list(self, sampling_type=None):
        if sampling_type:
            return sorted(self.objects_by_sampling_type.get(sampling_type))
        else:
            return sorted(self.objects.keys())

    def get_match_object(self, main_file_id, match_file_id, *args, **kwargs):
        self._check_file_id(main_file_id)
        self._check_file_id(match_file_id)
        if not self.match_objects.get(main_file_id) or not self.match_objects.get(main_file_id).get(match_file_id):
            raise GISMOExceptionInvalidInputArgument

        return self.match_objects.get(main_file_id).get(match_file_id)

    def get_match_data(self, main_file_id, match_file_id, *args, **kwargs):
        self._check_file_id(main_file_id)
        self._check_file_id(match_file_id)
        if not self.match_objects.get(main_file_id) or not self.match_objects.get(main_file_id).get(match_file_id):
            raise GISMOExceptionInvalidInputArgument

        match_object = self.match_objects.get(main_file_id).get(match_file_id)
        return match_object.get_match_data(*args, **kwargs)

    def get_merge_data(self, main_file_id, match_file_id, *args, **kwargs):
        self._check_file_id(main_file_id)
        self._check_file_id(match_file_id)
        if not self.match_objects.get(main_file_id) or not self.match_objects.get(main_file_id).get(match_file_id):
            raise GISMOExceptionInvalidInputArgument

        match_object = self.match_objects.get(main_file_id).get(match_file_id)
        return match_object.get_merge_data(*args, **kwargs)


    def get_data(self, file_id, *args, **kwargs):
        """
        Created 20181004     
        Updated 20181005     

        :param file_id: file name minus the extension
        :param args:
        :param options:
        :param kwargs: specify filter. For example profile_id=<something>
        :return:
        """
        self._check_file_id(file_id)

        # Check if valid options
        for key in kwargs.get('filter_options', {}):
            if key not in self.get_filter_options(file_id):
                raise GISMOExceptionInvalidOption('{} is not a valid filter option'.format(key))

        for key in kwargs.get('flag_options', {}):
            if key not in self.get_flag_options(file_id):
                raise GISMOExceptionInvalidOption('{} is not a valid flag option'.format(key))

        for key in kwargs.get('mask_options', {}):
            if key not in self.get_mask_options(file_id):
                raise GISMOExceptionInvalidOption('{} is not a valid mask option'.format(key))

        gismo_object = self.objects.get(file_id)
        return gismo_object.get_data(*args, **kwargs)

    def get_parameter_list(self, file_id, **kwargs):
        self._check_file_id(file_id)
        return self.objects.get(file_id).get_parameter_list(**kwargs)

    def get_position(self, file_id, **kwargs):
        """
        :param file_id:
        :param kwargs:
        :return: List with position(s). Two options:
        fixed position: [lat, lon]
        trajectory: [[lat, lat, lat, ...], [lon, lon, lon, ...]]
        """
        self._check_file_id(file_id)
        return self.objects.get(file_id).get_position(**kwargs)

    def get_unit(self, file_id, unit, **kwargs):
        self._check_file_id(file_id)
        return self.objects.get(file_id).get_unit(unit, **kwargs)

    def get_valid_qc_routines(self, file_id):
        self._check_file_id(file_id)
        return self.objects.get(file_id).get_valid_qc_routines()

    def match_files(self, main_file_id, match_file_id, **kwargs):
        if not all([self.objects.get(main_file_id), self.objects.get(match_file_id)]):
            raise GISMOExceptionInvalidInputArgument

        self.match_objects.setdefault(main_file_id, {})
        self.match_objects[main_file_id][match_file_id] = MatchGISMOdata(self.objects.get(main_file_id),
                                                                         self.objects.get(match_file_id), **kwargs)

    def save_file(self, file_id, **kwargs):
        for key in kwargs:
            if key not in self.get_save_data_options(file_id):
                raise GISMOExceptionInvalidOption('{} is not a valid save data option'.format(key))

        self.objects.get(file_id).save_file(**kwargs)


# ==============================================================================
# ==============================================================================
class GISMOdata(object):
    """
    Created 20181003     
    Updated 20181005     

    Base class for a GISMO data file.
    A GISMO-file only has data from one sampling type.
    """

    def __init__(self, *args, **kwargs):
        self.file_id = ''

        self.parameter_list = []        # Valid data parameters
        self.filter_data_options = []   # Options for data filter (what to return in def get_data)
        self.flag_data_options = []     # Options for flagging data (where should data be flagged)
        self.mask_data_options = []     # Options for masking data (replaced by "missing value"

        self.save_data_options = []     # Options for saving data

        self.valid_flags = []

        self.valid_qc_routines = []     # Specify the valid qc routines

        self.comment_id = None

        self.metadata = None

    def add_qc_comment(self, comment):
        """

        :param comment:
        :return:
        """
        raise GISMOExceptionMethodNotImplemented

    def flag_data(self, flag, *args, **kwargs):
        """
        Created 20181004     

        :param flag: The flag you want to set for the parameter
        :param args: parameters that you want to flag.
        :param kwargs: conditions for flagging. Options are listed in self.flag_data_options
        :return: None
        """
        raise GISMOExceptionMethodNotImplemented

    def get_data(self, *args, **kwargs):
        """
        Created 20181004     

        :param args: parameters that you want to have data for.
        :param kwargs: specify filter. For example profile_id=<something>.
        :return: dict. each argument in args should be a key in the dict. Value are lists or arrays representing that key.
        """
        raise GISMOExceptionMethodNotImplemented

    def get_qf_list(self, *args, **kwargs):
        """
        :param args: parameters
        :param kwargs:
        :return: dict with parameters as keys and corresponding qf list as value.
        """
        raise GISMOExceptionMethodNotImplemented

    def get_metadata_tree(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        :return: dict with metadata information.
        """
        raise GISMOExceptionMethodNotImplemented

    def get_parameter_list(self, *args, **kwargs):
        """
        :return: list of available data parameters. Parameters that have quality flags.
        """
        return sorted(self.parameter_list)

    def get_position(self, **kwargs):
        """
        :param kwargs:
        :return: List with position(s). Two options:
        fixed position: [lat, lon]
        trajectory: [[lat, lat, lat, ...], [lon, lon, lon, ...]]
        """
        raise GISMOExceptionMethodNotImplemented

    def get_time(self, **kwargs):
        """
        :param kwargs:
        :return: list of timestamps
        """
        raise GISMOExceptionMethodNotImplemented

    def get_internal_parameter_name(self, parameter):
        """
        :param parameter:
        :return: internal name of the given parameter.
        """
        raise GISMOExceptionMethodNotImplemented

    def get_external_parameter_name(self, parameter):
        """
        :param parameter:
        :return: external name of the given parameter.
        """
        raise GISMOExceptionMethodNotImplemented

    def get_unit(self, unit, **kwargs):
        """

        :return: the unit of the parameter
        """
        raise GISMOExceptionMethodNotImplemented

    def get_valid_qc_routines(self, **kwargs):
        """

        :return: list of valid qc routines
        """
        return sorted(self.valid_qc_routines)

    def get_station_name(self, **kwargs):
        """

        :return: the station name if possible
        """
        raise GISMOExceptionMethodNotImplemented

    @property
    def has_metadata(self):
        """
        Returns True if metadata is not None. Else False.
        :return:
        """
        if self.metadata is not None:
            return True
        else:
            return False

    def save_file(self, **kwargs):
        """
        Saves data to file. Also saves metadata if available.

        """
        raise GISMOExceptionMethodNotImplemented

"""
========================================================================
========================================================================
"""


class GISMOqcManager(object):
    """
    Created 20181002     

    Class manager to handle qc of GISMO-objects.
    """

    def __init__(self, factory, *args, **kwargs):
        """
        Handles qc controll of gismo_objects.

        :param factory:
        :param args:
        :param kwargs:
        """
        self.factory = factory
        self.qc_routine_list = factory.get_list()
        self.qc_routines = {}

    def _check_qc_routine(self, qc_routine):
        """
        Adds qc_routine if not added before.
        :return:
        """
        if qc_routine not in self.qc_routine_list:
            raise GISMOExceptionInvalidQCroutine(qc_routine)

        if not self.qc_routines.get(qc_routine):
            self.add_qc_routine(qc_routine)


    def add_qc_routine(self, routine, **kwargs):
        self.qc_routines[routine] = self.factory.get_object(routine=routine, **kwargs)

    def run_automatic_qc(self, gismo_object=None, gismo_objects=[], qc_routine=None, **kwargs):
        """
        Runs the qc routines specified in qc_routines on the given gismo_object.

        :param gismo_object:
        :param args:
        :return: True if successful
        """
        if not qc_routine:
            raise GISMOExceptionMissingInputArgument('No qc_routine given.')

        if gismo_object:
            gismo_objects = [gismo_object]

        # Check if all qc_routines are valid for the given gismo_object
        for gismo_object in gismo_objects:
            if qc_routine not in gismo_object.valid_qc_routines:
                raise GISMOExceptionInvalidQCroutine(qc_routine)

        self._check_qc_routine(qc_routine)

        qc_routine_objects = self.qc_routines.get(qc_routine)

        # Run qc
        qc_routine_objects.run_qc(gismo_objects, **kwargs)

        # Add comment in metadata
        user = kwargs.pop('user', 'unknown user')
        employee = utils.get_employee_name()
        computer = utils.get_computer_name()

        # date/time will be set later
        comment = '{} ({} / {} / {})'.format(qc_routine, employee, computer, user)

        for gismo_object in gismo_objects:
            if gismo_object.has_metadata:
                gismo_object.add_qc_comment(comment)



    def get_qc_options(self, qc_routine):
        self._check_qc_routine(qc_routine)
        qc_object = self.qc_routines.get(qc_routine)
        return qc_object.get_options()




"""
========================================================================
========================================================================
"""
class GISMOqc(object):
    """
    Created 20181002     

    Base class to handle quality control of GISMO-objects.
    """

    def __init__(self, *args, **kwargs):
        self.name = ''

    def run_qc(self, gismo_objects, **kwargs):
        """
        Data is generally in a pandas dataframe that can be reach under gismo_object.df

        Make sure self.name is in gismo_object.valid_qc_routines

        :param gismo_objects: gismo objects or objects as a list.
        :return:
        """
        raise GISMOExceptionMethodNotImplemented

    def get_information(self):
        """
        Should return a dict with information about the QC routine.
        :return:
        """
        raise GISMOExceptionMethodNotImplemented

    def get_options(self):
        """
        Should return a dict with options available for the qc routine. Key is the option itself.
        Value are tho available choices for the corresponding option. Choices can be of the following types:

        list: multi select
        empty list: free nr of inputs (ex. list of quality flags)
        tuple: single select
        string: free text
        float: free float number
        int: free int number

        :return:
        """
        return {}


class MatchGISMOdata(object):
    """
    Class to match data from two GISMOdata objects.
    """
    def __init__(self,
                 main_gismo_object,
                 match_gismo_object,
                 tolerance_dist=1,  # distance in deg
                 tolerance_depth=1, # distance in meters
                 tolerance_hour=0,
                 **kwargs):

        self.main_object = main_gismo_object
        self.match_object = match_gismo_object
        self.merge_df_main = pd.DataFrame()
        self.merge_df_match = pd.DataFrame()

        # Save tolearances
        self.tolerance_dist = kwargs.get('dist', tolerance_dist)
        self.tolerance_depth = int(kwargs.get('depth', tolerance_depth))
        self.tolerance_time = pd.Timedelta(days=kwargs.get('days', 0), hours=kwargs.get('hours', tolerance_hour))

        # Run steps
        self._limit_data_scope(**kwargs)
        self._find_match(**kwargs)
        self._find_merge(**kwargs)


    def _limit_data_scope(self, **kwargs):
        """
        Narrow the data scope. Data outside the the tolerance is removed.
        :return:
        """

        main_df = self.main_object.df
        match_df = self.match_object.df

        # Time
        main_time_boolean = (main_df['time'] >= (np.nanmin(match_df['time']) - self.tolerance_time)) & (
                main_df['time'] <= (np.nanmax(match_df['time']) + self.tolerance_time))

        match_time_boolean = (match_df['time'] >= (np.nanmin(main_df['time']) - self.tolerance_time)) & (
                match_df['time'] <= (np.nanmax(main_df['time']) + self.tolerance_time))

        # Pos
        main_data = self.main_object.get_data('lat', 'lon', 'depth', type_float=True)
        match_data = self.match_object.get_data('lat', 'lon', 'depth', type_float=True)
#        print(type(self.tolerance_dist), type(self.tolerance_depth))
        main_lat_boolean = (main_data['lat'] >= (np.nanmin(match_data['lat']) - self.tolerance_dist)) & (
                main_data['lat'] <= (np.nanmax(match_data['lat']) + self.tolerance_dist))
        main_lon_boolean = (main_data['lon'] >= (np.nanmin(match_data['lon']) - self.tolerance_dist)) & (
                main_data['lon'] <= (np.nanmax(match_data['lon']) + self.tolerance_dist))

        match_lat_boolean = (match_data['lat'] >= (np.nanmin(main_data['lat']) - self.tolerance_dist)) & (
                match_data['lat'] <= (np.nanmax(main_data['lat']) + self.tolerance_dist))
        match_lon_boolean = (match_data['lon'] >= (np.nanmin(main_data['lon']) - self.tolerance_dist)) & (
                match_data['lon'] <= (np.nanmax(main_data['lon']) + self.tolerance_dist))

        # Depth
        main_depth_boolean = (main_data['depth'] >= (np.nanmin(match_data['depth']) - self.tolerance_depth)) & (
                main_data['depth'] <= (np.nanmax(match_data['depth']) + self.tolerance_depth))

        match_depth_boolean = (match_data['depth'] >= (np.nanmin(main_data['depth']) - self.tolerance_depth)) & (
                match_data['depth'] <= (np.nanmax(main_data['depth']) + self.tolerance_depth))

        self.main_time_boolean = main_time_boolean
        self.main_lat_boolean = main_lat_boolean
        self.main_lon_boolean = main_lon_boolean
        self.main_depth_boolean = main_depth_boolean

        self.match_time_boolean = match_time_boolean
        self.match_lat_boolean = match_lat_boolean
        self.match_lon_boolean = match_lon_boolean
        self.match_depth_boolean = match_depth_boolean

        # Extract limited scope
        self.main_df = main_df.loc[main_time_boolean & main_lat_boolean & main_lon_boolean & main_depth_boolean].copy()
        self.match_df = match_df.loc[match_time_boolean & match_lat_boolean & match_lon_boolean & match_depth_boolean].copy()

        self.main_df.sort_values(['time', 'depth'], inplace=True)
        self.match_df.sort_values(['time', 'depth'], inplace=True)
        # self.main_df.columns = [item + '_main' for item in self.main_df.columns]
        # self.match_df.columns = [item + '_match' for item in self.match_df.columns]


    def _find_match(self, **kwargs):
        """
        Look for match for all rows in seld.match_df
        :return:
        """
        main_lat_array = self.main_df['lat'].astype(float)
        main_lon_array = self.main_df['lon'].astype(float)
        main_depth_array = self.main_df['depth'].astype(float)


        print('Finding match...')
        self.matching_main_id_set = set()       # All matches in main frame
        self.matching_match_id_list = []        # All matches in match frame
        self.matching_main_id_for_match_id = {}
        for time, lat, lon, depth, id in zip(self.match_df['time'],
                                             self.match_df['lat'].astype(float),
                                             self.match_df['lon'].astype(float),
                                             self.match_df['depth'].astype(float),
                                             self.match_df['visit_depth_id']):

            # Time
            time_boolean = (self.main_df['time'] >= (time-self.tolerance_time)) & (
                    self.main_df['time'] <= (time+self.tolerance_time))

            # Distance
            # lat_array = np.array([float(item) if item else np.nan for item in self.main_df['lat']])
            # lon_array = np.array([float(item) if item else np.nan for item in self.main_df['lon']])

            dist_array = latlon_distance_array(lat, lon, main_lat_array, main_lon_array)
            dist_boolean = (dist_array <= self.tolerance_dist)

            # Depth
            depth_boolean = (main_depth_array >= (depth - self.tolerance_depth)) & (
                    main_depth_array <= (depth + self.tolerance_depth))


            m_df = self.main_df.loc[time_boolean & dist_boolean & depth_boolean]
            if len(m_df):
                self.matching_match_id_list.append(id)
                self.matching_main_id_set.update(m_df['visit_depth_id'].values)
                self.matching_main_id_for_match_id[id] = m_df['visit_depth_id'].values

    def _find_merge(self, **kwargs):
        """
        Saves merge between the two datasetsfirst:
        Merge filters on tolerance in time, pos and depth then looks and links the closest match in time.
        Matches both from main and match point of view.

        :return:
        """

        # Use the result from self._find_match to only include data that is in the valid tolerance.
        match_df = self.match_df.loc[self.match_df['visit_depth_id'].isin(self.matching_match_id_list), :].copy(deep=True)

        self.suffix_main = '_{}'.format(self.main_object.file_id)
        self.suffix_match = '_{}'.format(self.match_object.file_id)

        self.main_df['time{}'.format(self.suffix_main)] = self.main_df['time']
        match_df['time{}'.format(self.suffix_match)] = match_df['time']

        # Merge on time and saves the matching dataframes
        self.merge_df_main = pd.merge_asof(self.main_df,
                                           match_df,
                                           on='time',
                                           tolerance=self.tolerance_time,
                                           suffixes=[self.suffix_main, self.suffix_match],
                                           direction='nearest')

        self.merge_df_match = pd.merge_asof(match_df,
                                            self.main_df,
                                            on='time',
                                            tolerance=self.tolerance_time,
                                            suffixes=[self.suffix_match, self.suffix_main],
                                            direction='nearest')

        # Filter dataframes
        self.merge_df_main = self.merge_df_main.loc[~self.merge_df_main['time{}'.format(self.suffix_match)].isnull()]
        self.merge_df_match = self.merge_df_match.loc[~self.merge_df_match['time{}'.format(self.suffix_main)].isnull()]

    def get_merge_parameter(self, parameter_file_id):
        if not len(self.merge_df_main):
            raise GISMOExceptionNoMatchDataMade

        if parameter_file_id in self.merge_df_main.columns:
            return parameter_file_id

        par = parameter_file_id.replace(self.suffix_main, '').replace(self.suffix_match, '')
        print(par)

        # Check main parameter name
        par = self.main_object.get_external_parameter_name(par)
        if par in self.merge_df_main.columns:
            return par

        # Check match parameter name
        par = self.match_object.get_external_parameter_name(par)
        if par in self.merge_df_main.columns:
            return par

        raise GISMOExceptionInvalidInputArgument


    def get_match_data(self, *args, **kwargs):
        filter_options = kwargs.get('filter_options', {})
        filter_options['visit_depth_id'] = self.matching_match_id_list
        kwargs['filter_options'] = filter_options
        print('kwargs', kwargs)
        return self.match_object.get_data(*args, **kwargs)

    def get_merge_data(self, *args, **kwargs):
        if kwargs.get('inverted'):
            return self.merge_df_match
        else:
            return self.merge_df_main

    def get_main_id_for_match_id(self, match_id):
        return self.matching_main_id_for_match_id.get(match_id)


# ==============================================================================
def latlon_distance_array(lat_point, lon_point, lat_array, lon_array):
    '''
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    '''

    # convert decimal degrees to radians
    lat_point = np.radians(lat_point)
    lon_point = np.radians(lon_point)
    lat_array = np.radians(lat_array)
    lon_array = np.radians(lon_array)

    # haversine formula
    dlat = lat_array - lat_point
    dlon = lon_array - lon_point
    a = np.sin(dlat / 2.) ** 2 + np.cos(lat_point) * np.cos(lat_array) * np.sin(dlon / 2.) ** 2

    c = 2 * np.arcsin(np.sqrt(a))
    # km = 6367 * c
    km = 6363 * c  # Earth radius at around 57 degrees North
    return km



    
    
    
    
    
    
    
    
    
    