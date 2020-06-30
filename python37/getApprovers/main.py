import json
import uuid
from flask import Response
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


with open('approver_recepient_name.json') as json_file:
    recepient_Name = json.load(json_file)

with open('approve_reject.json') as f:
    approve_reject = json.load(f)


def getApprovers(request):
    data = []
    emailServer = request.args.get('emailServer')
    emailPassword = request.args.get('emailPassword')
    emailUser = request.args.get('emailUser')

    for i in range(len(recepient_Name)):
        myUuid = str(uuid.uuid1())

        body_htmlpage1 = (
            'Hi,<br /><br />Task has been assigned to you.'
            '<br></br> Please go through the links'
            ' <a href=https://storage.cloud.google.com/attached-mail-file/myfileGCP0>PDF File</a>'
            ' and <a href=https://storage.cloud.google.com/attached-mail-file/myfileGCP1>XLS File</a>'
            ' and Approve or Reject the Task using below buttons :'
            '<br/><br></br></br> <a href=' + approve_reject[0]['ApproverLink']
            + '?correlationKey='
        )

        body_htmlpage2 = (
            '><button>Approve</button></a> <a href='
            + approve_reject[0]['ApproverLink'] + '?correlationKey='
        )

        body_htmlpage3 = (
            '><button style="margin-left: 20px">Reject</button>'
            '</a><br/><br />Thanks,<br />Support Team'
        )

        body_htmlpage = (
            body_htmlpage1 + myUuid + 't' + body_htmlpage2
            + myUuid + 'f' + body_htmlpage3
        )
        data.append({
            'Name': recepient_Name[i]['name'],
            'Email': recepient_Name[i]['email'],
            'send_mail_approver_query_param': 'emailServer='
            + emailServer + '&emailUser=' + emailUser
            + '&emailPassword=' + emailPassword
            + '&recipientAddress=' + recepient_Name[i]['email']
            + '&messageSubject=Task Assigned to you'
            + '&messageBody=' + body_htmlpage + '&uuid='
            + myUuid,
            'uuid': myUuid,
            'send_Reminder_mail_approver_query_param': 'emailServer='
            + emailServer + '&' + 'emailUser=' + emailUser + '&'
            + 'emailPassword=' + emailPassword + '&' + 'recipientAddress='
            + recepient_Name[i]['email'] + '&messageSubject='
            + 'Reminder: Task Assigned to you&messageBody=' + body_htmlpage
            + '&uuid=' + myUuid,
            'uuid': myUuid,
        })

    python2json = json.dumps(data)
    # print(python2json)
    Response(python2json, mimetype='application/json')
    return python2json
