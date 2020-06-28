import flask
import json
from helpers.utils import (
    request_to_ckan_query,
    get_ckan_data,
    get_mailing_params,
)


def ckan_requestor(request):
    data = request_to_ckan_query(request)
    if isinstance(data, dict):
        return flask.make_response(data, 400)
    processed_request = get_ckan_data(request, data)
    processed_data_with_email = get_mailing_params(request, processed_request)
    return flask.make_response(processed_data_with_email)
