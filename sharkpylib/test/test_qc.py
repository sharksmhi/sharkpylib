import unittest
import yaml
from pathlib import Path
import os
import pandas as pd
import numpy as np

import sharkpylib.qc.functions.continuous
from sharkpylib.qc import functions
from sharkpylib.qc.mask_areas import MaskAreasDirectory


class TestQC(unittest.TestCase):
    root_directory = Path(__file__).parent.parent
    qc_routines_directory = Path(root_directory, 'qc', 'etc', 'qc_routines')

    @classmethod
    def setUpClass(cls):
        print(f'Root directory is {cls.root_directory}')

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_qc_routines_yaml_files(self):
        qc_index_list = []
        for file_name in os.listdir(self.qc_routines_directory):
            if not file_name.endswith('.yaml'):
                continue
            body = os.path.splitext(file_name)[0]
            file_path = Path(self.qc_routines_directory, file_name)
            with open(file_path, encoding='utf8') as fid:
                data = yaml.load(fid)
                qc_index = data.get('functions').get(body).get('qc_index')
                qc_index_list.append(qc_index)

        self.assertEqual(sorted(qc_index_list), sorted(set(qc_index_list)))

    def test_function_continuous(self):
        test_4 = [0, 1, 0.9, 2, 3]
        df = pd.DataFrame({
            'test_1': [3, 4, 6, 87, 3],
            'test_2': list(range(5)),
            'test_3': list(range(5))[::-1],
            'test_4': test_4})
        increasing = functions.continuous.Increasing(df, parameter='test_4', acceptable_error=0.01)
        increasing()
        decreasing = functions.continuous.Decreasing(df, parameter='test_3', acceptable_error=0.01)
        decreasing()
        self.assertFalse(increasing.qc_passed)
        self.assertTrue(decreasing.qc_passed)

    def test_function_diff(self):
        df = pd.DataFrame({'a': [1, 2, 3, 7.2, 5, 6],
                           'b': [2, 3, 4, 5, 6, 7],
                           'c': [4., 5., 6., 7., 8., 9.]})

        diff = functions.diff.DataDiff(df, parameters=['a', 'b'], acceptable_error=2.2)
        diff()
        self.assertTrue(diff.qc_passed)

    def test_mask_areas(self):
        mask_dir = MaskAreasDirectory()
        mask_obj = mask_dir.get_file_object('mask_areas_tavastland.txt')

        lat_list = [63.41, 66.31, 63.36, 63.11, 63.61, 65.31]
        lon_list = [19.1, 19.2, 19.14, 19.3, 18.14, 19.9]
        b = mask_obj.get_masked_boolean(lat_list, lon_list)

        expected_boolean = [False, False, True, False, False, False]
        self.assertEqual(list(b), expected_boolean)


if __name__ == '__main__':
    unittest.main()