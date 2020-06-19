import json
import uuid
from flask import Response
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

recepient_Name = [{
	"name": "shashank harsh",
	"email": "shashank.h@axxonet.net",
	"something_else": ""
}, {
	"name": "Uma",
	"email": "uma.m@axxonet.net",
	"something_else": ""
}, {
	"name": "basavaraja",
	"email": "basavaraja.pa@axxonet.net",
	"something_else": ""
}]


def getApprovers(request):
     # for i in range len(recepient_Name):
        data = []        
        emailServer = request.args.get('emailServer')
        emailPassword = request.args.get('emailPassword')
        emailUser = request.args.get('emailUser')
        recipientAddress = request.args.get('recipientAddress')
        
        body_htmlpage = """Hi,<br /><br />Task has been assigned to you.<br></br> Please go through the links <a href= https://storage.cloud.google.com/attached-mail-file/myfileGCP0>PDF File</a> and <a href= https://storage.cloud.google.com/attached-mail-file/myfileGCP1>XLS File</a> and Approve or Reject the Task using below buttons :<br/><br></br></br> <a href=https://us-central1-quick-bonfire-278608.cloudfunctions.net/approveorReject?approve=approved><button>Approve</button></a> <a href=https://us-central1-quick-bonfire-278608.cloudfunctions.net/approveorReject?approve=rejected><button style="margin-left: 20px">Reject</button></a><br/><br />Thanks,<br />Support Team"""

        for i in range (len(recepient_Name)):
                uuidOne = uuid.uuid1()
                myUuid = str(uuidOne)
                data.append({"Name": recepient_Name[i]["name"],"Email": recepient_Name[i]["email"],"send_mail_approver_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+recepient_Name[i]["email"]+"&"+"messageSubject=""Task Assigned to you""&"+"messageBody="+body_htmlpage+"&"+"uuid="+myUuid,"uuid":myUuid,
                                                            "send_Reminder_mail_approver_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+recepient_Name[i]["email"]+"&"+"messageSubject=""Reminder: Task Assigned to you""&"+"messageBody="+body_htmlpage+"&"+"uuid="+myUuid,"uuid":myUuid,})

        python2json = json.dumps(data)
        print(python2json)
        Response(python2json, mimetype='application/json')
        return python2json
