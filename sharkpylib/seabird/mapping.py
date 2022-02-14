
INSTRUMENT = {'SBE 911plus/917plus CTD': 'SBE09',
              'SBE 19plus V2 Seacat CTD': 'SBE19'}

SHIP = {'sv': '77SE'}


def get_instrument_mapping(string):
    return INSTRUMENT.get(string, '<unknown>')


def get_ship_mapping(string):
    return SHIP.get(string, '<unknown>')


def get_year_mapping(year):
    if len(year) == 2:
        year = '20' + year
    return year