

class Package:
    """
    Class to hold several seabird files with the same filename structure.
    """
    def __init__(self):
        self._files = []

    def __str__(self):
        if not self._files:
            return 'Empty Seabird Package'
        string = f'Seabird Package: {self.pattern}'
        for file_obj in sorted([str(f) for f in self._files]):
            string = string + '\n    ' + str(file_obj)
        return string

    def __call__(self, key):
        for file_obj in self._files:
            if file_obj(key):
                return file_obj(key)

    @property
    def pattern(self):
        if not self._files:
            return False
        return self._files[0].pattern.upper()

    @property
    def files(self):
        return self._files

    @property
    def attributes(self):
        attributes = {}
        for file_obj in self._files:
            attributes.update(file_obj.attributes)
        return attributes

    @property
    def key(self):
        if not all(list(self.key_info.values())):
            return None
        return '_'.join([self('instrument'),
                         self('instrument_number'),
                         self('date'),
                         self('time'),
                         self('ship'),
                         self('cruise'),
                         self('serno')]).upper()

    @property
    def key_info(self):
        return dict(instrument=self('instrument'),
                    instrument_number=self('instrument_number'),
                    date=self('date'),
                    time=self('time'),
                    ship=self('ship'),
                    cruise=self('cruise'),
                    serno=self('serno'))

    def add_file(self, file_obj):
        if not self._files:
            self._files.append(file_obj)
            return True
        elif file_obj.pattern == self._files[0].pattern and file_obj not in self._files:
            self._files.append(file_obj)
            return True
        return False



