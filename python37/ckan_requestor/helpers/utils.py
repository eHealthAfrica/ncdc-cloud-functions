import json
import os
import requests
import base64
import logging

import asyncio
import aiohttp
import pandas as pd
import numpy as np

from urllib import parse

from datetime import datetime
from ckanapi import RemoteCKAN
from ckanapi import errors as ckanapi_errors
from gcloud.aio.storage import Storage
from aiofile import AIOFile

LOG = logging.getLogger('Utils')

BUCKET_NAME = 'ncdc-nrl'


def request_to_ckan_query(rq):
    data = rq.get_json(silent=True)
    CKAN_URL = data.get('ckan_url')
    CKAN_API_KEY = data.get('ckan_api_key')
    EMAIL_PARAMS = data.get('email_params')

    if not CKAN_API_KEY or not CKAN_URL or not EMAIL_PARAMS:
        return {
            'error': 'Invalid request. Provide ckan_url,'
            + 'ckan_api_key and emailing_params in the body.'
        }
    else:
        content_type = rq.headers.get('Content-Type')
        result = []
        excel_file = None
        if content_type and content_type.startswith('multipart/form-data'):
            if 'file' not in rq.files:
                raise ValueError('No request file provided.')
            excel_file = pd.ExcelFile(rq.files['file'])
        elif content_type and content_type == 'application/json':
            link = data.get('file')
            attachments = EMAIL_PARAMS.get('attachments')
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
            elif len(attachments):
                for attachment in attachments:
                    if '.xls' in attachment:
                        o = parse.urlparse(attachment)
                        url = o._replace(path=parse.quote(o.path))
                        excel_file = pd.ExcelFile(url.geturl())
                        break
                if excel_file is None:
                    return {'error': 'No excel file is attached.'}
            else:
                return {'error': 'No file link was provided.'}
        else:
            return {'error': 'Malformed request.'}

        if len(excel_file.sheet_names):
            df = excel_file.parse(excel_file.sheet_names[0])
            dataset = None
            fields = []
            query = {}
            is_first = True
            is_all_datasets = False
            all_datasets_list = []
            for _, row in df.iterrows():
                row_list = row.values.tolist()
                _temp_dataset = get_value_or_none(row_list[0])

                if _temp_dataset == '*' and is_first:
                    is_all_datasets = True
                    config = {
                        'apikey': CKAN_API_KEY,
                        'address': CKAN_URL,
                    }

                    try:
                        ckan = RemoteCKAN(**config)
                        datasets = ckan.action.package_list()
                        all_datasets_list = datasets
                        field = get_value_or_none(row_list[1])
                        if field:
                            fields.append(field)
                        query_key = get_value_or_none(row_list[2])
                        query_value = get_value_or_none(row_list[3])
                        if query_key and query_value:
                            query[query_key] = query_value
                    except ckanapi_errors.ValidationError as e:
                        return {'error':
                                f'CKAN error: {json.dumps(e.error_dict)}'}
                elif is_all_datasets:
                    field = get_value_or_none(row_list[1])
                    if field:
                        fields.append(field)
                    query_key = get_value_or_none(row_list[2])
                    query_value = get_value_or_none(row_list[3])
                    if query_key and query_value:
                        query[query_key] = query_value
                else:
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

                is_first = False

            if is_all_datasets:
                for ds in all_datasets_list:
                    result.append({
                        ds: {
                            'q': query,
                            'f': fields,
                        },
                    })
            else:
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


def get_ckan_data(rq, request_data):
    _d = rq.get_json(silent=True)
    CKAN_URL = _d.get('ckan_url')
    CKAN_API_KEY = _d.get('ckan_api_key')
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
                dataset = ckan.action.package_show(id=d.lower())
                resource_id = dataset['resources'][0]['id']
                qs = {
                    'resource_id': resource_id,
                    'filters': rq[d]['q'],
                    'fields': rq[d]['f'],
                }
                resp = ckan.action.datastore_search(**qs)
                results.append({
                    d: {
                            'count': f'{resp["total"]} records found.',
                            'filters': rq[d]['q'],
                    }
                })
                record_count = len(resp['records'])
                if record_count:
                    if record_count < resp["total"]:
                        qs = {
                            'resource_id': resource_id,
                            'filters': rq[d]['q'],
                            'fields': rq[d]['f'],
                            'limit': resp["total"],
                        }
                        resp = ckan.action.datastore_search(**qs)
                    data.append({
                        d: resp['records']
                    })
            except ckanapi_errors.ValidationError as e:
                results.append({
                    d: {'error': json.dumps(e.error_dict)}
                })
                continue

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
            f'downloads/{blob_name}',
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


def get_mailing_params(rq, data):
    _d = rq.get_json(silent=True)
    EMAIL_PARAMS = _d.get('email_params')
    results = ''
    for ds in data['message']:
        for i in ds:
            try:
                filters = json.dumps(ds[i]['filters'], indent=2) \
                    if len(ds[i]['filters']) else 'None'
                results += (
                    i + ' : ' + ds[i]['count'] + '<br/>'
                    '(Applied Filters: ' + filters + ')<br/><br/>'
                )
            except Exception:
                LOG.error(f'{i}: {ds[i]["error"]}')

    body = (
        'Hi, <br></br><br></br> Your request has '
        'been approved.<br/>Here is a link to the downloadable file:<br/>'
        '<a href="' + data['link'] + '">' + data['link']
        + '</a><br/><br/> with the following results: <br/>'
        + results + '<br></br><br></br>Thanks,<br />Support Team.'
    )

    en_body = base64.urlsafe_b64encode(
        body.encode('utf-8')
    ).decode('utf-8')
    params = (
        'emailServer='
        + EMAIL_PARAMS['server'] + '&emailUser=' + EMAIL_PARAMS['user']
        + '&emailPassword=' + EMAIL_PARAMS['password'] + '&recipientAddress='
        + EMAIL_PARAMS['requestor_email'] + '&messageSubject=Request Approved&'
        'messageBody=' + en_body + '&encoded=true'
    )
    data['approval_email_params'] = params

    return data
