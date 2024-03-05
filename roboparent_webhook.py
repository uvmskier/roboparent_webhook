#ports
#5001 for webhook listener
#5002 for custom exporter

#imports for logging and json handling
import sys
import logging
from pythonjsonlogger import jsonlogger
import json
from flask import Flask, request, make_response
import socket

import pythonmysql

import datetime
from datetime import datetime,date
import requests
import urllib, hmac,hashlib
import dotenv, os

from slack_sdk import signature

if socket.gethostname() == 'nuc1':
    dotenv.load_dotenv('/home/brian/python-scripts/secrets.env')
else:
    dotenv.load_dotenv('secrets.env')

slack_signing_secret = os.getenv('SLACK_SIGNING_SECRET')

logger = logging.getLogger(__name__)

#stdout = logging.StreamHandler(stream=sys.stdout)
if socket.gethostname() == 'nuc1':
    fileHandler = logging.FileHandler(filename = '/home/brian/roboparent_logs/roboparentEvents.log')
else:
    fileHandler = logging.FileHandler(filename = 'roboparentEvents.log')
format = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(message)s',
    rename_fields ={"asctime": "timestamp"}
)

jsonlogger.JsonFormatter.default_msec_format = '%s.%03d'

fileHandler.setFormatter(format)
logging.basicConfig(level=logging.INFO)
logger.addHandler(fileHandler)

#import flask for web hook
app = Flask(__name__)

@app.route('/status', methods=['GET'])
def status():
    if request.method == 'GET':
        return "Success - listener is up"

def parseSlackMessage(event):
    jsonObjectToLog = {}
    if event == "SuccessfulCleanupEthan":
        jsonObjectToLog['eventMessage'] = 'successful cleanup'
        jsonObjectToLog['kid'] = 'Ethan'
        jsonObjectToLog['event'] = 'SuccessfulCleanup'
        jsonObjectToLog['roomCleanStatus'] = 1
        return jsonObjectToLog
    elif event == "FailedCleanupEthan":
        jsonObjectToLog['eventMessage'] = 'failed cleanup'
        jsonObjectToLog['kid'] = 'Ethan'
        jsonObjectToLog['event'] = 'FailedCleanup'
        jsonObjectToLog['roomCleanStatus'] = 0
        return jsonObjectToLog
    elif event == "DismissedCleanupEthan":
        jsonObjectToLog['eventMessage'] = 'dismissed cleanup'
        jsonObjectToLog['kid'] = 'Ethan'
        jsonObjectToLog['event'] = 'DismissedCleanup'
        jsonObjectToLog['roomCleanStatus'] = 1
        return jsonObjectToLog
    elif event == "SuccessfulCleanupBenjamin":
        jsonObjectToLog['eventMessage'] = 'successful cleanup'
        jsonObjectToLog['kid'] = 'Benjamin'
        jsonObjectToLog['event'] = 'SuccessfulCleanup'
        jsonObjectToLog['roomCleanStatus'] = 1
        return jsonObjectToLog
    elif event == "FailedCleanupBenjamin":
        jsonObjectToLog['eventMessage'] = 'failed cleanup'
        jsonObjectToLog['kid'] = 'Benjamin'
        jsonObjectToLog['event'] = 'FailedCleanup'
        jsonObjectToLog['roomCleanStatus'] = 0
        return jsonObjectToLog
    elif event == "DismissedCleanupBenjamin":
        jsonObjectToLog['eventMessage'] = 'dismissed cleanup'
        jsonObjectToLog['kid'] = 'Benjamin'
        jsonObjectToLog['event'] = 'DismissedCleanup'
        jsonObjectToLog['roomCleanStatus'] = 1
        return jsonObjectToLog
    else:
        jsonObjectToLog['kid'] = 'Error Parsing Slack Payload'
        jsonObjectToLog['event'] = 'Error Parsing Slack Payload'
        return jsonObjectToLog

def roboparentPostReply(kid,event,slackuser,eventMessage):
    message = f"The user {slackuser} updated the room status for {kid} to {eventMessage}."

    jsonMessage = json.dumps({"text": message})

    if(kid=="Ethan"):
        url = os.getenv('ETHAN_SLACK_URL')   
    elif(kid=="Benjamin"):
        url = os.getenv('BENJAMIN_SLACK_URL')

    my_response = requests.post(url,data=jsonMessage)

    foo = 'bar'

