import time

from sharkpylib.seabird.modify import Modify
from sharkpylib.seabird.modify import InvalidFileToModify


class Header:
    
    @staticmethod
    def old_insert_row_after(rows, row, after_str, ignore_if_string=None):
        for line in rows:
            if row == line:
                return
        for i, value in enumerate(rows[:]):
            if after_str in value:
                if ignore_if_string and ignore_if_string in rows[i+1]:
                    continue
                rows.insert(i+1, row.strip())
                break

    @staticmethod
    def insert_row_after(lines, row, after_str):
        for line in lines:
            if row == line:
                return
        for i, value in enumerate(lines[:]):
            if after_str in value:
                lines.insert(i + 1, row.strip())
                break

    @staticmethod
    def append_to_row(lines, string_in_row, append_string):
        for i, value in enumerate(lines[:]):
            if string_in_row in value:
                if value.endswith(append_string):
                    continue
                new_string = lines[i] + append_string.rstrip()
                # if self._rows[i] == new_string:
                #     continue
                lines[i] = new_string
                break
    
    @staticmethod
    def get_row_index_for_matching_string(lines, match_string, as_list=False):
        index = []
        for i, value in enumerate(lines):
            if match_string in value:
                index.append(i)
        if not index:
            return None
        if as_list:
            return index
        if len(index) == 1:
            return index[0]
        return index

    @staticmethod
    def replace_string_at_index(lines, index, from_string, to_string, ignore_if_present=True):
        if index is None:
            return
        if type(index) == int:
            index = [index]
        for i in index:
            if to_string in lines[i] and ignore_if_present:
                continue
            lines[i] = lines[i].replace(from_string, to_string)

    @staticmethod
    def replace_row(lines, index, new_value):
        lines[index] = new_value.strip()


