import flask
import json
from helpers.utils import (
    dict_to_ckan,
)


def push_to_ckan(request):
    data = dict_to_ckan(request)
    if isinstance(data, list):
        return flask.make_response(json.dumps(data))
    return flask.make_response(json.dumps(data), 400)
