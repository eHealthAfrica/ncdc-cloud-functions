import flask
import json
# import pandas as pd
from helpers.utils import (
    read_xlxs,
    request_to_ckan_query,
)


def naiis_dict_avro(request):
    data = read_xlxs(request)
    return flask.make_response(json.dumps(data))


def ckan_query_generator(request):
    data = request_to_ckan_query(request)
    return flask.make_response(json.dumps(data))
