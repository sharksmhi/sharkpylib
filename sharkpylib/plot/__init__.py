from sharkpylib.plot.seabird_like_plot import ProfilePlot4
from . import config
from pathlib import Path


def create_seabird_like_plots_for_package(pack, directory, suffix='png', **kwargs):
    img_paths = []
    config_files_obj = config.ConfigFiles()
    for conf_file in config_files_obj.iter_config_files_for_position(pack.lat, pack.lon):
        file_path = Path(directory, f'{pack.key}_{pack("station")}_{conf_file.name}.{suffix.strip(".")}')
        plot = ProfilePlot4(pack)
        plot.plot_from_config(conf_file.get_config(**kwargs))
        path = plot.save(file_path)
        img_paths.append(path)
    return img_paths


def get_parameter_config_for_pack(pack):
    parameter_config = {}
    config_files_obj = config.ConfigFiles()
    for conf_file in config_files_obj.iter_config_files_for_position(pack.lat, pack.lon):
        for par in conf_file.config['pars']:
            parameter_config[par['key']] = par
    return parameter_config

    # for file in config.get_config_list():
    #     if not file.startswith('seabird'):
    #         continue
    #     plot_tag = file.split('_', 1)[-1]
    #     file_path = Path(directory, f'{pack.key}_{pack("station")}_{plot_tag}.{suffix.strip(".")}')
    #     conf = config.load_file(file)
    #     plot = ProfilePlot4(pack)
    #     plot.plot_from_config(conf)
    #     plot.save(file_path)