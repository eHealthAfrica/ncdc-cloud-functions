import json
import os
import requests
import base64
import logging

import io
import urllib.request
import asyncio
import aiohttp
import pandas as pd
import numpy as np

from datetime import datetime
from ckanapi import RemoteCKAN
from ckanapi import errors as ckanapi_errors
from gcloud.aio.storage import Storage
from aiofile import AIOFile

LOG = logging.getLogger('Utils')


def get_request_category_fields(rq):
    data = rq.get_json(silent=True) or {}
    switch = data.get('ops', 'get')
    if switch == 'get_categories':
        pass
    try:
        CKAN_URL = data.get('ckan_url') or rq.form['ckan_url']
        CKAN_API_KEY = data.get('ckan_api_key') or rq.form['ckan_api_key']
    except Exception:
        pass

    if not CKAN_API_KEY or not CKAN_URL:
        return {
            'error': 'Invalid request. Provide ckan_url,'
            + 'and ckan_api_key in the body.'
        }
    else:
        excel_file = load_excel_file(rq, data)
        if isinstance(excel_file, dict) and 'error' in excel_file:
            return excel_file
        if len(excel_file.sheet_names):
            df = excel_file.parse(excel_file.sheet_names[0])
            _current_category = 'unknown'
            _groups = {}
            for _, row in df.iterrows():
                row_list = row.values.tolist()
                _category = get_value_or_none(row_list[0])
                _field = get_value_or_none(row_list[2])
                _current_category = _category if _category \
                    else _current_category
                if _field:
                    if _current_category in _groups:
                        _groups[_current_category].add(_field)
                    else:
                        _groups[_current_category] = set()
                        _groups[_current_category].add(_field)

            for g in _groups:
                print(g)

        return json.dumps(_groups, default=set_default)


def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


def get_value_or_none(value):
    _isnan = False
    try:
        _isnan = np.isnan(value)
    except Exception:
        pass
    return None if _isnan else value


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def url_to_id(url):
    x = url.split("/")
    return x[5] if len(x) > 5 else None


def load_excel_file(rq, data):
    content_type = rq.headers.get('Content-Type')
    excel_file = None
    if content_type and content_type.startswith('multipart/form-data'):
        if 'file' not in rq.files:
            raise ValueError('No request file provided.')
        try:
            excel_file = pd.ExcelFile(rq.files['file'])
            return excel_file
        except Exception as e:
            return {'error': str(e)}
    elif content_type and content_type == 'application/json':
        link = data.get('file')
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

                    if token:
                        params = {'id': id, 'confirm': token}
                        response = requests.get(
                            url,
                            params=params,
                            stream=True,
                            verify=False
                        )

                    excel_file = pd.ExcelFile(response.content)
                    return excel_file
                except Exception as e:
                    return {'error': str(e)}
            else:
                return {
                    'error': 'An invalid Google drive file url was provided.'
                }
        else:
            return {'error': 'No file link was provided.'}
    else:
        return {'error': 'Malformed request.'}
