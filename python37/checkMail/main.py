import email
import imaplib
import mailbox
import json
import shutil
import os
from OpenSSL import crypto
from OpenSSL import SSL
from backports import ssl
from imapclient import IMAPClient
from flask import Response
from flask import Flask
from flask import jsonify
import tempfile
import io
import re
import logging
from io import BytesIO
import datetime
from google.cloud import storage

result = {"Result": "Succesfully Uploaded","Source": "GCP Storage"}

with open('parameters.json') as json_file:

    params = json.load(json_file)

# import werkzeug
from flask import flash, request

app = Flask(__name__)

nomail = [{"success": "false","Sender": "None", "Body": "None"}]


def checkMail(request):
        now = datetime.datetime.now()
        timenow = str(now.strftime("_%Y-%m-%d_%H:%M:%S"))
        char_list = ['%', '-',':']
        comp_time = re.sub("|".join(char_list[:]), "", timenow)
        storage_client = storage.Client.from_service_account_json("project.json")
        emailServer = request.args.get('emailServer')
        emailPassword = request.args.get('emailPassword')
        emailUser = request.args.get('emailUser')
        recipientAddress = request.args.get('recipientAddress')
        sender = []
        
        # allfiles =[]
        allsender =[]
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        imapObj = IMAPClient(emailServer, ssl=True, ssl_context=context)
        mail = imaplib.IMAP4_SSL(emailServer)
        mail.login(emailUser, emailPassword)
        mail.list()
        mail.select('inbox')
        result, data = mail.uid('search', None, "UNSEEN") # (ALL/UNSEEN)
        j = len(data[0].split())
        nomail_Json = json.dumps(nomail)
        Response(nomail_Json, mimetype='application/json')
        # print(j)
        if(j==0):
                return nomail_Json
        else:
                for x in range(j):
                        
                        latest_email_uid = data[0].split()[x]
                        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
                        latest_email_uid = data[0].split()[x]
                        raw_email = email_data[0][1]
                        raw_email_string = raw_email.decode('utf-8')
                        email_message = email.message_from_string(raw_email_string)
                        # Ensure the file is read/write by the creator only
                        saved_umask = os.umask(0o77)
                        # Header Details
                        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
                        email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
                        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
                        sender.append(email_from)
                        # print("mysender",sender)

                        tmpdir = tempfile.mkdtemp()
                        for part in email_message.walk():
                                if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True)
                                        # print(body)
                                        #
                                if part.get_content_maintype() == 'multipart':
                                        continue
                                if part.get('Content-Disposition') is None:
                                        continue
                                fileName = part.get_filename()
                                # print(fileName)

                                if bool(fileName):
                                        filePath = os.path.join(tmpdir, fileName)
                                        # print(filePath)
                                if not os.path.isfile(filePath) :
                                        fp = open(filePath, 'wb')
                                        fp.write(part.get_payload(decode=True))
                                        fp.close()
                                        subject = str(email_message).split("Subject: ", 1)[1].split("\nTo:", 1)[0]
                                        # print('Downloaded "{file}" from email titled "{subject}" with UID {uid}.'.format(file=fileName, subject=subject, uid=latest_email_uid.decode('utf-8')))
                                # url = []
                                url2 = []
                                extension =[]
                                modifiedurl =[]

                                bucket = storage_client.get_bucket(params[0]["bucket_name"])
                                folder = params[0]["folder"]
                                
                                arr = os.listdir(tmpdir)
                                # print(arr)

                                for i in range (len(arr)):
                                    filename = str(arr[i-1])
                                    split_string = filename.split('.')
                                    new_file = split_string[0]+comp_time+'.'+split_string[1]
                                    extension1 = split_string[1]
                                    extension.append(extension1.upper()+" "+"File")
                                    url2.append(new_file)
                                    blob = bucket.blob(new_file)
                                    xpath = os.path.join(tmpdir,arr[i])
                                    with open(xpath, 'rb') as f:
                                            blob.upload_from_file(f)
                                            filename2 = list(bucket.list_blobs(prefix=''))
                                            for blob in filename2:
                                                logging.info('Blobs: {}'.format(blob.name))
                                                destination_uri = '{}/{}'.format(folder, blob.name)
                                                # if(destination_uri not in url):
                                                #         url.append(destination_uri)
                                                # my_json = json.dumps(url)
                                                # print(filename2)
                                    modifiedurl.append(folder+"/"+url2[i])
                                       
                        # print(extension)
                        # print(modifiedurl)                           
                        # print(url2) 
                        # separator = ' , '  
                        address = sender[x].replace('<','')
                        address1 = address.replace('>','')
                        address2 = re.findall('\S+@\S+', address1)
                        # print(address2)
                        # body_htmlpage1 = "Hi,<br /><br />Task has been assigned to you.<br></br> Please go through the links"
                        # body_htmlpage2 = "and Approve or Reject the Task using below buttons :<br/><br></br></br> <a href="+params[0]["ApproveOrReject"]+"?decision=true><button>Approve</button></a> <a href="+params[0]["ApproveOrReject"]+"""?decision=false><button style="margin-left: 20px">Reject</button></a><br/><br />Thanks,<br />Support Team"""
                        # body_html = body_htmlpage1+" "+separator.join(modifiedurl)+" "+body_htmlpage2 
                        a = {"success": "true","Sender":sender[x], "send_mail_requester_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+address2[0]+"&"+"messageSubject=""Request Accepted""&"+"messageBody=""Hi, <br></br><br></br> Your request has been Accepted<br></br><br></br><br></br>Thanks,<br />Support Team",
                                                 "send_mail_requester_approved_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+address2[0]+"&"+"messageSubject=""Request Approved""&"+"messageBody=""Hi, <br></br><br></br> Your request has been approved<br></br><br></br><br></br>Thanks,<br />Support Team",
                                                 "send_mail_requester_rejected_query_param":"emailServer="+emailServer+"&"+"emailUser="+emailUser+"&"+"emailPassword="+emailPassword+"&"+"recipientAddress="+address2[0]+"&"+"messageSubject=""Request Rejected""&"+"messageBody=""Hi, <br></br><br></br> Your request has been rejected<br></br><br></br><br></br>Thanks,<br />Support Team","Attachments":modifiedurl}
                # print(sender[y])
                        allsender.append(a)
                                # allfiles.clear()
                        os.remove(filePath)
                        os.umask(saved_umask)
                        shutil.rmtree(tmpdir)
                        # Response(my_json, mimetype='application/json')
                # print("value of i is :", j)
                # for y in range(j):
                    
                        # address = sender[y].replace('<','')
                        # address1 = address.replace('>','')
                        # address2 = re.findall('\S+@\S+', address1)
                        # print(address2)
                        # body_htmlpage = """Hi,<br /><br />Task has been assigned to you.<br></br> Please go through the links <a href=https://storage.cloud.google.com/attached-mail-file/myfileGCP0>PDF File</a> and <a href= https://storage.cloud.google.com/attached-mail-file/myfileGCP1>XLS File</a> and Approve or Reject the Task using below buttons :<br/><br></br></br> <a href=https://us-central1-quick-bonfire-278608.cloudfunctions.net/approveorReject?approve=approved><button>Approve</button></a> <a href=https://us-central1-quick-bonfire-278608.cloudfunctions.net/approveorReject?approve=rejected><button style="margin-left: 20px">Reject</button></a><br/><br />Thanks,<br />Support Team"""

                
                my_json_string = json.dumps(allsender)
                # print(my_json_string)
                Response(my_json_string, mimetype='application/json')
                # print("upload Complete")
                # print(destination_uri)
                # print(url)
                return my_json_string
