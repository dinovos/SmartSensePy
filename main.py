##IMPORTED MODULES
from datetime import datetime
from mfrc522 import SimpleMFRC522
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import signal
import sys
import random
import json

import jsonBuilder
import redis_conn
import mysql_conn
import restClient

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#SETUP MESSAGES
gasMessages = ['Osjeti se plin!', 'Osjeti se PLIN u prostoriji!', 'Plinovi u zraku!', 'Curenje plina!']
flameMessages = ['VATRA detektirana', 'Vidim vatru!', 'Ovdje nesto gori!?!', 'Pozar!!!']
photoMessages = ['Ovdje je pao mrak?!','Nista se ne vidi','Smanjena vidljivost u prostoriji','Upaliti svjetlo molim']
rainMessages = ['VODA detektirana','Poplava!!','VODA u server sobi!!', 'Pod je mokar!!']
pirMessages = ['Nesto se mice!','Kretanje u dvorani detektirano','Vidim kretanje!']

#SETUP READER OBJECT FOR RFID
reader = SimpleMFRC522()

#CHECK REDIS DATABASE CONNECTION
print('\n*******************************************************')
redis_conn.checkConnection()

#CHECK MYSQL DATABASE CONNECTION
print('*******************************************************')
mysql_conn.checkConnection()

#GAS SENSOR GPIO
GAS_GPIO = 17
GPIO.setup(GAS_GPIO, GPIO.IN)
print('*******************************************************')
print('Inicijalizacija senzor plina')
print('GPIO ==> {0:5d}').format(GAS_GPIO)
print('*******************************************************')
time.sleep(.100)

#RAIN SENSOR GPIO
RAIN_GPIO = 5
GPIO.setup(RAIN_GPIO, GPIO.IN)
print('Inicijalizacija senzora kise')
print('GPIO ==> {0:5d}').format(RAIN_GPIO)
print('*******************************************************')
time.sleep(.100)

#FLAME SENSOR GPIO
FLAME_GPIO = 6
GPIO.setup(FLAME_GPIO, GPIO.IN)
print('Inicijalizacija senzor plamena')
print('GPIO ==> {0:5d}').format(FLAME_GPIO)
print('*******************************************************')
time.sleep(.100)

#PHOTOSENSITIVE SENSOR GPIO
PHOTO_GPIO = 16
GPIO.setup(PHOTO_GPIO, GPIO.IN)
print('Inicijalizacija foto osjetljivi senzor')
print('GPIO ==> {0:5d}').format(PHOTO_GPIO)
print('*******************************************************')
time.sleep(.100)

#PIR SENSOR GPIO
PIR_GPIO = 20
GPIO.setup(PIR_GPIO, GPIO.IN)
print('Inicijalizacija senzor pokreta')
print('GPIO ==> {0:5d}').format(PIR_GPIO)
print('*******************************************************')
time.sleep(.100)

#RELAY GPIO
RELAY_GPIO = 21
GPIO.setup(RELAY_GPIO, GPIO.OUT)
GPIO.output(RELAY_GPIO, 1)
upaljeno = False
print('Inicijalizacija elektromagnetne sklopke')
print('GPIO ==> {0:5d}').format(RELAY_GPIO)
print('*******************************************************')
time.sleep(.100)

#SENSOR START
print('Senzori uspjesno inicijalizirani')
print('*******************************************************')
print('Program pokrenut')
print('Za izlaz pritisni CTRL+C')
print('*******************************************************')

#CALLBACK FUNCTION FOR GAS SENSOR, id = 6
def gas_sensor_callback(GAS_GPIO):
	poruka = random.choice(gasMessages)
	print('\nSenzor plina: ' + poruka)
	redis_conn.writeToDb('Senzor_plin', jsonBuilder.createRedisEntry(6,poruka))
	mysql_conn.insertAlarm(6, poruka)
	payload = jsonBuilder.createPOSTmessage(6, poruka)
	print("Server response: {0}").format(restClient.sendPOSTMessage(payload))

#CALLBACK FUNCTION FOR RAIN SENSOR, id = 7
def rain_sensor_callback(RAIN_GPIO):
	poruka = random.choice(rainMessages)
	print('\nSenzor vode: ' + poruka)
	redis_conn.writeToDb('Senzor_voda', jsonBuilder.createRedisEntry(7,poruka))
	mysql_conn.insertAlarm(7, poruka)
	payload = jsonBuilder.createPOSTmessage(7, poruka)
        print("Server response: {0}").format(restClient.sendPOSTMessage(payload))

#CALLBACK FUNCTION FOR FLAME SENSOR, id = 8
def flame_sensor_callback(FLAME_GPIO):
	poruka = random.choice(flameMessages)
	print('\nSenzor vatre: ' + poruka)
	redis_conn.writeToDb('Senzor_vatra', jsonBuilder.createRedisEntry(8,poruka))
	mysql_conn.insertAlarm(8, poruka)
	payload = jsonBuilder.createPOSTmessage(8, poruka)
        print("Server response: {0}").format(restClient.sendPOSTMessage(payload))

