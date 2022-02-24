from pathlib import Path

from sharkpylib.seabird.file import InstrumentFile

from sharkpylib.seabird import xmlcon_parser


class XmlconFile(InstrumentFile):
    suffix = '.xmlcon'
    _tree = None
    _sensor_info = None

    def _save_info_from_file(self):
        self._tree = xmlcon_parser.get_parser_from_file(self.path)
        self._sensor_info = xmlcon_parser.get_sensor_info(self._tree)

    def _save_attributes(self):
        self._attributes['sensor_info'] = self._sensor_info
        self._attributes['instrument'] = self.instrument
        self._attributes['instrument_number'] = self.instrument_number

    @property
    def instrument_number(self):
        return xmlcon_parser.get_instrument_number(self._tree)

    @property
    def instrument(self):
        return xmlcon_parser.get_instrument(self._tree)
