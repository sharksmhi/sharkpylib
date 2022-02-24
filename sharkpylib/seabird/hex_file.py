from sharkpylib.seabird.file import InstrumentFile


class HexFile(InstrumentFile):
    suffix = '.hex'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass