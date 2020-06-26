import flask
import json
from helpers.utils import (
    read_xlxs,
)


def naiis_data_to_dict(request):
    data = read_xlxs(request)
    return flask.make_response(json.dumps(data, indent=4, sort_keys=True, default=str))
