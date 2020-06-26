import pandas as pd
import numpy as np

TYPES_MAP = {
    'num': 'int',
    'char': 'text',
    'decimal': 'float',
    'alphanumeric': 'text',
    'integer': 'int',
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
            data = {}
            df = excel_file.parse(sheet_name)
            for _, row in df.iterrows():
                row_list = row.values.tolist()
                if get_value_or_none(row_list[0]):
                    data[row_list[0]] = {
                        'name': get_value_or_none(row_list[0]),
                        'type': get_type(row_list[3], row_list[0]),
                        # 'label': get_value_or_none(row_list[1]),
                        # 'options': None,
                        # 'source': None,
                        # 'pii': get_value_or_none(row_list[2]),
                        # 'organism': get_value_or_none(row_list[4]),
                        # 'disease_of_interest_or_purpose': get_value_or_none(row_list[5])
                    }
                data_list[sheet_name] = data
    return data_list


def get_value_or_none(value):
    _isnan = False
    try:
        _isnan = np.isnan(value)
    except Exception:
        pass
    return None if _isnan else value


def get_type(value, n):
    _value = value if isinstance(value, str) else None
    if _value:
        for _key in TYPES_MAP:
            if _value.lower().startswith(_key):
                return TYPES_MAP[_key]
    return None
