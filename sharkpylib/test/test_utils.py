import unittest
import socket
import os
import datetime
import json
import shutil
from pathlib import Path

import yaml


from sharkpylib import utils


class TestUtils(unittest.TestCase):
    data_folder = Path('test_utils_data')
    json_file_path = Path(data_folder, 'test_json_file.json')
    dummy_file_path = Path(data_folder, 'dummy.dum')

    @classmethod
    def setUpClass(cls):
        if cls.data_folder.exists():
            raise PermissionError
        os.mkdir(cls.data_folder)

        with open(cls.json_file_path, 'w') as fid:
            fid.write('{}')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.data_folder)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_computer_name(self):
        self.assertEqual(utils.get_computer_name(), socket.gethostname())

    def test_get_employee_name(self):
        self.assertEqual(utils.get_employee_name(), os.path.expanduser('~').split('\\')[-1])

    def test_get_time_as_format(self):
        fmt = '%Y%m%d%H%M%S'
        self.assertEqual(utils.get_time_as_format(now=True, fmt=fmt), datetime.datetime.now().strftime(fmt))

        with self.assertRaises(ValueError):
            utils.get_time_as_format()

        with self.assertRaises(ValueError):
            utils.get_time_as_format(fmt=True)

        with self.assertRaises(NotImplementedError):
            utils.get_time_as_format(now=True)

        with self.assertRaises(NotImplementedError):
            utils.get_time_as_format(timestamp=True)

    def test_save_json(self):
        with self.assertRaises(ValueError):
            utils.load_json(self.data_folder, 'dummy.dum')

    def test_load_json(self):
        with self.assertRaises(ValueError):
            utils.load_json(self.data_folder, 'dummy.dum')

        with self.assertRaises(ValueError):
            utils.load_json(self.dummy_file_path)

        with self.assertRaises(FileNotFoundError):
            utils.load_json(self.data_folder, 'test.json')

        self.assertEqual(utils.load_json(str(self.data_folder), 'test1.json', create_if_missing=True), {})
        self.assertEqual(utils.load_json(self.data_folder, 'test2.json', create_if_missing=True), {})

    def test_save_and_load_json(self):
        data = {'test1': 99,
                'test2': '99'}

        utils.save_json(data, self.json_file_path)
        loaded_data = utils.load_json(self.json_file_path)
        self.assertEqual(data, loaded_data)

    def test_sorted_int(self):
        list_to_sort = ['4', '22', '333', '111111']
        expected_result = ['4', '22', '333', '111111']
        self.assertEqual(utils.sorted_int(list_to_sort), expected_result)

    def test_recursive_dict_update(self):
        d1 = {'key1': {'key_11': 12,
                       'key_12': 'test'},
              'key2': {'key_21': 'testing'}}

        d2 = {'key1': {'key_11': 99,
                       'key_13': 88},
              'key3': {'key_31': 'testing'}}

        dr = {'key1': {'key_11': 99,
                       'key_12': 'test',
                       'key_13': 88},
              'key2': {'key_21': 'testing'},
              'key3': {'key_31': 'testing'}}

        d3 = utils.recursive_dict_update(d1, d2)

        self.assertDictEqual(d3, dr)


if __name__ == '__main__':
    unittest.main()
