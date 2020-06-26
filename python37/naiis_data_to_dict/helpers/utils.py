import pandas as pd
import numpy as np

TYPES_MAP = {
    'num': 'int',
    'char': 'text',
    'decimal': 'float',
    'alphanumeric': 'text',
    'integer': 'int',
    'decimal': 'float',
}


def read_xlxs(request):
    content_type = request.headers.get('Content-Type')
    data_list = {}
    if content_type.startswith('multipart/form-data'):
        if 'file' not in request.files:
            raise ValueError('No file provided.')
        excel_file = pd.ExcelFile(request.files['file'])
        sheet_names = excel_file.sheet_names
        for sheet_name in sheet_names:
            df = excel_file.parse(sheet_name)
            data = {}
            has_started = False
            for _, row in df.iterrows():
                row_list = row.values.tolist()
                if has_started and get_value_or_none(row_list[1]):
                    data[row_list[1]] = {
                        'name': get_value_or_none(row_list[1]),
                        'type': get_type(row_list[2]),
                        # 'label': row_list[3],
                        # 'options': get_value_or_none(row_list[4]),
                        # 'source': get_value_or_none(row_list[5]),
                    }

                else:
                    has_started = row_list[0] == '#'
                data_list[sheet_name] = data
    return data_list


def get_value_or_none(value):
    _isnan = False
    try:
        _isnan = np.isnan(value)
    except Exception:
        pass

    return None if _isnan else value


def get_type(value):
    _type = 'text'
    try:
        _type = TYPES_MAP[value.lower()]
    except KeyError:
        pass
    return _type
