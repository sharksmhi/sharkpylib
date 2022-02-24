from sharkpylib.seabird.package import Package


class PackageCollection:

    def __init__(self, name, packages=None):
        self._name = name
        self._packages = []

        if packages:
            self.add_packages(packages)

    def __call__(self, key, missing=True):
        attr_list = []
        for pack in self.packages:
            value = pack(key)
            if not value and not missing:
                continue
            attr_list.append(value)
        return attr_list

    def __getitem__(self, key):
        for pack in self.packages:
            if pack.key == key:
                return pack

    def add_package(self, package):
        if not isinstance(package, Package):
            raise Exception('This is not a package')
        self._packages.append(package)

    def add_packages(self, package_list):
        for package in package_list:
            self.add_package(package)

    @property
    def name(self):
        return self._name

    @property
    def packages(self):
        return self._packages

    @property
    def keys(self):
        return [pack.key for pack in self.packages]

    def missing(self, key):
        mis = []
        for pack in self.packages:
            if not pack(key):
                item = pack.key or pack.files[0].name
                mis.append(item)
        return mis

    @property
    def nr_files(self):
        return [(pack.key, len(pack.files)) for pack in self.packages]


