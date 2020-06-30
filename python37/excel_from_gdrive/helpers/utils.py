import pandas as pd
import json
import requests
import traceback


def file_to_dict(request):
    link = request.get_json(silent=True).get('file')

    if link:
        id = url_to_id(link)
        if id:
            try:
                url = "https://docs.google.com/uc?export=download"
                response = requests.get(
                    url,
                    params={'id': id},
                    stream=True,
                    verify=False
                )

                token = get_confirm_token(response)
                data_list = []

                if token:
                    params = {'id': id, 'confirm': token}
                    response = requests.get(
                        url,
                        params=params,
                        stream=True,
                        verify=False
                    )

                excel_file = pd.ExcelFile(response.content)
                sheet_names = excel_file.sheet_names
                for sheet_name in sheet_names:
                    df = excel_file.parse(sheet_name)
                    sheet_dict = {
                        'name': sheet_name,
                        'data': json.loads(df.to_json(orient='records'))
                    }
                    data_list.append(sheet_dict)
                return data_list
            except Exception as e:
                return {'error': str(e)}
        else:
            return {'error': 'An invalid Google drive file url was provided.'}
    else:
        return {'error': 'No file link was provided.'}


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def url_to_id(url):
    x = url.split("/")
    return x[5] if len(x) > 5 else None
