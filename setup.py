from setuptools import setup, find_packages

from sharkpylib import __version__

requirements = []
with open('requirements.txt') as fid:
    for line in fid:
        if not line.startswith('#'):
            module = line.strip()
            requirements.append(module)
print(requirements)

setup(name='sharkpylib',
    version=__version__,
    description='Python 3 library',
    url='www.smhi.se',
    author='SHARK SMHI',
    author_email='shark@smhi.se',
    license='MIT',
    include_package_data=True,
    # packages=['sharkpylib'],
    packages=find_packages(),
#    install_requires=requirements,
#    setup_requires=requirements,
    zip_safe=False)