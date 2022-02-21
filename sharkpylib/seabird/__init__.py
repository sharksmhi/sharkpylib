from pathlib import Path
import os
import shutil

from sharkpylib.seabird.file import UnrecognizedFile

from sharkpylib.seabird.cnv_file import CnvFile
from sharkpylib.seabird.xmlcon_file import XmlconFile
from sharkpylib.seabird.hdr_file import HdrFile
from sharkpylib.seabird.bl_file import BlFile
from sharkpylib.seabird.btl_file import BtlFile
from sharkpylib.seabird.hex_file import HexFile
from sharkpylib.seabird.ros_file import RosFile

from sharkpylib.seabird.package import Package

FILES = {CnvFile.suffix: CnvFile,
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


def get_package_for_file(path):
    path = Path(path)
    all_files = Path(path.parent).glob(f'**/{path.stem}*')
    packages = get_packages_from_file_list(all_files)
    return packages[path.stem]


def get_file_names_in_directory(directory, suffix=None):
    packages = get_packages_in_directory(directory)
    paths = []
    print('packages', packages)
    for pack in packages.values():
        path = pack[suffix or 'hex']
        if not path:
            continue
        if suffix:
            paths.append(path.name)
        else:
            paths.append(path.stem)
    return paths


def update_package_with_files_in_directory(package, directory):
    all_files = Path(directory).glob('**/*')
    for path in all_files:
        obj = get_file_object_for_path(path)
        if not obj:
            continue
        package.add_file(obj)


def rename_file_object(file_object, overwrite=False):
    current_path = file_object.path
    proper_path = file_object.get_proper_path()
    if proper_path == current_path:
        return file_object
    if proper_path.exists():
        if not overwrite:
            raise FileExistsError(proper_path)
        os.remove(proper_path)
    current_path.rename(proper_path)
    return get_file_object_for_path(proper_path)


def copy_file_object(file_object, directory=None, overwrite=False):
    current_path = file_object.path
    if directory:
        target_path = Path(directory, file_object.get_proper_name())
    else:
        target_path = file_object.get_proper_path()
    if target_path == current_path:
        return file_object
    if target_path.exists():
        if not overwrite:
            raise FileExistsError(target_path)
        os.remove(target_path)
    shutil.copy2(current_path, target_path)
    return get_file_object_for_path(target_path)


def rename_package(package, overwrite=False):
    if not isinstance(package, Package):
        raise Exception('Given package is not a Package class')
    package.set_key()
    new_package = Package()
    for file in package.files:
        new_package.add_file(rename_file_object(file, overwrite=overwrite))
    return new_package


def copy_package(package, overwrite=False):
    if not isinstance(package, Package):
        raise Exception('Given package is not a Package class')
    package.set_key()
    new_package = Package()
    for file in package.files:
        new_package.add_file(copy_file_object(file, overwrite=overwrite))
    return new_package


def copy_raw_files_in_package(package, directory, overwrite=False):
    if not isinstance(package, Package):
        raise Exception('Given package is not a Package class')
    package.set_key()
    new_package = Package()
    for file in package.files:
        if file.suffix in Package.RAW_FILES_EXTENSIONS:
            new_package.add_file(copy_file_object(file, directory=directory, overwrite=overwrite))
        else:
            new_package.add_file(file)
    return new_package


def modify_cnv_down_file(package, directory=None, overwrite=False):
    from sharkpylib.seabird.modify_cnv import ModifyCnv, InvalidFileToModify
    for file in package.files:
        obj = ModifyCnv(file)
        try:
            obj.modify()
        except InvalidFileToModify:
            pass
        else:
            file.save_file(directory, overwrite=overwrite)
            return file



    # MODIFY = {'.cnv': {'prefix': 'd',
    #                    'cls': ModifyCnv}}
    # package.modify(MODIFY)
    # package.save_files(directory=directory, overwrite=overwrite)
    #
    # def modify(self, modify):
    #     for key, item in modify.items():
    #         cls = item.pop('cls')
    #         for file in self._files:
    #             if key == file.suffix:
    #                 for k, value in item.items():
    #                     if file(k) != value:
    #                         break









