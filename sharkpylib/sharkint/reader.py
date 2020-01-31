# -*- coding: utf-8 -*-
"""
Created on 2020-01-07 13:13

@author: a002028

"""
import datetime
import pyodbc
import json
import pandas as pd


def get_pyodbc_engine(server):
    with open('//winfs-proj/proj/havgem/SHARKtools/settings_info/srv_info.json', 'r') as fd:
        settings = json.load(fd)

    if server == 'prod':
        engine = pyodbc.connect(**settings['servers'].get('sharkint_prd'))
    elif server == 'test':
        engine = pyodbc.connect(**settings['servers'].get('sharkint_tst'))
    else:
        raise UserWarning('sharkint prod/test not set', server)

    return engine


class SHARKintReader(object):
    """
    Class to extract data from SHARKint.
    """
    def __init__(self, prod_or_test, year=None, start_date=None, end_date=None):
        if start_date and end_date:
            self.start_date = start_date
            self.end_date = end_date
        else:
            if not year:
                #FIXME. use assert ?
                year = str(datetime.date.today().year)
            else:
                year = str(year)

            self.start_date = ''.join([year, '01', '01'])
            self.end_date = ''.join([year, '12', '31'])

        self.prod_or_test = prod_or_test
        if prod_or_test not in ['prod', 'test']:
            return

        self._clear_selection()

    def _clear_selection(self):
        self.select_list = []
        self.in_dict = {}
        self.between = {}
        self.more_than = {}
        self.less_than = {}
        self.equal_to = {}
        self.like = {}

        self.item_list = []

        self.where_statements = []

    def add_select(self, item):
        if type(item) == list:
            self.select_list.extend(item)
        else:
            self.select_list.append(item)

    def add_in_dict(self, item_dict):
        self.in_dict.update(item_dict)

    def add_between(self, item_dict):
        self.between.update(item_dict)

    def add_more_than(self, item_dict):
        self.more_than.update(item_dict)

    def add_less_than(self, item_dict):
        self.less_than.update(item_dict)

    def add_equal_to(self, item_dict):
        self.equal_to.update(item_dict)

    def add_like(self, item_dict):
        self.like.update(item_dict)

    def add_where_statement(self, statement):
        if not statement.strip().startswith('AND'):
            statement = 'AND ' + statement
        self.where_statements.append(statement)

    def print_sql_query(self):
        self.get_sql_query()

    def get_data_dict_from_sql_query(self):
        result = self.get_data_from_sql_query(combine_proj=True)

        if not result:
            return result

        previous_key_depth = None
        new_line_dict = {}
        data_dict = dict((key, []) for key in self.item_list)
        for line in result:
            line_dict = dict(zip(self.item_list, line))
            if line_dict['key_depth'] != previous_key_depth:
                if previous_key_depth:
                    for key, value in new_line_dict.iteritems():
                        if value != None:
                            data_dict[key].append(str(value))
                        else:
                            data_dict[key].append(u'')
                previous_key_depth = line_dict['key_depth']
                new_line_dict = dict(zip(self.item_list, line))
            else:
                new_line_dict['PROJ'] = ', '.join([new_line_dict['PROJ'], line_dict['PROJ']])

        return data_dict

    def get_data_in_dataframe(self, sql_query=None):
        """ Added by Johannes 20180807
        """
        print('Loading data from SHARKint..')
        if not sql_query:
            sql_query = self.get_default_sql_query()
        df = pd.read_sql(sql_query, self._get_engine())
        print('SHARKint-data load completed!')

        return df

    def get_default_sql_query(self):
        """
        :return:
        """
        print('Using default sql query! SHARKintReader.default_sql_query()')
        station_string = """('ANHOLT E', 'BCS III-10', 'BY1', 'BY10', 'BY15 GOTLANDSDJ', 'BY2 ARKONA', 'BY20 FÅRÖDJ', 
                             'BY32 NORRKÖPINGSDJ', 'BY38 KARLSÖDJ', 'BY4 CHRISTIANSÖ', 'BY5 BORNHOLMSDJ', 'FLADEN', 
                             'N14 FALKENBERG', 'P2', 'REF M1V1', 'SLÄGGÖ', 'W LANDSKRONA', 'Å13', 'Å15', 'Å17')"""
        test_query = """
                    Select distinct 
                    "ctryid" || "shipid" as "SHIPC",
                    stnreg.stnname AS "STATN",
                    stnvisit.sea1id || stnvisit.sea2id || stnvisit.sea3id || stnvisit.stnid as "STNCODE",
                    "year" || "month" || "day" as "SDATE", 
                    serie as "SERNO", 
                    depth as "DEPH", 
                    chla as "CHLA",
                    qchla as "Q_CHLA",
                    ctdfluo as "CTDCPHL"
                    from visit
                    join stnreg using(sea1id, sea2id, sea3id, stnid)
                    join stnvisit using (serie, "year", ctryid, shipid)
                    join depthtab using(serie, "year", ctryid, shipid)
                    join biodata using(serie, "year", ctryid, shipid, depthno )
                    join hyddata using(serie, "year", ctryid, shipid, depthno )
                    join visproj using(serie, "year", ctryid, shipid)
                    where 1=1
                    AND stnreg.stnname IN """+station_string+"""
                    AND "depth" <= 50
                    AND "year" || "month" || "day" >= '"""+self.start_date+"""'
                    AND "year" || "month" || "day" <= '"""+self.end_date+"""'
                    order by "SDATE", "SERNO", "DEPH"
                    """
        return test_query

    def execute_query(self, sql_query):
        """
        Updated 20180702     by Magnus Wenzer
        Updated 20180807     by Johannes Johansson
        """
        try:
            cnxn = self._get_engine()
            cursor = cnxn.cursor()
            cursor.execute(sql_query)
            dbdata = cursor.fetchall()
            cursor.close()
            return dbdata
        except:
            return False

    def _get_engine(self):
        """
        :return:
        """
        engine = get_pyodbc_engine(self.prod_or_test)
        return engine


if __name__ == '__main__':
    si = SHARKintReader('prod')
    df = si.get_data_in_dataframe()
