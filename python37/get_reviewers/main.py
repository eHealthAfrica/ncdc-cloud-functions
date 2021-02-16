import json
import uuid
from flask import Response
import urllib
import os
import base64


def get_reviewers(request):
    data = []
    filename = []
    links = []
    emailServer = request.args.get('emailServer')
    emailPassword = request.args.get('emailPassword')
    emailUser = request.args.get('emailUser')
    attachments = request.args.get('Attachments')
    reviewers = request.args.get('reviewers', '').split(',')
    sender = request.args.get('Sender')
    senderAddress = request.args.get('senderAddress')

    recepient_Name = reviewers
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
        links1 = (
            '<a id="links" href="' + placeholder[x]
            + '">' + filename[x] + '</a>'
        )
        links.append(links1)
    separator = ' and '
    for i in range(len(recepient_Name)):
        uuidOne = uuid.uuid1()
        myUuid = str(uuidOne)
        if links[0] == "<a href=></a>":
            body_htmlpage = (
                'Hi,<br /><br />A task has been assigned to you.<br></br>'
                'A malformed data request has been submitted.<br/><br/>'
                'Requester Email Address: ' + sender + ' : '
                + '<a id="emails" href="mailto:' + senderAddress + '" target="_blank">'
                + senderAddress + '</a><br/><br/>'
                'Thanks,<br />Support Team'
            )
        else:
            body_htmlpage = (
                'Hi,<br /><br />A review task has been assigned to you.<br>'
                '</br> Please go through the links '
                + separator.join(links) +
                ' and foward a summary for approval.'
                '<br/><br/>Requester Email Address: ' + sender + ' : '
                + '<a id="emails" href="mailto:' + senderAddress
                + '" target="_blank">'
                + senderAddress + '</a><br/><br/>'
                '<br/></br>Thanks,<br />Support Team'
            )
        en_body = base64.urlsafe_b64encode(
            body_htmlpage.encode('utf-8')
        ).decode('utf-8')
        data.append({
            'Email': recepient_Name[i],
            'send_mail_reviewer_query_param': 'emailServer='
            + emailServer + '&emailUser=' + emailUser
            + '&emailPassword=' + emailPassword
            + '&recipientAddress=' + recepient_Name[i]
            + '&messageSubject=Review Task Assigned to you'
            + '&messageBody=' + en_body + '&uuid='
            + myUuid + '&encoded=true',
            'uuid': myUuid,
            'send_reminder_mail_reviewer_query_param': 'emailServer='
            + emailServer + '&' + 'emailUser=' + emailUser + '&'
            + 'emailPassword=' + emailPassword + '&' + 'recipientAddress='
            + recepient_Name[i] + '&messageSubject='
            + 'Reminder: Review Task Assigned to you&messageBody=' + en_body
            + '&uuid=' + myUuid + '&encoded=true',
            'uuid': myUuid,
        })
    python2json = json.dumps(data)
    Response(python2json, mimetype='application/json')
    return python2json
