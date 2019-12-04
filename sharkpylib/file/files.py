import os
import codecs

from .txt_reader import load_txt_df

try:
    import numpy as np
except ImportError:
    pass

try:
    import pandas as pd
except ImportError:
    pass


class MappingFile(object):

    def __init__(self, file_path, from_col=None, to_col=None, **kwargs):

        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        kw = {'sep': '\t',
              'encoding': 'cp1252',
              'dtype': 'str'}
        kw.update(kwargs)

        self.from_col = from_col
        self.to_col = to_col

        self.file_path = file_path
        self.df = pd.read_csv(file_path, **kw)
        self.df.replace(np.nan, '', regex=True, inplace=True)

        self.columns = self.df.columns[:]

    def get(self, item, from_col=None, to_col=None, missing_value=None, **kwargs):
        if not self.file_path:
            return item

        if not from_col:
            from_col = self.from_col
        if not to_col:
            to_col = self.to_col

        # Saving current columns
        self.from_col = from_col
        self.to_col = to_col

        result = self.df.loc[self.df[from_col] == item, to_col]
        value = ''
        if len(result):
            value = result.values[0]

        if value:
            return str(value)
        else:
            if missing_value is not None:
                return missing_value
            else:
                return str(item)

    def get_mapped_list(self, item_list, **kwargs):
        """
        Maps a iterable
        :param item_list:
        :param kwargs: Se options in method get
        :return:
        """

        output_list = []
        for k, item in enumerate(item_list):
            mapped_item = self.get(item, **kwargs)
            output_list.append(mapped_item)
        return output_list


class SynonymFile(object):
    def __init__(self, file_path=None, main_sep='\t', sub_sep=';', case_sensitive=False):
        """
        Synonym files are two column files separated by "main_sep". Second column is split by "sub_sep" and each
        item in the resulting list ar mapped as a synonym to the first column.
        :param file_path:
        :param kwargs:
        """
        self.data = {}
        self.file_path = file_path
        self.main_sep = main_sep
        self.sub_sep = sub_sep
        self.items = []
        if self.file_path:
            with codecs.open(file_path) as fid:
                for line in fid:
                    line = line.strip('\r\n')
                    if not line:
                        continue
                    split_line = line.split(self.main_sep)
                    if len(split_line) > 1:
                        items = [key.strip() for key in split_line[1].split(self.sub_sep)]
                        for key in items:
                            self.data[key] = split_line[0]
                            if not case_sensitive:
                                self.data[key.upper()] = split_line[0]
                                self.data[key.lower()] = split_line[0]
                        self.items.append(split_line[0])

    def get(self, item, no_match_value=None):
        return self.data.get(item, no_match_value)

    def get_mapped_list(self,
                 item_list,
                 no_match_value=None,
                 as_array=False):
        """
        Maps a iterable.
        :param item_list:
        :param no_match_value:
        :param col_nummer_if_no_match:
        :param kwargs:
        :return:
        """
        output_list = []
        for k, item in enumerate(item_list):
            if no_match_value == 'items':
                mapped_item = self.get(item, item)
            else:
                mapped_item = self.get(item, no_match_value)
            output_list.append(mapped_item)
        if as_array:
            output_list = np.array(output_list)

        return output_list


class ListFile(object):
    def __init__(self, file_path, **kwargs):
        self.file_path = file_path
        self.list = []
        comment = kwargs.pop('comment', None)
        with codecs.open(file_path, **kwargs) as fid:
            for line in fid:
                stripped_line = line.strip()
                if comment and stripped_line.startswith(comment):
                    continue
                if stripped_line:
                    self.list.append(stripped_line)

    def get(self, **kwargs):
        if kwargs.get('sorted'):
            return sorted(self.list)
        return self.list[:]


class MultiListFile(object):
    def __init__(self, file_path, **kwargs):

        self.file_path = file_path

        kw = {'sep': '\t',
              'encoding': 'cp1252',
              'dtype': 'str'}
        kw.update(kwargs)

        kw['separator'] = kwargs.pop('sep')

        self.df = load_txt_df(file_path, **kw)

        self.lists = self.df.columns[:]

    def get(self, columns_name, **kwargs):
        return_list = list(self.df[columns_name])
        if kwargs.get('sorted'):
            return sorted(return_list)
        return return_list


def get_list_from_file(file_path, **kwargs):
    """
    Returns a list of the content in file_path. Each row is an element in list.
    :param file_path:
    :return:
    """
    list_object = ListFile(file_path, **kwargs)
    return list_object.get()


def get_list_from_column_file(file_path, column_name, **kwargs):
    """
    Returns a list of the content in file_path in the column column name. Each row of named column is an element in list.
    :param file_path:
    :return:
    """
    multi_list_object = MultiListFile(file_path, **kwargs)
    return multi_list_object.get(column_name)

