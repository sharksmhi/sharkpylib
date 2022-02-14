from pathlib import Path

from sharkpylib.seabird.file import UnrecognizedFile

from sharkpylib.seabird.cnv_file import Cnvfile
from sharkpylib.seabird.xmlcon_file import XmlconFile
from sharkpylib.seabird.hdr_file import HdrFile
from sharkpylib.seabird.bl_file import BlFile
from sharkpylib.seabird.btl_file import BtlFile
from sharkpylib.seabird.hex_file import HexFile
from sharkpylib.seabird.ros_file import RosFile

from sharkpylib.seabird.package import Package

FILES = {Cnvfile.suffix: Cnvfile,
         XmlconFile.suffix: XmlconFile,
         HdrFile.suffix: HdrFile,
         BlFile.suffix: BlFile,
         BtlFile.suffix: BtlFile,
         HexFile.suffix: HexFile,
         RosFile.suffix: RosFile}


def get_file_object_for_path(path):
    path = Path(path)
    file_cls = FILES.get(path.suffix.lower())
    if not file_cls:
        return
    try:
        return file_cls(path)
    except UnrecognizedFile:
        return False


def get_packages_from_file_list(file_list):
    packages = {}
    for path in file_list:
        file_obj = get_file_object_for_path(path)
        if not file_obj:
            continue
        pack = packages.setdefault(file_obj.pattern, Package())
        pack.add_file(file_obj)
    return packages


def get_packages_in_directory(directory):
    all_files = Path(directory).glob('**/*')
    return get_packages_from_file_list(all_files)







