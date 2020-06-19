import flask
import json
from helpers.utils import (
    read_xlxs,
)


def naiis_dict_avro(request):
    data = read_xlxs(request)
    return flask.make_response(json.dumps(data))
