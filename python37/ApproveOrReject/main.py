
import json
from flask import request
import requests
from flask import Response
from requests.auth import HTTPBasicAuth


with open('approve_endpoint.json') as json_file:

    data = json.load(json_file)


def ApproveOrReject():
    correlationKey1 = request.args.get('correlationKey')
    correlationKey = correlationKey1[:-1]
    if correlationKey1[-1] == "t":
        decision = "true"
    else:
        decision = "false"
    PARAMS = {
        "listener_name": data[0]["listener_name"],
        "correlationKey": correlationKey,
        "variables": {"decision": decision}
    }
    headers = {
        'Content-Type': "application/json"
    }
    response = requests.request(
        "GET",
        data[0]["url"],
        auth=HTTPBasicAuth(
            data[0]["Username"],
            data[0]["Password"]
        ),
        data=json.dumps(PARAMS),
        headers=headers,
        params={"id": "default"}
    )

    result1 = response.text
    result = {"success": result1.replace("\n", "")}
    python2json = json.dumps(result)
    Response(python2json, mimetype='application/json')
    return python2json
