import flask
import json
from helpers.utils import (
    request_to_ckan_query,
    get_ckan_data,
)


def ckan_requestor(request):
    data = request_to_ckan_query(request)
    if isinstance(data, dict):
        return flask.make_response(json.dumps(data), 400)
    processed_request = get_ckan_data(data)
    return flask.make_response(json.dumps(processed_request))
