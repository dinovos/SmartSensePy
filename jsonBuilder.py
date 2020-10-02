import json
from datetime import datetime

dateTimeFormat = '%Y-%m-%d %H:%M:%S'

def createRedisEntry(sensor, message):
	entry = {
		"senzor_id" : sensor,
		"poruka" : message,
		"vrijeme" : datetime.now().strftime(dateTimeFormat)
		}
	message = json.dumps(entry)
	return message

def createRedisStudentEntry(tagid, action):
	entry = {
		"tag_id" : tagid,
		"akcija" : action,
		"vrijeme" : datetime.now().strftime(dateTimeFormat)
		}
	message = json.dumps(entry)
	return message

def createRedisLightEntry(tagid, message, action):
	entry = {
                "senzor_id" : tagid,
		"poruka" : message,
                "akcija" : action,
                "vrijeme" : datetime.now().strftime(dateTimeFormat)
                }
        message = json.dumps(entry)
        return message

def createPOSTmessage(sensor_id, message):
	entry = {
		"senzor_id": sensor_id,
		"poruka": message,
		"vrijeme": datetime.now().strftime(dateTimeFormat)
		}
	payload = json.dumps(entry)
	return payload