@app.route('/roboparentEvent', methods=['POST'])
def roboparentEvent():
    #########authorize the request############
    timestamp = request.headers['X-Slack-Request-Timestamp']
    slack_payload = request.form

    signatureVerifier = signature.SignatureVerifier(slack_signing_secret,signature.Clock())

    calculated_signature = signatureVerifier.generate_signature(timestamp=timestamp,body=slack_payload)

    isValid = signatureVerifier.is_valid(slack_payload,timestamp,calculated_signature)

    if (isValid == False):
        return 'Unauthorized', 400
    #########end authorize the request########

    if request.method == 'POST':
        payload = request.form.get('payload')
        jsonData = json.loads(payload)
        jsonObjectToLog = parseSlackMessage(jsonData['actions'][0]['value'])
        jsonObjectToLog['slackuser'] = jsonData['user']['name']

        logger.info('Event Received', extra=jsonObjectToLog)
    
        mySQLObject = pythonmysql.PythonMySQL()
        now = datetime.now()
        mySQLObject.insertEvent(jsonObjectToLog['kid'],now,jsonObjectToLog['event'],jsonObjectToLog['slackuser'])
        roboparentPostReply(jsonObjectToLog['kid'],jsonObjectToLog['event'],jsonObjectToLog['slackuser'],jsonObjectToLog['eventMessage'])
        return "Success"

@app.route('/snoozekid', methods=['POST'])
def snoozekid():
    #########authorize the request############
    timestamp = request.headers['X-Slack-Request-Timestamp']
    slack_payload = request.form

    signatureVerifier = signature.SignatureVerifier(slack_signing_secret,signature.Clock())

    calculated_signature = signatureVerifier.generate_signature(timestamp=timestamp,body=slack_payload)

    isValid = signatureVerifier.is_valid(slack_payload,timestamp,calculated_signature)

    if (isValid == False):
        return 'Unauthorized', 400
    #########end authorize the request########
    
    if request.method == 'POST':
        #payload = request.form.get('payload')
        payload = request.form.to_dict(flat=False)

        print(payload)

        text = payload['text'][0]
        if text == '':
             return "Error - kid and date string missing"
        
        x = text.split()
        kid = x[0]
        dateInput = x[1]

        slack_user = payload['user_name'][0]

        if(kid not in {"Ethan", "Benjamin"}):
            return "Invalid kid name"
        try:
            dateObject = datetime.strptime(dateInput,"%Y-%m-%d")
        except:
            return "Invalid date - date must be YYYY-MM-DD"
        if (dateObject <= datetime.now()):
            return "Invalid date - date must be in the future"
        
        mySQLObject = pythonmysql.PythonMySQL()
        mySQLObject.setSnooze(kid,dateInput,slack_user)

        responseObject = {}
        responseObject['response_type'] = 'in_channel'
        responseObject['text'] = "{} snoozed until {}".format(kid,dateInput)
        jsonObject = json.dumps(responseObject)

        requests.post(payload['response_url'][0], jsonObject)
        response = make_response("Request successfully received",200)
        return response
@app.route('/getsnoozestatus', methods = ['POST'])
def getsnoozestatus():
        #########authorize the request############
        timestamp = request.headers['X-Slack-Request-Timestamp']
        slack_payload = request.form

        signatureVerifier = signature.SignatureVerifier(slack_signing_secret,signature.Clock())

        calculated_signature = signatureVerifier.generate_signature(timestamp=timestamp,body=slack_payload)

        isValid = signatureVerifier.is_valid(slack_payload,timestamp,calculated_signature)

        if (isValid == False):
            return 'Unauthorized', 400
        #########end authorize the request########

        if request.method == 'POST':
            payload = request.form.to_dict(flat=False)
        print(payload)

        kid = payload['text'][0]
        if kid == '':
             return "Error - kid string missing"

        if(kid not in {"Ethan", "Benjamin"}):
            return "Invalid kid name"

        mySQLObject = pythonmysql.PythonMySQL()
        snoozeStatus = mySQLObject.getSnoozeStatus(kid)

        if(snoozeStatus['snoozeStatus'] == False):
            return "{} is not currently snoozed".format(kid)

        responseObject = {}
        responseObject['response_type'] = 'in_channel'
        responseObject['text'] = "{} snoozed until {}".format(kid,date.strftime(snoozeStatus['snoozeDate'],"%Y-%m-%d"))
        jsonObject = json.dumps(responseObject)

        requests.post(payload['response_url'][0], jsonObject)
        response = make_response("Request successfully received",200)
        return response

