from pathlib import Path
import datetime

from sharkpylib.seabird.file import SeabirdFile


class BlFile(SeabirdFile):
    suffix = '.bl'
    _number_of_bottles = 0

    @property
    def number_of_bottles(self):
        return self._number_of_bottles

    def _save_info_from_file(self):
        self._number_of_bottles = 0
        with open(self.path) as fid:
            for nr, line in enumerate(fid):
                stripped_line = line.strip()
                if nr > 1 and stripped_line:
                    self._number_of_bottles += 1

    def _save_attributes(self):
        self._attributes['nr_bottles'] = self.number_of_bottles
