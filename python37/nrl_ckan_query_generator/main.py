import flask
import json
from helpers.utils import (
    request_to_ckan_query,
)


def ckan_query_generator(request):
    data = request_to_ckan_query(request)
    return flask.make_response(json.dumps(data))