import email
import imaplib
import mailbox
import json
from OpenSSL import crypto
from OpenSSL import SSL
from backports import ssl
from imapclient import IMAPClient
from flask import Response
from flask import Flask
from flask import jsonify
# import werkzeug
from flask import flash, request

app = Flask(__name__)

nomail = {"result" : "false", "body" : "no mail founded"}


def checkMail(request):
        emailServer = request.args.get('emailServer')
        emailPassword = request.args.get('emailPassword')
        emailUser = request.args.get('emailUser')
        recipientAddress = request.args.get('recipientAddress')
        #messageSubject = request.args.get('messageSubject')
        #messageBody = request.args.get('messageBody')
        sender = []
        allsender =[]
        allfiles =[]
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        imapObj = IMAPClient(emailServer, ssl=True, ssl_context=context)
        mail = imaplib.IMAP4_SSL(emailServer)
        mail.login(emailUser, emailPassword)
        mail.list()
        mail.select('inbox')
        result, data = mail.uid('search', None, "UNSEEN") # (ALL/UNSEEN)
        i = len(data[0].split())
        print(i)
        if(i==0):
                return nomail
        else:
                for x in range(i):
                        latest_email_uid = data[0].split()[x]
                        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
                        latest_email_uid = data[0].split()[x]
                        raw_email = email_data[0][1]
                        raw_email_string = raw_email.decode('utf-8')
                        email_message = email.message_from_string(raw_email_string)
                        for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True)
                                if part.get_content_maintype() == 'multipart':
                                        continue
                                if part.get('Content-Disposition') is None:
                                        continue
                                fileName = part.get_filename()
                                allfiles.append(fileName)


                        # Header Details
                        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
                        email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
                        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
                        sender.append(email_from)
                        a = {"Sender":sender[x], "send_mail_requester_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+sender[x]+"&"+"messageSubject=""Request Accepted""&"+"messageBody=""Hi, <br></br><br></br> Your request has been Accepted<br></br><br></br> Thanks,<br />Support Team",
                                                 "send_mail_approver_approved_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+sender[x]+"&"+"messageSubject=""Request Approved""&"+"messageBody=""Hi, <br></br><br></br> Your request has been approved<br></br><br></br> Thanks,<br />Support Team",
                                                 "send_mail_approver_rejected_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+sender[x]+"&"+"messageSubject=""Request Rejected""&"+"messageBody=""Hi, <br></br><br></br> Your request has been rejected<br></br><br></br> Thanks,<br />Support Team"}
                        allsender.append(a)
                        allfiles.clear()
                        my_json_string = json.dumps(allsender)
                        print(my_json_string)
                        Response(my_json_string, mimetype='application/json')

        return my_json_string
