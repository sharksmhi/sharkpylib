import shutil
from pathlib import Path
from abc import ABC, abstractmethod

from sharkpylib.seabird.patterns import get_file_stem_match
from sharkpylib.seabird import mapping


class SeabirdFile(ABC):
    path = None
    suffix = None
    _path_info = {}
    _attributes = {}
    _lines = None

    def __init__(self, path):
        self.path = Path(path)
        self._key = None
        self._path_info = {}
        self._attributes = {}
        self._load_file()
        self._fixup()
        self._save_info_from_file()
        self._save_attributes()

        self._attributes.update(self._path_info)
        self._attributes['suffix'] = self.suffix


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

    def __eq__(self, other):
        if self.name.upper() == other.name.upper():
            return True
        return False

    @property
    def lines(self):
        """
        Use in self.save_file
        """
        return self._lines

    @lines.setter
    def lines(self, lines):
        if not isinstance(lines, list):
            raise TypeError(f'Invalid type when setting lines in file: {self}')
        self._lines = lines

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def name(self):
        return self.path.name

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

    def get_proper_name(self):
        prefix = self('prefix') or ''
        tail = self('tail') or ''
        return f'{prefix + self.key + tail}{self.suffix}'

    def get_proper_path(self, directory=None):
        if not directory:
            directory = self.path.parent
        return Path(directory, self.get_proper_name())

    def get_save_name(self):
        return self.get_proper_name()

    def get_save_path(self, directory=None):
        if not directory:
            directory = self.path.parent
        return Path(directory, self.get_save_name())

    def save_file(self, directory=None, overwrite=False):
        if not self.lines:
            return
        target_path = self.get_save_path(directory)
        if target_path.exists() and not overwrite:
            raise FileExistsError(target_path)
        with open(target_path, 'w') as fid:
            fid.write('\n'.join(self.lines))


    # def save_file(self, directory, overwrite=False):
    #     path = Path(directory, f'{self.key}{self.suffix}')
    #     if path.exists() and not overwrite:
    #         raise FileExistsError(path)
    #     if not path.parent.exists():
    #         path.parent.mkdir(parents=True)
    #     shutil.copy2(self.path, path)


class UnrecognizedFile(Exception):
    pass
