from pathlib import Path
import datetime

from sharkpylib.seabird.file import SeabirdFile


class BtlFile(SeabirdFile):
    suffix = '.btl'

    def _save_info_from_file(self):
        pass