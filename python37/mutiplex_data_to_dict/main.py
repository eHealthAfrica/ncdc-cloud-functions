import flask
import json
from helpers.utils import (
    read_xlxs,
)


def multiplex_data_to_dict(request):
    data = read_xlxs(request)
    return flask.make_response(json.dumps(data))