@app.route('/removesnooze', methods = ['POST'])
def removesnooze():
    #########authorize the request############
        timestamp = request.headers['X-Slack-Request-Timestamp']
        slack_payload = request.form

        signatureVerifier = signature.SignatureVerifier(slack_signing_secret,signature.Clock())

        calculated_signature = signatureVerifier.generate_signature(timestamp=timestamp,body=slack_payload)

        isValid = signatureVerifier.is_valid(slack_payload,timestamp,calculated_signature)

        if (isValid == False):
            return 'Unauthorized', 400
    #########end authorize the request########

        if request.method == 'POST':
            payload = request.form.to_dict(flat=False)
        print(payload)

        kid = payload['text'][0]
        if kid == '':
             return "Error - kid string missing"

        if(kid not in {"Ethan", "Benjamin"}):
            return "Invalid kid name"

        slack_user = payload['user_name'][0]

        mySQLObject = pythonmysql.PythonMySQL()

        snoozeStatus = mySQLObject.getSnoozeStatus(kid)

        mySQLObject.removeSnooze(kid,slack_user)

        if(snoozeStatus['snoozeStatus'] == False):
            return "{} is not currently snoozed".format(kid)

        responseObject = {}
        responseObject['response_type'] = 'in_channel'
        responseObject['text'] = "{} snooze removed".format(kid)
        jsonObject = json.dumps(responseObject)

        requests.post(payload['response_url'][0], jsonObject)
        response = make_response("Request successfully received",200)
        return response

@app.route('/testroute', methods = ['POST'])
def testroute():
    #########authorize the request############
    timestamp = request.headers['X-Slack-Request-Timestamp']
    slack_payload = request.form

    signatureVerifier = signature.SignatureVerifier(slack_signing_secret,signature.Clock())

    calculated_signature = signatureVerifier.generate_signature(timestamp=timestamp,body=slack_payload)

    isValid = signatureVerifier.is_valid(slack_payload,timestamp,calculated_signature)

    if (isValid == False):
        return 'Unauthorized', 400
    else:
        print("hooray")
    return '', 200
    #########end authorize the request########

@app.route('/getroomstatus', methods = ['POST'])
def getroomstatus():
    #########authorize the request############
    timestamp = request.headers['X-Slack-Request-Timestamp']
    slack_payload = request.form

    signatureVerifier = signature.SignatureVerifier(slack_signing_secret,signature.Clock())

    calculated_signature = signatureVerifier.generate_signature(timestamp=timestamp,body=slack_payload)

    isValid = signatureVerifier.is_valid(slack_payload,timestamp,calculated_signature)

    if (isValid == False):
        return 'Unauthorized', 400
    
    #########end authorize the request########

    if request.method == 'POST':
        payload = request.form.to_dict(flat=False)

    kid = payload['text'][0]
    if kid == '':
         return "Error - kid string missing"

    if(kid not in {"Ethan", "Benjamin"}):
        return "Invalid kid name"
    
    mySQLObject = pythonmysql.PythonMySQL()

    room_status = mySQLObject.getRoomStatus(kid)

    if room_status == 0:
      status = "Not picked up"
    elif room_status == 1:
      status = "Successful Cleanup"
    elif room_status == 2:
      status = "Snooze"

    responseObject = {}
    responseObject['response_type'] = 'in_channel'
    responseObject['text'] = "Status is {}".format(status)
    jsonObject = json.dumps(responseObject)

    requests.post(payload['response_url'][0], jsonObject)
    response = make_response("Request successfully received",200)
    return response

app.run(host='0.0.0.0', port=5001)