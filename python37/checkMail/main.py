import email
import json
import shutil
import os
from flask import Response
import tempfile
import re
import datetime
import asyncio

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import base64

from gcloud.aio.storage import Storage
from aiofile import AIOFile
import aiohttp

result = {"Result": "Succesfully Uploaded", "Source": "GCP Storage"}

with open('parameters.json') as json_file:
    params = json.load(json_file)

nomail = [{"success": "false", "Sender": "None", "Body": "None"}]


def checkMail(request):
    now = datetime.datetime.now()
    timenow = str(now.strftime("_%Y-%m-%d_%H:%M:%S"))
    char_list = ['%', '-', ':']
    comp_time = re.sub("|".join(char_list[:]), "", timenow)
    emailServer = request.args.get('emailServer')
    emailPassword = request.args.get('emailPassword')
    emailUser = request.args.get('emailUser')
    approvers = request.args.get('approvers')
    sender = []
    allsender = []

    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = None
    unread_messages_res = {}
    try:
        service = build('gmail', 'v1', credentials=creds)
        unread_messages_res = service.users().messages() \
            .list(userId='me', labelIds=['UNREAD']).execute()
    except Exception as error:
        print('An error occurred reading mail: ', error)

    unread_messages_ids = unread_messages_res.get('messages', [])

    nomail_Json = json.dumps(nomail)
    Response(nomail_Json, mimetype='application/json')
    msg_count = len(unread_messages_ids)
    if(msg_count == 0):
        return nomail_Json
    else:
        for x in range(msg_count):
            msg = unread_messages_ids[x]
            message = ''
            try:
                if not service:
                    service = build('gmail', 'v1', credentials=creds)
                message = service.users().messages() \
                    .get(userId='me', id=msg['id'], format='raw').execute()
                raw_email_string = base64.urlsafe_b64decode(
                    message['raw'].encode('ASCII')
                )
                if isinstance(raw_email_string, bytes):
                    raw_email_string = raw_email_string.decode('utf-8')
                email_message = email.message_from_string(
                    raw_email_string
                )
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
                    else:
                        modifiedurl = ""
                        filePath = tmpdir
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
                    modifiedurl = []
                    template_url = ''
                    arr = os.listdir(tmpdir)
                    for i in range(len(arr)):
                        filename = str(arr[i])
                        split_string = filename.split('.')
                        new_file = (
                            split_string[0] + comp_time
                            + '.' + split_string[1]
                        )
                        url2.append(new_file)
                        xpath = os.path.join(tmpdir, arr[i])
                        file_url = asyncio.run(upload(xpath, new_file))
                        # o = parse.urlparse(file_url)
                        # o_url = o._replace(path=parse.quote(o.path))
                        attachment_url = file_url
                        modifiedurl.append(
                            attachment_url
                        )
                        checker_link = url2[i].lower()
                        if 'xls' in checker_link and \
                            'request' in checker_link and \
                                'ncdc' in checker_link:
                            template_url = attachment_url

                separator = ' | '
                address = sender[x].replace('<', '')
                address1 = address.replace('>', '')
                address2 = re.findall('\S+@\S+', address1)

                a = {
                    'success': 'true',
                    'Sender': sender[x],'emailServer':emailServer,
                    'emailUser':emailUser,'emailPassword':emailPassword,
                    'approvers': approvers,
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
                    + address2[0] + '&'
                    + 'messageSubject=''Request Approved''&'
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
                    'Attachments': separator.join(modifiedurl),
                    'ckan_params': {
                        'requestor_email': address2[0],
                        'server': emailServer,
                        'user': emailUser,
                        'password': emailPassword,
                        'attachments': [template_url, ],
                    }
                }
                allsender.append(a)
                os.umask(saved_umask)
                shutil.rmtree(tmpdir)
                _ = service.users().messages() \
                    .modify(
                        userId='me', id=msg['id'],
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
            except Exception as error:
                import traceback
                traceback.print_exc()
                print('An error occurred processing mail: ', error)

        my_json_string = json.dumps(allsender)
        Response(my_json_string, mimetype='application/json')

        return my_json_string


async def async_upload_to_bucket(blob_name, file_obj):
    async with aiohttp.ClientSession() as session:
        storage = Storage(service_file='project.json', session=session)

        status = await storage.upload(
            params["bucket_name"],
            f'uploads/{blob_name}',
            file_obj,
            timeout=60,
        )
        return status['mediaLink']


async def upload(file_path, file_name):
    async with AIOFile(file_path, mode='rb') as afp:
        f = await afp.read()
        url = await async_upload_to_bucket(file_name, f)
        return url
