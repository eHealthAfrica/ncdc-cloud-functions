from .ckan import CKANInstance
from .data_dictionaries import DATA_DICTIONARY


def dict_to_ckan(request):
    request_body = request.get_json(silent=True) or {}
    data = request_body.get('data')
    ckan_url = request_body.get('ckan_url')
    ckan_api_key = request_body.get('ckan_api_key')

    result = []

    if ckan_url and data and ckan_api_key:
        config = {
            'apikey': ckan_api_key,
            'address': ckan_url,
        }
        ckan = CKANInstance(config)
        for sheet in data:
            try:
                dataset_data = {
                    'name': sheet['name'],
                }
                dataset = ckan.create_dataset(dataset_data)
                resource = ckan.create_resource(sheet['name'], dataset)
                if resource:
                    resource_data = sheet['data']
                    fields = get_fields(resource_data[0], DATA_DICTIONARY)
                    ckan.create_resource_in_datastore(resource)
                    ckan.send_data_to_datastore(fields, resource_data, resource)
                result.append({
                    'info': f'Processed {sheet["name"]} data.'
                })
            except Exception as e:
                result.append({
                    'error': str(e),
                })
        return result
    else:
        return {'error': 'Missing CKAN URL or data.'}


def get_fields(sample_data, data_dict):
    fields = []
    for item in sample_data:
        match = None
        for dict_dataset in data_dict:
            try:
                match = data_dict[dict_dataset][item]
                fields.append({
                    'id': item,
                    'type': match['type'],
                })
                break
            except KeyError:
                pass
        if match is None:
            # default type to text
            fields.append({
                'id': item,
                'type': 'text',
            })
    return fields
