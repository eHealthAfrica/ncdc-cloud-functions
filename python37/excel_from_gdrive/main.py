import flask
import json
from helpers.utils import (
    file_to_dict,
)


def excel_from_gdrive(request):
    data = file_to_dict(request)
    if isinstance(data, list):
        return flask.make_response(json.dumps(data))
    return flask.make_response(json.dumps(data), 400)