class ModifyCnv(Modify):

    missing_value = -9.990e-29
    missing_value_str = '-9.990e-29'
    g = 9.818  # g vid 60 gr nord (dblg)

    def _validate(self):
        if not (self._file('suffix') == '.cnv' and self._file('prefix') == 'd'):
            raise InvalidFileToModify

    def _modify(self):
        # self._check_index()
        self._header_lines = self._file.header_lines[:]
        # self._data_lines = self._file.data_lines[:]

        self._modify_header_information()
        self._modify_irradiance()
        self._modify_fluorescence()
        self._modify_depth()
        
        self._set_lines()

    def _set_lines(self):
        all_lines = []
        all_lines.extend(self._header_lines)
        all_lines.extend(self._file.data_lines[:])
        all_lines.append('')
        
        self._file.lines = all_lines

    def _modify_header_information(self):
        svMean = self._get_mean_sound_velocity()
        now = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        after_str = '** Ship'
        rows_to_insert = [f'** Average sound velocity: {str("%6.2f" % svMean)} m/s',
                          f'** True-depth calculation {now}',
                          # f'** CTD Python Module SMHI /ver 3-12/ feb 2012',
                          # f'** Python Module: ctd_processing, nov 2020'
                          # f'** LIMS Job: {self.year}{self.ctry}{self.ship}-{self.serie}'
        ]
        for row in rows_to_insert:
            if 'True-depth calculation' in row:
                if self._file.string_match_header_form('True-depth calculation'):
                    continue
                Header.insert_row_after(self._header_lines, row, after_str)
            else:
                Header.insert_row_after(self._header_lines, row, after_str)
            after_str = row

    def _modify_irradiance(self):
        Header.append_to_row(self._header_lines, 'par: PAR/Irradiance', ' [µE/(cm^2*s)]')

    def _modify_fluorescence(self):
        # Lägger till Chl-a på de fluorometrar som har beteckning som börjar på FLNTURT
        par_name_1 = self._get_parameter_name_matching_string('Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]')
        fluo_index_1 = Header.get_row_index_for_matching_string(self._header_lines, 'Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]')
        fluo_xml_index_1 = Header.get_row_index_for_matching_string(self._header_lines, 'Fluorometer, WET Labs ECO-AFL/FL -->')
        serial_index_1 = Header.get_row_index_for_matching_string(self._header_lines, '<SerialNumber>FLNTURT', as_list=True)

        par_name_2 = self._get_parameter_name_matching_string('Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]')
        fluo_index_2 = Header.get_row_index_for_matching_string(self._header_lines, 'Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]')
        fluo_xml_index_2 = Header.get_row_index_for_matching_string(self._header_lines, 'Fluorometer, WET Labs ECO-AFL/FL, 2 -->')
        serial_index_2 = Header.get_row_index_for_matching_string(self._header_lines, '<SerialNumber>FLPCRTD', as_list=True)

        if fluo_xml_index_1 and (fluo_xml_index_1 + 2) in serial_index_1:
            Header.replace_string_at_index(self._header_lines, fluo_xml_index_1, 'Fluorometer', 'Chl-a Fluorometer')
            Header.replace_string_at_index(self._header_lines, fluo_index_1, 'Fluorescence', 'Chl-a Fluorescence')
            new_par_name_1 = par_name_1.replace('Fluorescence', 'Chl-a Fluorescence')
            self._change_parameter_name(par_name_1, new_par_name_1)

        if fluo_xml_index_2 and (fluo_xml_index_2 + 2) in serial_index_2:
            if not par_name_2:
                raise Exception('Fluorometer parameter finns i xml-delen men inte i parameterlistan. Kan vara missmatch mellan DataCnv och xmlcon. ')
            Header.replace_string_at_index(self._header_lines, fluo_xml_index_2, 'Fluorometer', 'Phycocyanin Fluorometer')
            Header.replace_string_at_index(self._header_lines, fluo_index_2, 'Fluorescence', 'Phycocyanin Fluorescence')
            new_par_name_2 = par_name_2.replace('Fluorescence', 'Phycocyanin Fluorescence')
            self._change_parameter_name(par_name_2, new_par_name_2)
            
    def _modify_depth(self):
        index = Header.get_row_index_for_matching_string(self._header_lines, 'depFM: Depth [fresh water, m]')
        Header.replace_string_at_index(self._header_lines, index, 'fresh water', 'true depth')
        par_name = self._get_parameter_name_matching_string('depFM: Depth [fresh water, m]')
        if par_name:
            new_par_name = par_name.replace('fresh water', 'true depth')
            self._change_parameter_name(par_name, new_par_name)

        span_depth_index = Header.get_row_index_for_matching_string(self._header_lines, f'# span {self._file.col_depth}')
        true_depth_values = self._get_calculated_true_depth()
        if int(self._file.col_depth) < 10:
            new_line = '# span %s =%11.3f,%11.3f%7s' % (self._file.col_depth, min(true_depth_values), max(true_depth_values), '')
        else:
            new_line = '# span %s =%11.3f,%11.3f%6s' % (self._file.col_depth, min(true_depth_values), max(true_depth_values), '')
        Header.replace_row(self._header_lines, span_depth_index, new_line)

        # Ersätt data i fresh water kolumnen med true depth avrundar true depth till tre decimaler
        new_depth_data = []
        for value in true_depth_values:
            if value == self.missing_value:
                new_depth_data.append(self.missing_value_str)
                # new_depth_data.append(self.missing_value)
            else:
                new_depth_data.append(round(value, 3))
        self._file.parameters[self._file.col_depth].data = new_depth_data

    def _get_mean_sound_velocity(self):
        svCM_data = self._file.sound_velocity_data
        return sum(svCM_data) / len(svCM_data)

    def _get_parameter_name_matching_string(self, match_string):
        for par in self._file.parameters.values():
            if match_string in par.name:
                return par.name
            
    def _change_parameter_name(self, current_name, new_name):
        for par in self._file.parameters.values():
            if par.name == new_name:
                return
        for par in self._file.parameters.values():
            if current_name == par.name:
                par.change_name(new_name)
                
    def _get_calculated_true_depth(self):
        prdM_data = self._file.pressure_data
        sigT_data = self._file.density_data
        print(prdM_data[:10])
        print(sigT_data[:10])

        # Beräkning av truedepth # Ersätt depFM med true depth i headern
        # Start params
        dens_0 = (sigT_data[0] + 1000.) / 1000.  # ' start densitet
        p_0 = 0
        depth = 0
        true_depth = []
        for q in range(len(prdM_data)):
            if sigT_data[q] != self.missing_value:
                # decibar till bar (dblRPres)
                rpres = prdM_data[q] * 10.
                # Beräknar densitet (dblDens)
                dens = (sigT_data[q] + 1000.) / 1000.
                # Beräknar delta djup (dblDDjup)
                ddepth = (rpres - p_0) / ((dens + dens_0) / 2. * self.g)
                # Summerar alla djup och använd framräknande trycket i nästa loop
                # Om det är första (ej helt relevant kanske) eller sista värdet dela med två enl. trappetsmetoden
                dens_0 = dens
                #    if q == 0 or q == (len(prdM)-1):
                #        Depth = Depth + DDepth / 2.
                #    else:
                #        Depth = Depth + DDepth
                # Ändrad av Örjan 2015-02-10 /2. första och sista djupet borttaget.
                depth = depth + ddepth
                # Spara framräknat djup för nästa loop
                p_0 = rpres
                # Sparar undan TrueDepth
                true_depth.append(depth)
            else:
                true_depth.append(self.missing_value)
        return true_depth


    # def _check_index(self):
    #     if not self.cnv_info_object:
    #         raise exceptions.MissingAttribute('cnv_info_object')
    #     for info, cnv in zip(self.cnv_info_object.values(), self.parameters.values()):
    #         if 'depFM: Depth [true depth, m], lat' in info.name:
    #             continue
    #         if info.name not in cnv.name:
    #             print(info.name)
    #             print(cnv.name)
    #             raise exceptions.InvalidParameterIndex(f'Index stämmer inte i cnv för parameter: {info.name}')
    #         cnv.active = True

    # def _set_active_parameters(self):
    #     for i, info in self.cnv_info_object.items():
    #         if i not in self.parameters:
    #             raise Exception(f'''Sensoruppsättningen stämmer inte!
    #                                Kontrollera sensoruppsättningen i fil:
    #                                ctd_processing/ctd_processing/ctd_files/seabird/cnv_column_info/{info.file}''')
    #         if info.name not in self.parameters[i].name:
    #             if 'Depth' not in info.name:
    #                 raise Exception(f'''Sensoruppsättningen stämmer inte!
    #                                 Det är kan vara för få eller får många sensorer beskrivna i fil:
    #                                 "ctd_processing/ctd_processing/ctd_files/seabird/cnv_column_info/{info.file}"
    #
    #                                 Index:             {i}
    #                                 Sensoruppsättning: {info.name}
    #                                 Info i fil:        {self.parameters[i].name}''')
    #         self.parameters[i].set_active(info.active)

