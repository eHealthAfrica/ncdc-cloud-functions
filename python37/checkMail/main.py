import email
import imaplib
import json
import shutil
import os
from flask import Response
from flask import Flask
import tempfile
import re
import logging
import datetime
from google.cloud import storage

result = {'Result': 'Successfully Uploaded', 'Source': 'GCP Storage'}

with open('parameters.json') as json_file:
    params = json.load(json_file)

app = Flask(__name__)

nomail = [{'success': 'false', 'Sender': 'None', 'Body': 'None'}]


def checkMail(request):
    now = datetime.datetime.now()
    timenow = str(now.strftime('_%Y-%m-%d_%H:%M:%S'))
    char_list = ['%', '-', ':']
    comp_time = re.sub('|'.join(char_list[:]), '', timenow)
    storage_client = storage.Client.from_service_account_json('project.json')
    emailServer = request.args.get('emailServer')
    emailPassword = request.args.get('emailPassword')
    emailUser = request.args.get('emailUser')
    sender = []

    allsender = []
    mail = imaplib.IMAP4_SSL(emailServer)
    mail.login(emailUser, emailPassword)
    mail.list()
    mail.select('inbox')
    result, data = mail.uid('search', None, 'UNSEEN')   # (ALL/UNSEEN)
    j = len(data[0].split())
    nomail_Json = json.dumps(nomail)
    Response(nomail_Json, mimetype='application/json')
    if(j == 0):
        return nomail_Json
    else:
        for x in range(j):
            modifiedurl = []
            filePath = ''
            latest_email_uid = data[0].split()[x]
            result, email_data = mail.uid(
                'fetch',
                latest_email_uid,
                '(RFC822)'
            )
            latest_email_uid = data[0].split()[x]
            raw_email = email_data[0][1]
            raw_email_string = raw_email.decode('utf-8')
            email_message = email.message_from_string(raw_email_string)
            # Ensure the file is read/write by the creator only
            saved_umask = os.umask(0o77)
            # Header Details
            email_from = str(email.header.make_header(
                email.header.decode_header(email_message['From'])
            ))
            sender.append(email_from)

            tmpdir = tempfile.mkdtemp()
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                fileName = part.get_filename()

                if bool(fileName):
                    filePath = os.path.join(tmpdir, fileName)
                if not os.path.isfile(filePath):
                    fp = open(filePath, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
                url2 = []
                extension = []
                modifiedurl = []

                bucket_name = params[0]['bucket_name']
                folder = params[0]['folder']
                bucket = storage_client.get_bucket(bucket_name)

                arr = os.listdir(tmpdir)

                for i in range(len(arr)):
                    filename = str(arr[i-1])
                    split_string = filename.split('.')
                    new_file = 'requests/' + split_string[0] + comp_time + '.' + split_string[1]
                    extension1 = split_string[1]
                    extension.append(extension1.upper() + ' ' + 'File')
                    url2.append(new_file)
                    blob = bucket.blob(new_file)
                    xpath = os.path.join(tmpdir, arr[i])
                    with open(xpath, 'rb') as f:
                        blob.upload_from_file(f)
                        filename2 = list(bucket.list_blobs(prefix=''))
                        for blob in filename2:
                            logging.info('Blobs: {}'.format(blob.name))
                    modifiedurl.append(folder + bucket_name + '/' + url2[i])

            address = sender[x].replace('<', '')
            address1 = address.replace('>', '')
            address2 = re.findall('\S+@\S+', address1)

            a = {
                    'success': 'true',
                    'Sender': sender[x],
                    'send_mail_requester_query_param': 'emailServer='
                    + emailServer+'&'+'emailUser=' + emailUser+'&'
                    + 'emailPassword=' + emailPassword+'&'+'recipientAddress='
                    + address2[0]+'&'+'messageSubject=''Request Received''&'
                    + 'messageBody=''Hi, <br></br><br></br> Your request has '
                    + 'been received and undergoing an approval process.'
                    + '<br>We will contact you as soon as it is treated.'
                    + '</br><br></br><br></br>Thanks,<br />'
                    + 'Support Team',
                    'send_mail_requester_approved_query_param': 'emailServer='
                    + emailServer + '&' + 'emailUser=' + emailUser + '&'
                    + 'emailPassword=' + emailPassword + '&'
                    + 'recipientAddress='
                    + address2[0] + '&' + 'messageSubject=''Request Approved''&'
                    + 'messageBody=''Hi, <br></br><br></br> Your request has '
                    + 'been approved<br></br><br></br><br></br>Thanks,<br />'
                    + 'Support Team',
                    'send_mail_requester_rejected_query_param': 'emailServer='
                    + emailServer + '&' + 'emailUser=' + emailUser + '&'
                    + 'emailPassword=' + emailPassword + '&'
                    + 'recipientAddress=' + address2[0]
                    + '&' + 'messageSubject=''Request Rejected''&'
                    + 'messageBody=''Hi, <br></br><br></br> Your request has '
                    + 'been rejected<br></br><br></br><br></br>Thanks,'
                    + '<br />Support Team',
                    'Attachments': modifiedurl,
                    'ckan_params': {
                        'requestor_email': address2[0],
                        'server': emailServer,
                        'user': emailUser,
                        'password': emailPassword,
                        'attachments': modifiedurl,
                    }
                }
            allsender.append(a)
            os.remove(filePath)
            os.umask(saved_umask)
            shutil.rmtree(tmpdir)

        my_json_string = json.dumps(allsender)
        Response(my_json_string, mimetype='application/json')
        return my_json_string
