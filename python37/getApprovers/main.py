import json
import uuid
from flask import Response
import urllib
import os
import base64


with open('approver_recepient_name.json') as json_file:
    recepient_Name = json.load(json_file)

with open('approve_reject.json') as f:
    approve_reject = json.load(f)


def getApprovers(request):
    data = []
    filename = []
    links = []
    emailServer = request.args.get('emailServer')
    emailPassword = request.args.get('emailPassword')
    emailUser = request.args.get('emailUser')
    attachments = request.args.get('Attachments')
    if attachments is None:
        placeholder = ""
    else:
        placeholder = attachments.split(" | ")
    for y in range(len(placeholder)):
        path = urllib.parse.urlparse(placeholder[y]).path
        ext = os.path.splitext(path)[1]
        ext1 = ext.strip('.')
        filename.append(ext1.upper())
    for x in range(len(filename)):
        links1 = "<a href=" + placeholder[x] + ">" + filename[x] + "</a>"
        links.append(links1)
    separator = ' and '
    for i in range(len(recepient_Name)):
        uuidOne = uuid.uuid1()
        myUuid = str(uuidOne)
        if links[0] == "<a href=></a>":
            body_htmlpage1 = (
                'Hi,<br /><br />Task has been assigned to you.<br></br>'
                'Approve or Reject the Task using below buttons :<br/>'
                '<br></br></br><a href='
                + approve_reject[0]["ApproverLink"] + '?correlationKey='
            )
        else:
            body_htmlpage1 = (
                'Hi,<br /><br />Task has been assigned to you.<br>'
                '</br> Please go through the links '
                + separator.join(links) +
                ' and Approve or Reject the Task using below buttons :'
                '<br/><br></br></br>'
                '<a href='
                + approve_reject[0]["ApproverLink"] + '?correlationKey='
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
        en_body = base64.urlsafe_b64encode(
            body_htmlpage.encode('utf-8')
        ).decode('utf-8')
        data.append({
            'Name': recepient_Name[i]['name'],
            'Email': recepient_Name[i]['email'],
            'send_mail_approver_query_param': 'emailServer='
            + emailServer + '&emailUser=' + emailUser
            + '&emailPassword=' + emailPassword
            + '&recipientAddress=' + recepient_Name[i]['email']
            + '&messageSubject=Task Assigned to you'
            + '&messageBody=' + en_body + '&uuid='
            + myUuid + '&encoded=true',
            'uuid': myUuid,
            'send_Reminder_mail_approver_query_param': 'emailServer='
            + emailServer + '&' + 'emailUser=' + emailUser + '&'
            + 'emailPassword=' + emailPassword + '&' + 'recipientAddress='
            + recepient_Name[i]['email'] + '&messageSubject='
            + 'Reminder: Task Assigned to you&messageBody=' + en_body
            + '&uuid=' + myUuid + '&encoded=true',
            'uuid': myUuid,
        })
    python2json = json.dumps(data)
    Response(python2json, mimetype='application/json')
    return python2json
