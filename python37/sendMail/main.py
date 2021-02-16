import email
import imaplib
import mailbox
import json
import smtplib
import pickle
import base64
from flask import Response
from flask import Flask
from flask import jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import flask
import socket

import os.path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

result = {"result": "True", "body": "The Mail is Sent"}
MAX_RETRIES = 3


def sendMail(request, count=0):
    is_encoded = request.args.get('encoded')
    emailUser = request.args.get('emailUser')
    recipientAddress = request.args.get('recipientAddress')
    messageSubject = request.args.get('messageSubject')
    messageBody = request.args.get('messageBody')
    monitors = request.args.get('monitors', '')

    if is_encoded:
        messageBody = base64.urlsafe_b64decode(messageBody).decode('utf-8')
    message = MIMEMultipart()
    message['From'] = emailUser
    message['To'] = recipientAddress
    message['Subject'] = messageSubject
    if monitors:
        message['CC'] = monitors
    message.attach(MIMEText(messageBody, 'html'))
    API_msg = {'raw': base64.urlsafe_b64encode(
        message.as_string().encode('utf-8')
    ).decode('utf-8')}

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

    try:
        service = build('gmail', 'v1', credentials=creds)
        r_msg = (
                    service.users().messages().send(
                        userId="me",
                        body=API_msg
                    ).execute()
                )
        result['msg'] = r_msg

    except socket.timeout:
        count = count + 1
        print(f'Socket Timeout Retrying ... {count}')
        if count < MAX_RETRIES:
            sendMail(request, count)
        else:
            result['result'] = 'False'
    except Exception as error:
        print(f'An error occurred: {error}')
        result['result'] = 'False'

    return flask.make_response(json.dumps(result))
