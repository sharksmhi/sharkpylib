from pathlib import Path
import datetime

from sharkpylib.seabird.file import SeabirdFile


class RosFile(SeabirdFile):
    suffix = '.ros'

    def _save_info_from_file(self):
        pass