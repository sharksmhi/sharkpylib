import re
from pathlib import Path
from abc import ABC, abstractmethod

from sharkpylib.seabird.patterns import get_file_stem_match
from sharkpylib.seabird import mapping


class SeabirdFile(ABC):
    path = None
    suffix = None
    _path_info = {}
    _attributes = {}

    def __init__(self, path):
        self.path = Path(path)
        self._path_info = {}
        self._attributes = {}
        self._load_file()
        self._fixup()
        self._save_info_from_file()
        self._save_attributes()

        self._attributes.update(self._path_info)

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return self.__str__()

    def __call__(self, key):
        return self._attributes.get(key, None)

    @property
    def stem(self):
        return self.path.stem

    @property
    def pattern(self):
        pat = self.name_match.string
        if self._path_info.get('prefix'):
            pat = pat.lstrip(self._path_info.get('prefix'))
        if self._path_info.get('tail'):
            pat = pat.rstrip(self._path_info.get('tail'))
        return pat.upper()

    @property
    def attributes(self):
        return self._attributes

    def _load_file(self):
        if self.path.suffix.lower() != self.suffix.lower():
            raise UnrecognizedFile(f'{self.path} does not have suffix {self.suffix}')

        name_match = get_file_stem_match(self.path.stem)
        if not name_match:
            raise UnrecognizedFile(f'File {self.path} does not math any registered file patterns')
        self.name_match = name_match
        self._path_info.update(name_match.groupdict())

    def _fixup(self):
        self._path_info['year'] = mapping.get_year_mapping(self._path_info.get('year'))
        self._path_info['ship'] = mapping.get_ship_mapping(self._path_info['ship'])


class UnrecognizedFile(Exception):
    pass
