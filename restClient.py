import requests

url = "http://192.168.0.12:8084/SmartSense/webresources/message"

def sendPOSTMessage(message):
	try:
		r = requests.post(url, message)
		return r.text
	except:
		print("Neuspjesno slanje POST-a")
