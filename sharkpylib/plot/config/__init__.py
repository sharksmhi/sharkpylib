import yaml
from pathlib import Path
from typing import Union

CONFIG_DIR = Path(Path(__file__).parent)


class ConfigFile:

    def __init__(self, path: Union[Path, str]):
        self._path = Path(path)
        self._name = None
        self._instrument = None
        self._lat_min = None
        self._lat_max = None
        self._lon_min = None
        self._lon_max = None
        self._extract_info()

    def __repr__(self):
        return f'ConfigFile({self.stem})'

    def __str__(self):
        return self.__repr__()

    @property
    def path(self) -> str:
        return self._path

    @property
    def stem(self) -> str:
        return self._path.stem

    @property
    def name(self) -> str:
        return self._name

    @property
    def instrument(self) -> str:
        return self._instrument

    def _extract_info(self) -> None:
        self._instrument = self.stem.split('_')[0]
        self._name = self.stem.split('@')[-1]
        if self.stem.count('@') == 1:
            return
        la, lo = self.stem.split('@')[1].split('#')
        lat_min, lat_max = [float(item) for item in la.split('-')]
        lon_min, lon_max = [float(item) for item in lo.split('-')]
        self._lat_min = lat_min
        self._lat_max = lat_max
        self._lon_min = lon_min
        self._lon_max = lon_max

    def is_in_bounding_box(self, lat: float, lon: float) -> bool:
        if not self.has_bounding_box():
            return False
        if (self._lat_min <= float(lat) <= self._lat_max) and (self._lon_min <= float(lon) <= self._lon_max):
            return True
        return False

    def has_bounding_box(self):
        if self._lat_min == None:
            return False
        return True
    
    @property
    def config(self):
        return load_file(self.path)

    def get_config(self, **kwargs):
        config = self.config
        for par in config['pars']:
            data = kwargs.get(par['key'])
            if not data:
                continue
            print('data', data)
            par['xmin'] = data['xmin']
            par['xmax'] = data['xmax']
        return config


class ConfigFiles:
    def __init__(self):
        self._config_files = []
        self._default_files = {}
        self._bb_files = {}
        self._load_files()

    def _load_files(self):
        for path in CONFIG_DIR.iterdir():
            if not path.suffix == '.yaml':
                continue
            cf = ConfigFile(path)
            self._config_files.append(cf)
            if cf.has_bounding_box():
                self._bb_files.setdefault(cf.name, [])
                self._bb_files[cf.name].append(cf)
            else:
                self._default_files[cf.name] = cf

    def get_config_files_for_position(self, lat, lon):
        files = []
        for name, cf in self._default_files.items():
            bb_files = self._bb_files.get(name, [])
            if not bb_files:
                files.append(cf)
                continue
            for bb_file in bb_files:
                if bb_file.is_in_bounding_box(lat, lon):
                    files.append(bb_file)
                    break
            else:
                files.append(cf)
        return files
    
    def iter_config_files_for_position(self, lat: float, lon: float) -> ConfigFile:
        for cf in self.get_config_files_for_position(lat, lon):
            yield cf


def load_file(path):
    if not path.suffix == '.yaml':
        return
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path, encoding='utf8') as fid:
        config = yaml.load(fid, yaml.SafeLoader)
    return config




def get_config_list():
    return [path.stem for path in CONFIG_DIR.iterdir()]





def get_seabird_file_names_for_coordinate(lat, lon):
    files = []
    for path in get_config_list():
        name = path.name
        if 'seabird' not in name:
            continue
        if '@' not in name:
            continue
        la, lo = name.split('@')[1].split('#')
        lat_min, lat_max = [float(item) for item in la.split('-')]
        lon_min, lon_max = [float(item) for item in lo.split('-')]
        if lat_min <= float(lat) <= lat_max and lon_min <= float(lon) <= lon_max:
            files.append(name)
    if not files:
        files = [path.name for path in get_config_list() if 'seabird' in path.name]
    return files


if __name__ == '__main__':
    cfs = ConfigFiles()
    files = cfs.get_config_files_for_position(56, 11)
    for cf in files:
        print(cf)


