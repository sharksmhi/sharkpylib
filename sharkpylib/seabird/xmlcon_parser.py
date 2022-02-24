import xml.etree.ElementTree as ET

from sharkpylib.seabird import mapping


def get_parser_from_file(path):
    return ET.parse(path)


def get_parser_from_string(string):
    return ET.ElementTree(ET.fromstring(string))


def get_sensor_info(tree):
    index = {}
    sensor_info = []
    root = tree

    if tree.find('Instrument'):
        root = tree.find('Instrument').find('SensorArray')

    sensors = root.findall('Sensor')
    if not sensors:
        sensors = root.findall('sensor')

    for i, sensor in enumerate(sensors):
        children = sensor.getchildren()
        if not children:
            continue
        child = children[0]
        par = child.tag
        nr = child.find('SerialNumber').text
        if nr is None:
            nr = ''
        index.setdefault(par, [])
        index[par].append(i)
        data = {'parameter': par,
                'serial_number': nr}
        sensor_info.append(data)

    for par, index_list in index.items():
        if len(index_list) == 1:
            continue
        for nr, i in enumerate(index_list):
            sensor_info[i]['parameter'] = f'{sensor_info[i]["parameter"]}_{nr + 1}'
    return sensor_info


def get_instrument(tree):
    return mapping.get_instrument_mapping(tree.find('Instrument').find('Name').text)


def get_instrument_number(tree):
    for sensor in tree.find('Instrument').find('SensorArray').findall('Sensor'):
        child = sensor.getchildren()[0]
        if child.tag == 'PressureSensor':
            return child.find('SerialNumber').text
