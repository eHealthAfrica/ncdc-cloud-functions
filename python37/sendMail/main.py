import email
import imaplib
import mailbox
import json
import smtplib
from flask import Response
from flask import Flask
from flask import jsonify
# import werkzeug
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import flash, request

app = Flask(__name__)

result = {"result" : "True", "body" : "The Mail is Sent"}

def sendMail(request):
    emailServer = request.args.get('emailServer')
    print(emailServer)
    emailPassword = request.args.get('emailPassword')
    print(emailPassword)
    emailUser = request.args.get('emailUser')
    print(emailUser)
    recipientAddress = request.args.get('recipientAddress')
    print(recipientAddress)
    messageSubject = request.args.get('messageSubject')
    print(messageSubject)
    messageBody = request.args.get('messageBody')
    print(messageBody)
    message = MIMEMultipart()
    message['From'] = emailUser
    message['To'] = recipientAddress
    message['Subject'] = messageSubject
    message.attach(MIMEText(messageBody, 'html'))
    session = smtplib.SMTP(emailServer, 587)
    session.starttls()
    session.login(emailUser, emailPassword)
    text = message.as_string()
    session.sendmail(emailUser, recipientAddress, text)
    session.quit()
    python2json = json.dumps(result)
    Response(python2json, mimetype='application/json')
    return python2json
