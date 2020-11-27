# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on Thu Oct 25 2018

@author: a001985
"""
import os
import codecs
import datetime

try:
    import numpy as np
    import pandas as pd
except:
    pass

try:
    from .. import geography
    from ..bodc import vocabulary
except:
    print(f'Could not import relative imports in file: {__file__}')


class SimpleODVfile:
    def __init__(self,
                 data,
                 qf_prefix='Q_',
                 **kwargs):
        """
        :param data: pandas dataframe
        """
        self.data = data
        self.qf_prefix = qf_prefix

        self.col_type = {}

        self._save_column_types()

    def _save_column_types(self):
        self.col_type = {}
        columns = list(self.data.columns)
        for col in columns:
            pot_qf_col = col.lstrip(self.qf_prefix)
            if col != pot_qf_col:
                self.col_type[col] = 'par'
                self.col_type[pot_qf_col] = 'qf'

    def _get_semantic_header_rows(self, **kwargs):
        rows = [
            '//',
            f'//<Creator>{kwargs.get("creator", "Unknown")}</Creator>'
            f'//<CreateTime>{kwargs.get("created", "Unknown")}</CreateTime>',
            f'//<Encoding>{kwargs.get("encoding", "Unknown")}</Encoding>',
            f'//<MissingValueIndicators>{kwargs.get("missing_values", "Unknown")}</MissingValueIndicators>',
            f'//<Software>{kwargs.get("software", "Unknown")}</Software>',
            f'//<Source>{kwargs.get("source", "Unknown")}</Source>',
            f'//<SourceLastModified>{kwargs.get("last_mod", "Unknown")}</SourceLastModified>',
            f'//<Version>{kwargs.get("version", "Unknown")}</Version>',

            # Data information
            f'//<DataField>{kwargs.get("data_field", "Unknown")}</DataField>',
            f'//<DataType>{kwargs.get("data_type", "Unknown")}</DataType>',
            '//'
        ]
        return rows

    def _get_header_row(self):
        header = ['Cruise',
                  'Station',
                  'Type',
                  'yyyy-mm-ddThh:mm:ss.sss',
                  'Longitude [degrees_east]',
                  'Latitude [degrees_north]',
                  'Bot. Depth [m]']
        for


    def create_odv_file(self,
                        series,
                        series_list=False,
                        Creator=None,
                        Created=None,
                        Source=None,
                        LastMod=None,
                        file_path=False,
                        Encoding='cp1252',  # 'UTF-8',
                        MissingValues='-9 -99 -999',
                        Software='Python',
                        Version='ODV Spreadsheet',
                        DataField='Ocean',
                        DataType='Profiles'):
        """
        Creates odv file.
        """

        flag_as_questionable = ['?', 'S']
        flag_as_bad = ['B']
        # Check series
        if type(series) == dict:
            if not series_list:
                series_list = sorted(series.keys())

            current_series = []
            for key in series_list:
                try:
                    current_series.append(series[key])
                except:
                    pass
        elif type(series) != list:
            current_series = [series]

        # Check file path
        if not file_path:
            return
        elif not file_path.endswith('.txt'):
            file_path = file_path + '.txt'

        # Mandatory header
        header = ['Cruise', 'Station', 'Type', 'yyyy-mm-ddThh:mm:ss.sss', \
                  'Longitude [degrees_east]', 'Latitude [degrees_north]', 'Bot. Depth [m]']

        par_list = current_series[0].data_list
        par_list.pop(par_list.index('DEPH'))
        parameter_list = ['Depth'] + par_list
        for par in parameter_list:
            header.append(par)
            header.append('QF')
        #         header.append('QV:ODV:' + par)

        # ==========================================================================
        # Open file and write "information" and header
        #         fid = codecs.open(file_path,'w', encoding='cp1252')
        fid = codecs.open(file_path, 'w', encoding=Encoding)

        # --------------------------------------------------------------------------
        # File information
        fid.write(u'//\n')
        fid.write(u'//<Creator>%s</Creator>\n' % Creator)
        fid.write(u'//<CreateTime>%s</CreateTime>\n' % Created)
        fid.write(u'//<Encoding>%s</Encoding>\n' % Encoding)
        fid.write(u'//<MissingValueIndicators>%s</MissingValueIndicators>\n' % MissingValues)
        fid.write(u'//<Software>%s</Software>\n' % Software)
        fid.write(u'//<Source>%s</Source>\n' % Source)
        fid.write(u'//<SourceLastModified>%s</SourceLastModified>\n' % LastMod)
        fid.write(u'//<Version>%s</Version>\n' % Version)

        # Data information
        fid.write(u'//<DataField>%s</DataField>\n' % DataField)
        fid.write(u'//<DataType>%s</DataType>\n' % DataType)
        fid.write(u'//\n')

        # Header
        header_str = u'\t'.join(header) + u'\n'
        fid.write(header_str)
        # --------------------------------------------------------------------------
        # Add information to ODV-file
        for series in current_series:
            for i, value in enumerate(series['DEPH']):
                # Adding meta information
                if i == 0:

                    # --------------------------------------------------------------
                    # Get position
                    lat, lon = series.get_position()

                    # --------------------------------------------------------------
                    # Writing first row of data
                    fid.write(u'%s\t' % series.shipc)  # stnr_dict[nr]['SHIPC'][row])
                    fid.write(u'%s (%s)\t' % (
                    series.statn, series.serno))  # (stnr_dict[nr]['STATN'][row], stnr_dict[nr]['STNNO'][row]))
                    fid.write(u'%s\t' % u'Type')
                    try:
                        if series.stime:
                            fid.write(series.time.strftime('%Y-%m-%dT%H:%M\t'))
                        else:
                            fid.write(series.time.strftime('%Y-%m-%dT\t'))
                    except:
                        fid.write(u'%sT\t' % series.sdate)
                    fid.write(u'%s\t' % lon)
                    fid.write(u'%s\t' % lat)
                    fid.write(u'%s\t' % series.wadep)  # stnr_dict[nr]['WADEP'][row])

                # Tab if not first row
                else:
                    fid.write(u'\t\t\t\t\t\t\t')

                # Write values
                for par in parameter_list:

                    if par == u'Depth':
                        value = series['DEPH'][i]
                        qf = u''
                    elif not series[par].qf:
                        continue
                    else:
                        value = series[par][i]
                        qf = series[par].qf[i]

                    # Write value
                    if value:
                        fid.write(u'%s\t' % value)
                    else:
                        fid.write(u'\t')

                    # Write flag
                    if not value:
                        fid.write(u'1\t')
                    elif not qf:
                        fid.write(u'0\t')
                    elif qf in flag_as_questionable:
                        fid.write(u'4\t')
                    elif qf in flag_as_bad:
                        fid.write(u'8\t')
                    else:
                        fid.write(u'1\t')

                fid.write(u'\n')
                # ------------------------------------------------------------------

        fid.close()

class CreateODVfilesBaseRow(object):

    def __init__(self, df, output_directory=None, primary_variabel=None, **kwargs):
        self.df = df
        self.output_directory = output_directory
        self.primary_variabel = primary_variabel
        self.kwargs = kwargs

        self.p01_set = set()
        self.p02_set = set()
        self.station_id_set = set()

        self.p06_mapping = {'µg/kg': 'UUKG'}
        self.basis_mapping = {'lipid': 'lw',
                              'wet weight': 'ww',
                              'dry weight': 'dw'}

        self._load_attributes()
        self._initiate_columns()
        self.add_basic_columns()
        self.add_p01_column()
        self.limit_data_scope()
        self.add_p02_column()
        self.add_p06_column()
        self.add_data_column_name()
        self.add_semantic_header_column()
        self.limit_data_scope()
        self.map_qf()

    def _initiate_columns(self):
        self.desired_columns = ['_cruise',
                                '_latit_dg',
                                '_longi_dg',
                                '_sample_id',
                                '_sdate',
                                '_cas_number',
                                '_substance',
                                '_concentration',
                                '_qf',
                                '_unit',
                                '_station_id',
                                '_edmo_author',
                                '_comment',
                                '_statn',
                                '_p01',
                                '_p02',
                                '_p06',
                                '_data_column_name',
                                '_semantic_line',
                                '_local_cdi_id',
                                '_edmo_author',
                                '_dataset_name',
                                '_dataset_id',
                                '_edmo_originator',
                                '_dataset_abs',
                                '_edmo_custodian',
                                '_platform_type',
                                '_dataset_access',
                                '_method',
                                '_instrument',
                                '_abstract']

        for col in self.desired_columns:
            if col not in self.df.columns:
                self.df[col] = ''

    def _load_attributes(self):
        """ Chould be overwritten """
        self.qf_mapping = {}

    def add_basic_columns(self):
        self._add_basic_columns()
        print('Done adding columns!')

    def add_data_column_name(self):
        if 'data_column_name' in self.df.columns:
            print('data_column_name already in dataframe!')
            return
        self._add_data_column_name()
        print('Done adding data column name!')

    def add_p01_column(self):
        # if '_p01' in self.df.columns:
        #     print('P01 column already in dataframe!')
        #     return
        self._add_p01_column()

        self.p01_set = set(self.df['_p01'])
        # Strip self.df. No use for rows without P01 code
        self.df = self.df.loc[~self.df['_p01'].isnull()].copy(deep=True)
        print('Done adding P01 column!')

    def add_p02_column(self):
        # if '_p02' in self.df.columns:
        #     print('P02 column already in dataframe!')
        #     return
        self._add_p02_column()

        self.p02_set = set(self.df['_p02'])
        # Strip self.df. No use for rows without P01 code
        self.df = self.df.loc[~self.df['_p02'].isnull()].copy(deep=True)
        print('Done adding P02 column!')

    def add_p06_column(self):
        for unit in set(self.df['_unit']):
            # print('Adding P06 code for unit {}: {}'.format(unit, self.p06_mapping.get(unit)))
            boolean = self.df['_unit'] == unit
            mapped_unit = self.p06_mapping.get(unit)
            if not mapped_unit:
                raise ExceptionUnmappedValue('Unit: {}'.format(unit))
            self.df.loc[boolean, '_p06'] = mapped_unit
        print('Done adding P06 column!')

    def add_semantic_header_column(self):
        def get_semantic_header_line(series):
            string = '//<subject>SDN:LOCAL:{}</subject><object>SDN:P01::{}</object><units>SDN:P06::{}</units>'.format(
                series['_data_column_name'], series['_p01'], series['_p06'])
            return string
        self.df['_semantic_line'] = self.df.apply(get_semantic_header_line, axis=1)
        print('Done adding semantic line column!')


    def create_files(self, station_id='', odv_files=False, cdi_lines=False):
        """  """
        self.all_cdi_lines = []
        if self.primary_variabel == 'time_series':
            all_station_id_list = sorted(self.station_id_set)
            if station_id:
                if type(station_id) == 'str':
                    station_id_list = [station_id]
                else:
                    station_id_list = station_id
                for station_id in station_id_list:
                    if station_id not in all_station_id_list:
                        raise ExceptionNotFound('station_id: {}'.format(station_id))
            else:
                station_id_list = all_station_id_list

            for sid in station_id_list:
                sid_df = self.df.loc[self.df['_station_id']==sid]
                self.current_odv_object = CreateODVfileTimeseriesRow(sid_df, output_directory=self.output_directory)

                if odv_files:
                    self.current_odv_object.create_odv_file()
                if cdi_lines:
                    self.all_cdi_lines.extend(self.current_odv_object.get_cdi_lines())
        else:
            raise ExceptionNotImplemented('Creation of primary variable {} is not implemented.'.format(self.primary_variabel))

        self.cdi_info_file_path = os.path.join(self.output_directory, 'odv/cdi_info.txt')
        with codecs.open(self.cdi_info_file_path, 'w') as fid:
            fid.write('\t'.join(self.current_odv_object.cdi_lines_columns))
            fid.write('\n')
            fid.write('\n'.join(self.all_cdi_lines))

    def limit_data_scope(self):

        # Remove lines with insufficient data
        self.df = self.df.loc[~self.df['_latit_dg'].isnull()]

        # Fill nan as ''
        self.df.fillna('', inplace=True)

        self.station_id_set = set(self.df['_station_id'])

        try:
            self.p01_set = set(self.df['_p01'])
        except:
            pass
        try:
            self.p02_set = set(self.df['_p02'])
        except:
            pass

        print('Done limiting data scope!')

    def map_qf(self):
        self.df['_qf'] = self.df['_qf'].apply(lambda qf: self.qf_mapping.get(qf, '0'))
        print('Done mapping qf!')

    def _add_basic_columns(self):
        """ Different for different sources """
        pass

    def _add_p01_column(self):
        """ Different for different sources """
        pass

    def _add_p02_column(self):

        p01_to_p02_file_path = self.kwargs.get('p02_mapping_file_path')
        # First check if file exists and has information. Additional P01 are added if not in file.
        p01_to_p02 = {}
        if p01_to_p02_file_path and os.path.exists(p01_to_p02_file_path):
            nr_p01_codes = 0
            with codecs.open(p01_to_p02_file_path) as fid:
                for line in fid:
                    line = line.strip()
                    if not line:
                        continue
                    split_line = line.split('\t')
                    p01_to_p02[split_line[0]] = split_line[1]
                    nr_p01_codes += 1
            print('{} P01 codes in mapping file'.format(nr_p01_codes))
        else:
            print('No valid p02 mapping file provided. Will search P02 for every P01 code in dataframe.')

        # Add P02 code if not in list
        nr_added_p01_codes = 0
        for p01 in self.p01_set:
            if not p01:
                continue
            if not p01_to_p02.get(p01):
                print('Searching P02 for P01 code: {}'.format(p01))
                info = vocabulary.get_vocab_code_info(p01, from_vocab='P01', to_vocab='P02', show_progress=True)
                p01_to_p02[p01] = info['P02']
                nr_added_p01_codes += 1
        print('{} P01 codes added to mapping file'.format(nr_added_p01_codes))

        for p01 in self.p01_set:
            boolean = self.df['_p01'] == p01
            self.df.loc[boolean, '_p02'] = p01_to_p02.get(p01, '')

        # Save mapping file
        if p01_to_p02_file_path:
            with codecs.open(p01_to_p02_file_path, 'w') as fid:
                for p01 in sorted(p01_to_p02):
                    fid.write('{}\t{}\n'.format(p01, p01_to_p02[p01]))
            print('P01 => P02 Mapping file saved at: {}'.format(p01_to_p02_file_path))

    def _add_data_column_name(self):
        """ Different for different sources """
        pass

    def _add_local_cdi_id(self):
        """ Different for different sources """
        pass



class CreateODVfilesBiotaEEA(CreateODVfilesBaseRow):
    """ Class to create ODV files from Biota data from EEA database """
    def __init__(self, df, **kwargs):
        CreateODVfilesBaseRow.__init__(self, df, **kwargs)

    def _load_attributes(self):
        self.qf_mapping = {'<': 'Q',
                           '': '1'}

    def _add_basic_columns(self):

        def get_local_cdi_id(series):
            string = '{}_{}_{}'.format(series['Species'].replace(' ', '_'),
                                       series['_statn'].replace(' ', '_').replace('/', '_').replace('å', 'a').replace(
                                           'ä', 'a').replace('ö', 'o'),
                                       series['_sdate'].replace('-', ''))
            return string

        # Remove lines with unvalid time (hour and/or minute equals 0
        self.df = self.df.loc[self.df['Month'] != '0']
        self.df = self.df.loc[self.df['Day'] != '0']

        # Remove lines with no Basis
        self.df = self.df.loc[~self.df['Basis'].isnull()].copy(deep=True)

        self.df['_cruise'] = self.df['Species'].apply(lambda x: 'Contaminants in {}'.format(x))
        self.df['_latit_dg'] = self.df['LATIT'].apply(geography.decmin_to_decdeg)
        self.df['_longi_dg'] = self.df['LONGI'].apply(geography.decmin_to_decdeg)
        self.df['_sample_id'] = self.df['SampleID']
        self.df['_sdate'] = self.df['Year'] + '-' + self.df['Month'].apply(lambda x: x.zfill(2)) + '-' + self.df['Day'].apply(lambda x: x.zfill(2))
        self.df['_cas_number'] = self.df['CASNumber']
        self.df['_substance'] = self.df['Determinand_HazSubs']
        self.df['_concentration'] = self.df['Concentration']
        self.df['_qf'] = self.df['LOD_LOQ_Flag']
        self.df['_unit'] = self.df['Unit_HazSubs']
        self.df['_station_id'] = self.df['Species'] + self.df['_sdate'] + self.df['_latit_dg'].astype(str) + self.df['_longi_dg'].astype(str)
        self.df['_comment'] = ''
        self.df['_statn'] = self.df['NationalStationID']

        self.df['_edmo_author'] = '545'
        self.df['_edmo_originator'] = '545'
        self.df['_edmo_custodian'] = '730' # 730=ICES

        self.df['_local_cdi_id'] = self.df.apply(get_local_cdi_id, axis=1)

        self.df['_dataset_name'] = self.df['_local_cdi_id']
        self.df['_dataset_id'] = self.df['_local_cdi_id']
        self.df['_dataset_abs'] = 'Measurement of toxic substances in biota' # 'Not Specified'
        self.df['_platform_type'] = '0'
        self.df['_dataset_access'] = 'LS'
        self.df['_method'] = 'CDIMTH02'
        self.df['_instrument'] = '999'
        self.df['_abstract'] = self.df['Species'].apply(lambda x: 'Swedish measurements of chemicals in {}'.format(x))

    def _add_p01_column(self):
        self.df['P01_search_string'] = self.df['_cas_number'] + '%' + self.df['Basis'] + '%' + self.df['Species'] + '%' + self.df['Tissue']
        p01_mapping = {}
        if self.kwargs.get('p01_mapping_file_path'):
            p01_mapping_df = pd.read_csv(self.kwargs.get('p01_mapping_file_path'), sep='\t', encoding='cp1252')
            p01_mapping = dict(zip(p01_mapping_df['vocab_search_string'], p01_mapping_df['P01']))

        for p01_search_string in set(self.df['P01_search_string']):
            boolean = self.df['P01_search_string'] == p01_search_string
            self.df.loc[boolean, '_p01'] = p01_mapping.get(p01_search_string)

    def _add_data_column_name(self):
        def get_column_name(series):
            ba = self.basis_mapping.get(series['Basis'])
            if not ba:
                raise ExceptionUnmappedValue('Basis: {}'.format(series['Basis']))
            string = '{}_{}_{}_{}'.format(series['Species'].replace(' ', '_'), series['_substance'],
                                          ba, series['Tissue']).replace(' ', '')
            return string

        self.df['_data_column_name'] = self.df.apply(get_column_name, axis=1)



class CreateODVfileRow(object):

    def __init__(self, df, output_directory=None, **kwargs):
        self.df = df.copy(deep=True)
        self.df.reset_index(inplace=True)
        self.output_directory = output_directory

        self.cdi_lines_columns = ['LOCAL_CDI_ID',
                                  'EDMO_AUTHOR',
                                  'AREA_TYPE',
                                  'DATASET_NAME',
                                  'DATASET_ID',
                                  'DATASET_REV_DATE',
                                  'EDMO_ORIGINATOR',
                                  'DATASET_ABS',
                                  'EDMO_CUSTODIAN',
                                  'PDV_CODE',
                                  'PLATFORM_TYPE',
                                  'DATASET_ACCESS',
                                  'CRUISE_NAME',
                                  'STATION_NAME',
                                  'STATION_LATITUDE',
                                  'STATION_LONGITUDE',
                                  'STATION_DATE',
                                  'EDMO_DISTRIBUTOR',
                                  'FORMAT',
                                  'FORMAT_VERSION',
                                  'DATA_SIZE',
                                  'DIST_DATABASE_REF',
                                  'DIST_WEBSITE',
                                  'DIST_METHODE',
                                  'INSTRUMENT',
                                  'ABSTRACT']

        self.cdi_mapping = {'LOCAL_CDI_ID': '_local_cdi_id',

                            'EDMO_AUTHOR': '_edmo_author',
                            'EDMO_DISTRIBUTOR': '_edmo_author',
                            'EDMO_ORIGINATOR': '_edmo_originator',
                            'EDMO_CUSTODIAN': '_edmo_custodian',

                            'AREA_TYPE': '',
                            'DATASET_NAME': '_dataset_name',
                            'DATASET_ID': '_dataset_id',
                            'DATASET_REV_DATE': datetime.datetime.now().strftime('%Y-%m-%d'),
                            'DATASET_ABS': '_dataset_abs',
                            'PDV_CODE': '_p02',
                            'PLATFORM_TYPE': '_platform_type',
                            'DATASET_ACCESS': '_dataset_access',
                            'CRUISE_NAME': '_cruise',
                            'STATION_NAME': '_statn',
                            'STATION_LATITUDE': '_latit_dg',
                            'STATION_LONGITUDE': '_longi_dg',
                            'STATION_DATE': '_sdate',
                            'FORMAT': 'ODV',
                            'FORMAT_VERSION': '0.4',
                            'DATA_SIZE': '',
                            'DIST_DATABASE_REF': '',
                            'DIST_WEBSITE': 'http://www.sdn-taskmanager.org/',
                            'DIST_METHODE': '_method',
                            'INSTRUMENT': '_instrument',
                            'ABSTRACT': '_abstract'}

        self._load_attributes()

    def _load_attributes(self):
        """ Depends on datatype and choice of primary variable """
        self.primary_variable = {}
        self.include_columns = [{}]
        self.area_type = ''




    def create_odv_file(self):

        # List comments
        self.comment_list = sorted(set(self.df['_comment']))
        self.comment_list = ['//' + item for item in self.comment_list if item]

        # Mandatory header
        self.mandatory_header = ['Cruise',
                                 'Station',
                                 'Type',
                                 'yyyy-mm-ddThh:mm:ss.sss',
                                 'Longitude [degrees_east]',
                                 'Latitude [degrees_north]',
                                 'LOCAL_CDI_ID',
                                 'EDMO_code',
                                 'Bot. Depth [m]']


        # Loop parameters (in row format)
        self.semantic_dict = {}
        self.data_dict = {}

        self.sample_id_list = sorted(set(self.df['_sample_id']))
        # Only one sample_id (='') if not used

        for sid in self.sample_id_list:
            self.data_dict[sid] = {}
            iddf = self.df.loc[self.df['_sample_id'] == sid].copy(deep=True).reset_index()
            for index in iddf.index:
                series = iddf.iloc[index]
                self.semantic_dict[series['_data_column_name']] = series['_semantic_line']

                sample_id_line = []
                # Mandatory columns
                if index == 0:
                    self.data_dict[sid]['Cruise'] = series['_cruise']
                    self.data_dict[sid]['Station'] = series['_statn']
                    self.data_dict[sid]['Type'] = '*'
                    self.data_dict[sid]['yyyy-mm-ddThh:mm:ss.sss'] = series['_sdate']
                    self.data_dict[sid]['Longitude [degrees_east]'] = '+' + str(series['_longi_dg'])
                    self.data_dict[sid]['Latitude [degrees_north]'] = '+' + str(series['_latit_dg'])
                    self.data_dict[sid]['LOCAL_CDI_ID'] = series['_local_cdi_id']
                    self.data_dict[sid]['EDMO_code'] = series['_edmo_author']
                    self.data_dict[sid]['Bot. Depth [m]'] = ''

                    # Add primary variable
                    self.data_dict[sid][self.primary_variable['data_column_name']] = series[self.primary_variable['dataframe_column']]

                    for item in self.include_columns:
                        self.data_dict[sid][item['data_column_name']] = series[item['dataframe_column']]

                # Data
                column_name = series['_data_column_name']
                #                 print(column_name)
                self.data_dict[sid][column_name] = {}
                self.data_dict[sid][column_name]['value'] = series['_concentration']
                self.data_dict[sid][column_name]['qf'] = series['_qf']

        # Create semantic lines
        self.semantic_lines = []
        # Add primary variable
        self.semantic_lines.append(self.primary_variable['semantic_line'])
        # Add "include_columns"
        for col in self.include_columns:
            self.semantic_lines.append(col['semantic_line'])

        for col in sorted(self.semantic_dict):
            self.semantic_lines.append(self.semantic_dict[col])

        # Create data lines
        self.header = self.mandatory_header[:]
        # Add primary variable name
        self.header.append(self.primary_variable['data_column_name'])
        self.header.append('QV:SEADATANET')
        # Add "include_columns"
        for col in self.include_columns:
            self.header.append(col['data_column_name'])
            self.header.append('QV:SEADATANET')
        # Add parameters
        for col in sorted(self.semantic_dict):
            self.header.append(col)
            self.header.append('QV:SEADATANET')

        self.data_lines = []  # One row for each "sample_id"
        self.data_lines.append('\t'.join(self.header))
        for k, sid in enumerate(sorted(self.data_dict)):
            self.data_line = []
            for col in self.header:
                if col == 'QV:SEADATANET':
                    continue
                if col == self.primary_variable['data_column_name']:
                    self.data_line.append(self.data_dict[sid][col])
                    self.data_line.append('1')
                elif col in self.mandatory_header:
                    self.data_line.append(self.data_dict[sid][col])
                elif col not in self.data_dict[sid]: # All sample_id might not have all parameters
                    self.data_line.append('')  # for value
                    self.data_line.append('')  # for qf
                elif type(self.data_dict[sid][col]) == dict:
#                    print(self.data_dict[sid].keys())
                    self.data_line.append(self.data_dict[sid][col]['value'])
                    self.data_line.append(self.data_dict[sid][col]['qf'])
                else:  # From "self.include_columns"
                    self.data_line.append(self.data_dict[sid][col])
                    self.data_line.append('1')
            self.data_lines.append('\t'.join(self.data_line))

        # Combine all lines
        self.all_lines = self.comment_list + ['//', '//SDN_parameter_mapping'] + self.semantic_lines + [
            '//'] + self.data_lines

        self.text = '\n'.join(self.all_lines)

        if self.output_directory is not None:
            self.odv_output_directory = os.path.join(self.output_directory, 'odv')
            if not os.path.exists(self.odv_output_directory):
                os.makedirs(self.odv_output_directory)
            self.file_path = os.path.join(self.odv_output_directory, '{}.txt'.format(series['_local_cdi_id']))
            # print(self.file_path)
            with codecs.open(self.file_path, 'w', encoding='utf8') as fid:
                fid.write(self.text)

        return self.text

    def get_cdi_lines(self):
        p02_list = sorted(set(self.df['_p02']))
        if 'AYMD' in p02_list:
            p02_list.pop(p02_list.index('AYMD'))
        cdi_lines = []
        for p02 in p02_list:
            cdi_line = []
            for item in self.cdi_lines_columns:
                series = self.df.iloc[0]
                col = self.cdi_mapping.get(item)
                if col in series:
                    value = series[col]
                    # if item == 'PDV_CODE':
                    #     print(value)
                elif col:
                    value = col
                elif item == 'AREA_TYPE':
                    value = self.area_type
                elif item == 'DATA_SIZE':
                    statinfo = os.stat(self.file_path)
                    value = statinfo.st_size/1e6
                elif item == 'DIST_DATABASE_REF':
                    value = ''
                else:
                    value = ''
                cdi_line.append(str(value))
            cdi_lines.append('\t'.join(cdi_line))

        return cdi_lines

class CreateODVfileTimeseriesRow(CreateODVfileRow):
    def __init__(self, df, output_directory, **kwargs):
        CreateODVfileRow.__init__(self, df, output_directory, **kwargs)

    def _load_attributes(self):
        self.primary_variable = {'data_column_name': 'time_ISO8601 [yyyy-mm-dd]',
                                 'dataframe_column': '_sdate',
                                 'semantic_line': '//<subject>SDN:LOCAL:time_ISO8601</subject><object>SDN:P01::DTUT8601</object><units>SDN:P06::TISO</units>'}

        self.include_columns = [{'data_column_name': 'sample_id',
                                 'dataframe_column': '_sample_id',
                                 'semantic_line': '//<subject>SDN:LOCAL:sample_id</subject><object>SDN:P01::ACYCAA01</object><units>SDN:P06::UUUU</units>'}]

        self.area_type = 'Point'


# ==============================================================================
class CreateODVException(Exception):
    """
    Created     20180926
    Updated

    Blueprint for error message.
    code is for external mapping of exceptions. For example if a GUI wants to
    handle the error text for different languages.
    """
    code = None
    message = ''

    def __init__(self, message='', code=''):
        self.message = '{}: {}'.format(self.message, message)
        if code:
            self.code = code

class ExceptionUnmappedValue(CreateODVException):
    """  """
    code = ''
    message = ''

class ExceptionNotImplemented(CreateODVException):
    """  """
    code = ''
    message = ''

class ExceptionNotFound(CreateODVException):
    """  """
    code = ''
    message = ''


if __name__ == '__main__':
    file_path = r'C:\mw\temp_sharktools/OlandsSodraGrund_35063_1978_2004.txt'
    df = pd.read_csv(file_path, sep='\t')


