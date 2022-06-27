import yaml
from pathlib import Path

CONFIG_DIR = Path(Path(__file__).parent)


def get_config_list():
    return [path.stem for path in CONFIG_DIR.iterdir()]


def load_file(name):
    if not name.endswith('.yaml'):
        name = name + '.yaml'
    path = Path(CONFIG_DIR, name)
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path, encoding='utf8') as fid:
        config = yaml.load(fid, yaml.SafeLoader)
    return config


