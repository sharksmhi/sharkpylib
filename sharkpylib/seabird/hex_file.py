from pathlib import Path
import datetime

from sharkpylib.seabird.file import SeabirdFile


class HexFile(SeabirdFile):
    suffix = '.hex'

    def _save_info_from_file(self):
        pass