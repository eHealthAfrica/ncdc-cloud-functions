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

import os.path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

result = {"result": "True", "body": "The Mail is Sent"}


def sendMail(request):
    is_encoded = request.args.get('encoded')
    emailUser = request.args.get('emailUser')
    recipientAddress = request.args.get('recipientAddress')
    messageSubject = request.args.get('messageSubject')
    messageBody = request.args.get('messageBody')
    if is_encoded:
        messageBody = base64.urlsafe_b64decode(messageBody).decode('utf-8')
        print(messageBody)
    message = MIMEMultipart()
    message['From'] = emailUser
    message['To'] = recipientAddress
    message['Subject'] = messageSubject
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

    service = build('gmail', 'v1', credentials=creds)

    try:
        r_msg = (
                    service.users().messages().send(
                        userId="me",
                        body=API_msg
                    ).execute()
                )
        print(f'Message Id: {r_msg["id"]}')
        result['msg'] = r_msg
    except HttpError as error:
        print(f'An error occurred: {error}')
        result['result'] = 'False'

    return flask.make_response(json.dumps(result))
