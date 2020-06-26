import json
import os
import requests

import asyncio
import aiohttp
import pandas as pd
import numpy as np

from datetime import datetime
from ckanapi import RemoteCKAN
from ckanapi import errors as ckanapi_errors
from gcloud.aio.storage import Storage
from aiofile import AIOFile


CKAN_URL = 'http://aether.local:5000/'
CKAN_API_KEY = 'd44f69dd-bb49-4fec-98d3-cf62d2d88a1f'
BUCKET_NAME = 'ncdc-nrl'


def request_to_ckan_query(request):
    content_type = request.headers.get('Content-Type')
    result = []
    excel_file = None
    if content_type and content_type.startswith('multipart/form-data'):
        if 'file' not in request.files:
            raise ValueError('No request file provided.')
        excel_file = pd.ExcelFile(request.files['file'])
    elif content_type and content_type == 'application/json':
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

                    if token:
                        params = {'id': id, 'confirm': token}
                        response = requests.get(
                            url,
                            params=params,
                            stream=True,
                            verify=False
                        )

                    excel_file = pd.ExcelFile(response.content)
                except Exception as e:
                    return {'error': str(e)}
            else:
                return {'error': 'An invalid Google drive file url was provided.'}
        else:
            return {'error': 'No file link was provided.'}
    else:
        return {'error': 'Malformed request.'}

    if len(excel_file.sheet_names):
        df = excel_file.parse(excel_file.sheet_names[0])
        dataset = None
        fields = []
        query = {}
        for _, row in df.iterrows():
            row_list = row.values.tolist()
            _temp_dataset = get_value_or_none(row_list[0])
            if _temp_dataset and dataset is None:
                dataset = _temp_dataset
            if dataset and _temp_dataset and dataset is not _temp_dataset:
                result.append({
                    dataset: {
                        'q': query,
                        'f': fields,
                    },
                })
                fields = []
                query = {}
                dataset = _temp_dataset

            field = get_value_or_none(row_list[1])
            if field:
                fields.append(field)
            query_key = get_value_or_none(row_list[2])
            query_value = get_value_or_none(row_list[3])
            if query_key and query_value:
                query[query_key] = query_value

        result.append({
            dataset: {
                'q': query,
                'f': fields,
            },
        })
    return result


def get_value_or_none(value):
    _isnan = False
    try:
        _isnan = np.isnan(value)
    except Exception:
        pass
    return None if _isnan else value


def get_ckan_data(request_data):
    results = []
    data = []
    config = {
        'apikey': CKAN_API_KEY,
        'address': CKAN_URL,
    }
    ckan = RemoteCKAN(**config)
    for rq in request_data:
        for d in rq:
            try:
                dataset = ckan.action.package_show(id=d)
                resource_id = dataset['resources'][0]['id']
                qs = {
                    'resource_id': resource_id,
                    'filters': rq[d]['q'],
                    'fields': rq[d]['f']
                }
                resp = ckan.action.datastore_search(**qs)
                results.append({
                    d: f'{resp["total"]} records found.'
                })
                if len(resp['records']):
                    data.append({
                        d: resp['records']
                    })
            except ckanapi_errors.ValidationError as e:
                results.append({
                    d: {'error': json.dumps(e.error_dict)}
                })

    link = ''
    if len(data):
        # zip and upload
        file_name = f'ncdc-nrl-{datetime.now().strftime("%d%m%Y%H%M%S")}.xlsx'
        file_path = f'temp/{file_name}'
        with pd.ExcelWriter(file_path) as writer:
            for row in data:
                for prop in row:
                    df = pd.DataFrame(row[prop])
                    df.to_excel(writer, sheet_name=prop)

        link = asyncio.run(upload(f'./{file_path}', file_name))
        os.remove(file_path)
    return {'link': link, 'message': results}


async def async_upload_to_bucket(blob_name, file_obj):
    async with aiohttp.ClientSession() as session:
        storage = Storage(service_file='./cred/cred.json', session=session)
        status = await storage.upload(
            BUCKET_NAME,
            f'{blob_name}',
            file_obj
        )
        return status['mediaLink']


async def upload(file_path, file_name):
    async with AIOFile(file_path, mode='rb') as afp:
        f = await afp.read()
        url = await async_upload_to_bucket(file_name, f)
        return url


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def url_to_id(url):
    x = url.split("/")
    return x[5] if len(x) > 5 else None
