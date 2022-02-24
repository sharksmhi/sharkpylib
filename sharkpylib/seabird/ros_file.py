from pathlib import Path
import datetime

from sharkpylib.seabird.file import InstrumentFile


class RosFile(InstrumentFile):
    suffix = '.ros'

    def _save_info_from_file(self):
        pass