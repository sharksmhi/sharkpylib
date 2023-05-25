#!/usr/bin/env python3
"""
Created on Tue Sep 11 08:05:22 2018

@author: a002028
"""
import os
import setuptools
import pathlib


root_path = pathlib.Path(__file__).parent.resolve()

requirements = []
with open(pathlib.Path(root_path, 'requirements.txt')) as fh:
    for line in fh:
        requirements.append(line.strip())

with open(pathlib.Path(root_path, 'README.md')) as fid:
    README = fid.read()


include_files = []
for root, dirs, files in os.walk(root_path, topdown=False):
    for name in files:
        path = pathlib.Path(root, name)
        if not path.suffix in ['.txt', '.json', '.yaml']:
            continue
        include_files.append(str(path))

setuptools.setup(
    name='sharkpylib',
    version='0.1.1',
    author="Magnus Wenzer",
    author_email="magnus.wenzer@smhi.se",
    description="Package containing a collection of help functions and classes used by the shark team.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/sharksmhi/sharkpylib",
    packages=setuptools.find_packages(exclude=('tests*', 'htmlcov*', 'log*')),
    package_data={'sharkpylib': include_files},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
)
