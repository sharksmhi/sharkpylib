#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import os
import re
import codecs
import pandas as pd
import sharkpylib


def convert_standard_format_to_nodc_standard_format(file_path, prefix='nodc', **kwargs):
    comment_id = kwargs.get('comment_id', '//')
    encoding = kwargs.get('encoding', 'cp1252')
    data_delimiter = kwargs.get('data_delimiter', '\t')
    metadata = []
    header = []
    data = []
    with codecs.open(file_path, encoding='cp1252') as fid:
        for line in fid:
            if line.startswith(comment_id):
                metadata.append(line)
            else:
                split_line = re.split(data_delimiter, line.strip('\n\r'))
                split_line = [item.strip() for item in split_line]
                if not header:
                    header = split_line
                else:
                    data.append(split_line)

    df = pd.DataFrame(data, columns=header)
    updated_df = sharkpylib.mappinglib.add_nodc_qc_columns_to_df(df)

    # Saving file
    if prefix:
        directory = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        output_file_path = os.path.join(directory, f'{prefix}_{file_name}')
    else:
        output_file_path = file_path

    data_dict = updated_df.to_dict('split')

    with codecs.open(output_file_path, 'w', encoding=encoding) as fid:
        fid.write(''.join(metadata))
        # Write column header
        fid.write(data_delimiter.join(data_dict['columns']))
        fid.write('\n')
        for line in data_dict['data']:
            fid.write(data_delimiter.join(line))
            fid.write('\n')