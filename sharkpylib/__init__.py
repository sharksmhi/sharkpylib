# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on Thu Aug 30 15:53:08 2018

@author: a001985
"""
import os

__version__ = '2019.10.01'
DIRECTORY_MAPPING_FILES = os.path.join(os.path.dirname(__file__), 'gismo', 'mapping_files')
DIRECTORY_SETTINGS_FILES = os.path.join(os.path.dirname(__file__), 'gismo', 'settings_files')

from . import bodc
from . import diva
from . import eea
from . import gismo
from . import ices
from . import odv
from . import file_io
from . import geography
from . import mappinglib
from . import utils
from . import loglib
from . import tklib
from . import file
from . import ferrybox
from . import sharkint



