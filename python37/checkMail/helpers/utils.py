import os
import pickle
import base64
import json
import email
import tempfile
import re
import datetime
import asyncio
import shutil

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from gcloud.aio.storage import Storage
from aiofile import AIOFile
import aiohttp

from flask import Response


def check_reviewer_mail(
    emailServer,
    emailUser,
    emailPassword,
    reviewers,
    monitors,
):
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    nomail = [{"success": "false", "Sender": "None", "Body": "None"}]
    sender = []
    allsender = []

    now = datetime.datetime.now()
    timenow = str(now.strftime("_%Y-%m-%d_%H:%M:%S"))
    char_list = ['%', '-', ':']
    comp_time = re.sub("|".join(char_list[:]), "", timenow)

    if os.path.exists('review_token.pickle'):
        with open('review_token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'review_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('review_token.pickle', 'wb') as token:
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
                    modifiedurl = []
                    arr = os.listdir(tmpdir)
                    for i in range(len(arr)):
                        filename = str(arr[i])
                        split_string = filename.split('.')
                        new_file = (
                            split_string[0] + comp_time
                            + '.' + split_string[1]
                        )
                        xpath = os.path.join(tmpdir, arr[i])
                        file_url = asyncio.run(
                            upload(xpath, f'reviews/{new_file}')
                        )
                        modifiedurl.append(
                            file_url
                        )

                separator = ' | '
                address = sender[x].replace('<', '').replace('>', '')
                address2 = re.findall('\S+@\S+', address)

                a = {
                    'success': 'true',
                    'Sender': sender[x],
                    'emailServer': emailServer,
                    'emailUser': emailUser,
                    'emailPassword': emailPassword,
                    'reviewers': reviewers,
                    'senderAddress': address2[0],
                    'send_mail_requester_review_query_param': 'emailServer='
                    + emailServer + '&emailUser=' + emailUser
                    + '&emailPassword=' + emailPassword + '&recipientAddress='
                    + address2[0] + '&monitors=' + monitors
                    + '&messageSubject=''Request Received''&'
                    + 'messageBody=''Hi, <br></br><br></br> Your request has '
                    + 'been received and is being reviewed.'
                    + '<br>We will contact you as soon as it has a response.'
                    + '</br><br></br><br></br>Thanks,<br />'
                    + 'Support Team',
                    'Attachments': separator.join(modifiedurl),
                }
                allsender.append(a)
                # Ensure the file is read/write by the creator only
                saved_umask = os.umask(0o77)
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
                print('An error occurred processing review mail: ', error)

        my_json_string = json.dumps(allsender)
        Response(my_json_string, mimetype='application/json')

        return my_json_string


async def async_upload_to_bucket(blob_name, file_obj):
    with open('parameters.json') as json_file:
        params = json.load(json_file)

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