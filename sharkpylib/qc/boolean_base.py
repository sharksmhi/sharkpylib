# -*- coding: utf-8 -*-
"""
Created on 2019-08-30 15:05

@author: a002028

"""
import numpy as np


class BooleanBaseDataFrame:
    """
    """
    def __init__(self):
        super().__init__()
        self.data = None
        self._boolean = True
        self._boolean_combo = {}

    def add_boolean_from_list(self, parameter, value_list):
        """
        :param parameter:
        :param value_list:
        :return: Adds boolean to self.boolean. See property: self.boolean
        """
        self.boolean = self.data[parameter].isin(value_list)

    def add_boolean_month(self, month):
        """
        :param month:
        :return:
        """
        self.boolean = self.data['timestamp'].dt.month == month

    def add_boolean_diff(self, parameters, accepted_diff):
        """
        :param parameters: list of two parameters
        :param accepted_diff: int or float
        :return: True where diff <= accepted_diff. False indicates discrepancies between the two parameters
        """
        # We need 2, and only 2 parameters
        assert len(parameters) == 2

        # Get the absolute difference between parameter_1 and parameter_2
        diff = self.data[parameters].astype(float).diff(axis=1).abs()

        # Check how parameter_2 compares to parameter_1 and add this to self.boolean
        # (True indicates difference acceptance)
        self.boolean = diff[parameters[-1]] <= accepted_diff

    def add_boolean_equal(self, param, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param] == value

    def add_boolean_less_or_equal(self, param, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param] <= value

    def add_boolean_greater_or_equal(self, param, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param] >= value

    def add_boolean_not_equal(self, param, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.data[param] != value

    def add_boolean_not_nan(self, param):
        """
        :param param:
        :return:
        """
        self.boolean = self.data[param].notna()

    def reset_boolean(self):
        """
        :return:
        """
        self._boolean = True

    def reset_boolean_combo(self):
        """
        :return:
        """
        self._boolean_combo = {}

    def add_combo_boolean(self, key, boolean, only_true_values=False):
        """
        :param key:
        :param boolean:
        :param only_true_values:
        :return:
        """
        self._boolean_combo[key] = boolean
        if only_true_values:
            boolean_true = self.boolean_not_nan(key)
            self._boolean_combo[key] = self._boolean_combo[key] & boolean_true

    def remove_combo_boolean(self, key):
        """
        :param key:
        :return:
        """
        self._boolean_combo.pop(key, None)

    def boolean_not_nan(self, param):
        """
        :param param:
        :return:
        """
        return self.data[param].notna()

    @property
    def _boolean_stack(self):
        return np.column_stack([self._boolean_combo[key] for key in self._boolean_combo.keys()])

    @property
    def combo_boolean_all(self):
        try:
            return self._boolean_stack.all(axis=1)
        except ValueError:
            return self._boolean

    @property
    def combo_boolean_any(self):
        return self._boolean_stack.any(axis=1)

    @property
    def index(self):
        return np.where(self.boolean)[0]

    @property
    def boolean(self):
        return self._boolean

    @boolean.setter
    def boolean(self, add_bool):
        """
        :param add_bool:
        :return:
        """
        self._boolean = self._boolean & add_bool


class BooleanBaseSerie:
    """
    """
    def __init__(self):
        super().__init__()
        self.serie = None
        self._boolean = True
        self._boolean_combo = {}

    def add_boolean_from_list(self, value_list):
        """
        :param parameter:
        :param value_list:
        :return: Adds boolean to self.boolean. See property: self.boolean
        """
        self.boolean = self.serie.isin(value_list)

    def add_boolean_equal(self, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.serie == value

    def add_boolean_less_or_equal(self, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.serie <= value

    def add_boolean_greater_or_equal(self, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.serie >= value

    def add_boolean_not_equal(self, value):
        """
        :param param:
        :param value:
        :return:
        """
        self.boolean = self.serie != value

    def add_boolean_less_than_other(self, other):
        """
        Compare self.serie to other index-wise. If self.serie[index] < other[index] : True else False
        :param other: other pd.Serie of the same length as self.serie
        :return:
        """
        self.boolean = self.serie.lt(other)

    def add_boolean_greater_than_other(self, other):
        """
        Compare self.serie to other index-wise. If self.serie[index] > other[index] : True else False
        :param other: other pd.Serie of the same length as self.serie
        :return:
        """
        self.boolean = self.serie.gt(other)

    def add_boolean_not_nan(self):
        """
        :param param:
        :return:
        """
        self.boolean = self.serie.notna()

    def reset_boolean(self):
        """
        :return:
        """
        self._boolean = True

    def reset_boolean_combo(self):
        """
        :return:
        """
        self._boolean_combo = {}

    def add_combo_boolean(self, key, boolean, only_true_values=False):
        """
        :param key:
        :param boolean:
        :param only_true_values:
        :return:
        """
        self._boolean_combo[key] = boolean
        if only_true_values:
            boolean_true = self._boolean_not_nan(key)
            self._boolean_combo[key] = self._boolean_combo[key] & boolean_true

    def remove_combo_boolean(self, key):
        """
        :param key:
        :return:
        """
        self._boolean_combo.pop(key, None)

    def _boolean_not_nan(self):
        """
        :param param:
        :return:
        """
        return self.serie.notna()

    @property
    def _boolean_stack(self):
        return np.column_stack([self._boolean_combo[key] for key in self._boolean_combo.keys()])

    @property
    def combo_boolean_all(self):
        try:
            return self._boolean_stack.all(axis=1)
        except ValueError:
            return self._boolean

    @property
    def combo_boolean_any(self):
        return self._boolean_stack.any(axis=1)

    @property
    def index(self):
        return np.where(self.boolean)[0]

    @property
    def boolean(self):
        return self._boolean

    @boolean.setter
    def boolean(self, add_bool):
        """
        :param add_bool:
        :return:
        """
        self._boolean = self._boolean & add_bool
