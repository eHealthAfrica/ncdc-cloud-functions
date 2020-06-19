import json


def request_to_ckan_query(request):
    request_data = json.loads(request.data)
    categories = request_data.get('categories', [])
    fields = request_data.get('fields', [])
    ckan_query_url = \
        f'/q?categories={json.dumps(categories)}&facets={json.dumps(fields)}'
    return ckan_query_url
