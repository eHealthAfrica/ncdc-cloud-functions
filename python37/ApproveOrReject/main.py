
import json
import flask
from flask import flash, request
import requests
from flask import Response
from requests.auth import HTTPBasicAuth


with open('approve_endpoint.json') as json_file:

    data = json.load(json_file)
 
# URL = data[0]["url"]
# Username = data[0]["Username"]
# Password = data[0]["Password"]
# print(URL)
# print(Username)
# print(Password)

def ApproveOrReject(request):

	# decision=request.args.get('decision')
	correlationKey1=request.args.get('correlationKey')
	correlationKey=correlationKey1[:-1]
	if correlationKey1[-1] == "t":
		decision = "true"
	else:
		decision = "false"
	# print(decision)
	# print(correlationKey)
	PARAMS = {"listener_name":data[0]["listener_name"],"correlationKey": correlationKey,  "variables": { "decision" : decision}}
	# print(PARAMS)
	headers = {
   'Content-Type': "application/json"   
   }
	response = requests.request("GET", data[0]["url"],auth=HTTPBasicAuth(data[0]["Username"], data[0]["Password"]), data=json.dumps(PARAMS), headers=headers, params={"id":"default"})
	
	print(response)
	result1 = response.text
	result = {"success":result1.replace("\n","")}
	python2json = json.dumps(result)
	Response(python2json, mimetype='application/json')
	# print(python2json)
	# print(type(python2json))
	return python2json
	
