import flask
import json
from helpers.utils import (
    get_request_category_fields,
)


def ckan_utils(request):
    return flask.make_response(get_request_category_fields(request))