#CALLBACK FUNCTION FOR PHOTOSENSITIVE SENSOR, id = 3
def photo_sensor_callback(PHOTO_GPIO):
	poruka = random.choice(photoMessages)
	print('\nFoto senzor: ' + poruka)
	redis_conn.writeToDb('Senzor_foto', jsonBuilder.createRedisEntry(3,poruka))
	mysql_conn.insertAlarm(3, poruka)
	payload = jsonBuilder.createPOSTmessage(3, poruka)
        print("Server response: {0}").format(restClient.sendPOSTMessage(payload))

#CALLBACK FUNCTION FOR PIR SENSOR, id = 4
def pir_sensor_callback(PIR_GPIO):
	poruka = random.choice(pirMessages)
        print('\nSenzor pokreta: ' + poruka)
	mysql_conn.insertAlarm(4, poruka)
	payload = jsonBuilder.createPOSTmessage(4, poruka)
        print("Server response: {0}").format(restClient.sendPOSTMessage(payload))
	redis_entry = redis_conn.getFromDb("Senzor_pokreta")
	if upaljeno == False:
		powerON()
		message = jsonBuilder.createRedisLightEntry(4, poruka, "UPALJENO")
		redis_conn.writeToDb("Senzor_pokreta", message)

	elif upaljeno == True:
		powerOFF()
		if redis_entry is not None:
			new_message = jsonBuilder.createRedisLightEntry(4, poruka, "UGASENO")
			data = json.loads(redis_entry)
			time_from = data["vrijeme"]
			new_data = json.loads(new_message)
			time_to = new_data["vrijeme"]
			razlika = datetime.strptime(time_to, '%Y-%m-%d %H:%M:%S') - datetime.strptime(time_from, '%Y-%m-%d %H:%M:%S')
			mysql_conn.insertLightLog(4, razlika, time_from, time_to)

#FUNCTION TO POWER ON RELAY
def powerON():
	upaljeno = True
	GPIO.output(RELAY_GPIO, 0)

#FUNCTION TO POWER OFF RELAY
def powerOFF():
	upaljeno = False
	GPIO.output(RELAY_GPIO, 1)

#FUNCTION USED TO READ TAG
def readTag():
	id, text = reader.read()
	print('\nProcitan tag id: {0} ==> Payload: {1}').format(id, text)
	if mysql_conn.checkStudentTagId(id) == True:
		message = redis_conn.getFromDb(id)
		if message is None:
			data = jsonBuilder.createRedisStudentEntry(id, "ULAZ")
			print('\n'+data)
			redis_conn.writeToDb(id, data)
		else:
			data = jsonBuilder.createRedisStudentEntry(id, "IZLAZ")
			print('\n'+data)
			redis_conn.writeToDb(id, data)
			entry = json.loads(message)
			from_time = entry["vrijeme"]
			entry_data = json.loads(data)
			to_time = entry_data["vrijeme"]
			razlika = datetime.strptime(to_time, '%Y-%m-%d %H:%M:%S') - datetime.strptime(from_time, '%Y-%m-%d %H:%M:%S')
			mysql_conn.insertStudentLog(id, 2, razlika, from_time, to_time)
			redis_conn.deleteFromDb(id)
	time.sleep(2)


#CALLBACK FUNCTION FOR KEYBOARD INTERRUPTION
def keyboardInterruptHandler(signal, frame):
        print('\nPrekid sa tipkovnice')
        mysql_conn.closeConnection()
        print('\nBye bye ID:{}').format(signal)
        GPIO.cleanup()
        sys.exit(0)

#DETECT GAS
GPIO.add_event_detect(GAS_GPIO, GPIO.RISING, bouncetime=10000)
GPIO.add_event_callback(GAS_GPIO, gas_sensor_callback)

#DETECT RAIN
GPIO.add_event_detect(RAIN_GPIO, GPIO.RISING, bouncetime=10000)
GPIO.add_event_callback(RAIN_GPIO, rain_sensor_callback)

#DETECT FLAME
GPIO.add_event_detect(FLAME_GPIO, GPIO.RISING, bouncetime=10000)
GPIO.add_event_callback(FLAME_GPIO, flame_sensor_callback)

#DETECT PHOTO
GPIO.add_event_detect(PHOTO_GPIO, GPIO.FALLING, bouncetime=50000)
GPIO.add_event_callback(PHOTO_GPIO, photo_sensor_callback)

#DETECT MOVEMENT - PIR SENSOR
GPIO.add_event_detect(PIR_GPIO, GPIO.BOTH, bouncetime=300000)
GPIO.add_event_callback(PIR_GPIO, pir_sensor_callback)

#DETECT KEYBOARD INTERRUPTION
signal.signal(signal.SIGINT, keyboardInterruptHandler)

if __name__ == "__main__":
	while True:
		try:
                	readTag()
		finally:
			pass

