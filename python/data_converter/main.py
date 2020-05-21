import flask
from helpers.utils import (
    csv_list_to_dict,
    csv_list_to_xml,
    csv_process_content_type,
)


def csv_to_json(request):
    data = csv_process_content_type(request)
    if isinstance(data, list):
        return flask.jsonify(csv_list_to_dict(data))
    return flask.make_response('Invalid csv provided.', 400)


def csv_to_xml(request):
    data = csv_process_content_type(request)
    if isinstance(data, list):
        return csv_list_to_xml(data)
    return flask.make_response('Invalid csv provided.', 400)
