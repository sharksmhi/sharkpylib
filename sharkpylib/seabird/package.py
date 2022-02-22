

class Package:
    """
    Class to hold several seabird files with the same filename structure.
    """
    RAW_FILES_EXTENSIONS = ['.bl', '.btl', '.hdr', '.hex', '.ros', '.xmlcon', '.con']

    def __init__(self):
        self._files = []
        self._config_file_suffix = None

    def __str__(self):
        if not self._files:
            return 'Empty Seabird Package'
        string = f'Seabird Package: {self.pattern}'
        for file_obj in sorted([str(f) for f in self._files]):
            string = string + '\n    ' + str(file_obj)
        return string

    # def __call__(self, key):
    #     for file_obj in self._files:
    #         if file_obj(key):
    #             return file_obj(key)

    def __call__(self, key):
        return self.attributes.get(key)

    def __getitem__(self, item):
        return self.path(item)

    def path(self, item):
        for f in self._files:
            if f.suffix[1:] == item or f.suffix == item:
                return f.path

    @property
    def pattern(self):
        if not self._files:
            return False
        return self._files[0].pattern.upper()

    @property
    def files(self):
        return self._files

    # @property
    # def config_file_suffix(self):
    #     return self._config_file_suffix

    @property
    def attributes(self):
        attributes = dict()
        attributes['config_file_suffix'] = self._config_file_suffix
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

    def add_file(self, file_obj, replace=False):
        if file_obj in self._files:
            return False
        elif self._files and file_obj.pattern != self._files[0].pattern:
            return False

        if replace:
            for file in self._files:
                if file_obj.get_proper_name() == file.get_proper_name():
                    self._files.pop(self._files.index(file))

        self._files.append(file_obj)
        self._set_config_suffix(file_obj)
        self.set_key()

        # if not self._files:
        #     self._files.append(file_obj)
        #     return True
        # elif file_obj.pattern == self._files[0].pattern:
        #     self._files.append(file_obj)
        #     return True
        # return False

    def _set_config_suffix(self, file_obj):
        if 'con' in file_obj.suffix:
            self._config_file_suffix = file_obj.suffix

    def set_key(self):
        for file in self.files:
            file.key = self.key

    def get_files(self, **kwargs):
        matching_files = []
        for file in self._files:
            if all([file(key) == value for key, value in kwargs.items()]):
                matching_files.append(file)
        return matching_files

    def get_file(self, **kwargs):
        matching_files = self.get_files(**kwargs)
        if not matching_files:
            raise Exception(f'No matching files for keyword arguments {kwargs}')
        if len(matching_files) > 1:
            raise Exception(f'To many matching files for keyword arguments {kwargs}')
        return matching_files[0]

    def get_file_path(self, **kwargs):
        file = self.get_file(**kwargs)
        return file.path

    def get_raw_files(self):
        return [file for file in self._files if file.suffix in self.RAW_FILES_EXTENSIONS]

    def get_plot_files(self):
        return [file for file in self._files if file.suffix == '.jpg']





