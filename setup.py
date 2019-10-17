from setuptools import setup, find_packages
import os

from sharkpylib import __version__

include_files = []
for root, dirs, files in os.walk('.', topdown=False):
    for name in files:
        if name.endswith('.txt'):
            file_path = os.path.join(root, name).strip('.\\')
            include_files.append(file_path)
            # print(file_path)

setup(name='sharkpylib',
    version=__version__,
    description='Python 3 library',
    url='www.smhi.se',
    author='SHARK SMHI',
    author_email='shark@smhi.se',
    license='MIT',
    include_package_data=False,  # False fo include sub packages
    packages=find_packages(),
    package_data={'sharkpylib': include_files},
    zip_safe=False)


# [os.path.join('gismo', 'qc', 'data', '*.txt')]