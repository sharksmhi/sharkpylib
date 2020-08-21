import unittest
from pathlib import Path
import os
import shutil

from sharkpylib.file.file_handlers import Directory


class TestFile(unittest.TestCase):
    data_folder = Path('test_file_data')

    @classmethod
    def setUpClass(cls):
        if cls.data_folder.exists():
            raise PermissionError
        os.mkdir(cls.data_folder)

        # Create some test files
        file_paths = [Path(cls.data_folder, 'TEST_file_1.txt'),
                      Path(cls.data_folder, 'TEST_file_1.json'),
                      Path(cls.data_folder, 'test_file_1.ini'),
                      Path(cls.data_folder, 'test_file_2.txt'),
                      Path(cls.data_folder, 'test_pic_1.jpeg'),
                      Path(cls.data_folder, 'test_file_3.txt')]

        for file_path in file_paths:
            with open(file_path, 'w') as fid:
                fid.write('test')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.data_folder)

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_directory(self):
        files_object = Directory(str(self.data_folder), prefix='TEST')
        print(files_object.get_path_list())
        print(files_object.get_file_list())

        self.assertEqual(sorted(files_object.get_file_list()),
                         sorted(['TEST_file_1.txt', 'TEST_file_1.json']))

        # file_type='', match_string='', match_format='', prefix=''):


if __name__ == '__main__':
    unittest.main()

