from setuptools import setup

from sharkpylib import __version__

requirements = []
with open('requirements.txt') as fid:
    for line in fid:
        if not line.startswith('#'):
            requirements.append(line.strip())
print(requirements)

setup(name='sharkpylib',
    version=__version__,
    description='Python 3 library',
    url='www.smhi.se',
    author='SHARK SMHI',
    author_email='shark@smhi.se',
    license='MIT',
    packages=['sharkpylib'],
    install_requires=requirements,
    setup_requires=requirements,
    zip_safe=False)