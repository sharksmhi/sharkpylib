from abc import ABC, abstractmethod


class InvalidFileToModify(Exception):
    pass


class Modify(ABC):

    def __init__(self, file):
        self._file = file

    def modify(self):
        self._validate()
        self._modify()

    @abstractmethod
    def _validate(self):
        pass

    @abstractmethod
    def _modify(self):
        pass

