import pandas as pd
import numpy as np


def read_xlxs(request):
    content_type = request.headers.get('Content-Type')
    data_list = []
    if content_type.startswith('multipart/form-data'):
        if 'file' not in request.files:
            raise ValueError('No file provided.')
        excel_file = pd.ExcelFile(request.files['file'])
        sheet_names = excel_file.sheet_names
        for sheet_name in sheet_names:
            df = excel_file.parse(sheet_name)
            sheet_dict = {
                'name': sheet_name,
            }
            data = {}
            has_started = False
            for _, row in df.iterrows():
                row_list = row.values.tolist()
                if has_started:
                    data[row_list[1]] = None \
                        if not isinstance(row_list[3], str) \
                        and np.isnan(row_list[3]) else row_list[3]
                else:
                    has_started = row_list[0] == '#'
            sheet_dict['data'] = data
            data_list.append(sheet_dict)
    return data_list
