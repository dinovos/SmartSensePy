from datetime import datetime
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import sys
import signal
import json
import random

import jsonBuilder
import redis_conn
import mysql_conn
import restClient

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

tempMessages = ['Vruce ili hladno?!', 'Upozorenje na temperaturu', 'TEMPERATURA izvan normale']
humMessages = ['Razina vlage!','Upozorenje na vlagu','VLAGA izvan normale','']

#CHECK REDIS DATABASE CONNECTION
print('\n*******************************************************')
redis_conn.checkConnection()

#CHECK MYSQL DATABASE CONNECTION
print('*******************************************************')
mysql_conn.checkConnection()

#TEMPERATURE & HUMIDITY GPIO
TEMP_GPIO = 23
GPIO.setup(TEMP_GPIO, GPIO.IN)
print('*******************************************************')
print('Inicijalizacija senzora temperature i vlage')
print('GPIO ==> {0:5d}').format(TEMP_GPIO)
print('*******************************************************')
time.sleep(.100)

#SENSOR START
print('Program pokrenut')
print('Za izlaz pritisni CTRL+C')
print('*******************************************************')

#CALLBACK FUNCTION FOR KEYBOARD INTERRUPTION
def keyboardInterruptHandler(signal, frame):
        print('\nPrekid sa tipkovnice')
        mysql_conn.closeConnection()
        print('Bye bye ID:{}').format(signal)
	GPIO.cleanup()
        sys.exit(0)

#FUNCTION FOR TEMPERATURE AND HUMIDITY SENSOR, id = 1
def temp_sensor_callback():
        humidity, temperature = Adafruit_DHT.read_retry(11, TEMP_GPIO)
	if humidity == None and temperature == None:
		data = 'Greska kod mjerenja temperature i vlage'
		print(data)
	else:
		data = 'Dohvacena temperatura: {0:0.1f} C i vlaga: {1:0.1f} %'.format(temperature, humidity)
        	print('\n'+data)
        	redis_conn.writeToDb('temperatura', jsonBuilder.createRedisEntry(1, data))
        	mysql_conn.insertTermolog(1,('{:0.2f}').format(round(temperature, 2)),
                                        ('{:0.2f}').format(round(humidity, 2)), 'Izmjerena temperatura i vlaga')

		is_between_temp = int(temperature) in range(18, 26)
        	if not is_between_temp:
			poruka = random.choice(tempMessages)
			print(poruka)
                	mysql_conn.insertAlarm(1, poruka)
			payload = jsonBuilder.createPOSTmessage(1, poruka)
		        print("Server response: {0}").format(restClient.sendPOSTMessage(payload))

		is_between_hum = int(humidity) in range(20, 80)
        	if not is_between_hum:
			poruka = random.choice(humMessages)
                	print(poruka)
                	mysql_conn.insertAlarm(1, poruka)
			payload = jsonBuilder.createPOSTmessage(1, poruka)
		        print("Server response: {0}").format(restClient.sendPOSTMessage(payload))

#DETECT KEYBOARD INTERRUPTION
signal.signal(signal.SIGINT, keyboardInterruptHandler)

if __name__ == "__main__":
        while True:
                try:
                        temp_sensor_callback()
                finally:
                        pass

