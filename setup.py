from setuptools import setup

from sharkpylib import __version__

setup(name='sharkpylib',
    version=__version__,
    description='Python 3 library',
    url='www.smhi.se',
    author='SHARK SMHI',
    author_email='shark@smhi.se',
    license='MIT',
    packages=['sharkpylib'],
    install_requires=[],
    zip_safe=False)