from pathlib import Path
import datetime

from sharkpylib.seabird.file import InstrumentFile
from sharkpylib.seabird.patterns import get_cruise_match_dict


class HdrFile(InstrumentFile):
    suffix = '.hdr'
    date_format = '%b %d %Y %H:%M:%S'
    _datetime = None
    _station = None
    _cruise_info = None
    _header_form = None

    def _get_datetime(self):
        return self._datetime

    def _save_info_from_file(self):
        self._cruise_info = {}
        self._header_form = {'info': []}
        with open(self.path) as fid:
            for line in fid:
                strip_line = line.strip()
                if line.startswith('* System UTC'):
                    self._datetime = datetime.datetime.strptime(line.split('=')[1].strip(), self.date_format)
                elif line.startswith('* NMEA Latitude'):
                    self._lat = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('* NMEA Longitude'):
                    self._lon = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('** Station'):
                    self._station = line.split(':')[-1].strip()
                elif line.startswith('** Cruise'):
                    self._cruise_info = get_cruise_match_dict(line.split(':')[-1].strip())
                if line.startswith('**'):
                    if line.count(':') == 1:
                        key, value = [part.strip() for part in line.strip().strip('*').split(':')]
                        self._header_form[key] = value
                    else:
                        self._header_form['info'].append(strip_line)

    def _save_attributes(self):
        self._attributes.update(self._cruise_info)
        self._attributes['lat'] = self._lat
        self._attributes['lon'] = self._lon
        self._attributes['station'] = self._station

