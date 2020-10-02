import mysql.connector
from datetime import datetime
from mysql.connector import Error
import sys

__localhost = 'localhost'
__database = 'dinnovose2_rpiMySQL'
__user = 'dinnovose2'
__password = 'mysqladmin'

connection = ''

def checkConnection():
	try:
		global connection
		connection = mysql.connector.connect(host=__localhost,
                                     database=__database,
                                     user=__user,
                                     password=__password)

	    	if(connection.is_connected()):
        		print('Uspjesno spajanje na MySQL bazu - {0}').format(__database)

	except Error as e:
	    	print('Greska kod spajanja na bazu: {0}').format(e)
		sys.exit(0)

def closeConnection():
	global connection
	if(connection.is_connected()):
		connection.close()
		print('Zatvorena veza prema MySQL bazi - {0}').format(__database)

##sensor id --> {temp = 1, hum = 2, gas = 3, fire = 4, rain = 5, photo = 6, pir = 7}
def insertLog(message):
        cursor = connection.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO dnevnik (opis, vrijeme) VALUES (%s,%s)",(message, timestamp,))
        connection.commit()
        cursor.close()

##GET sensor info in form of a message, use message for log entry
def getSensorInfoMessage(id, message):
	message_new = ''
        cursor = connection.cursor()
        cursor.execute("SELECT naziv, opis FROM senzor WHERE id = %s", (id,))
        result = cursor.fetchone()
       	message_new = ("Senzor: {0} - {1}, Poruka: {2}").format(result[0], result[1], message)
	cursor.close()
	return message_new

##SAVE data in table alarm
def insertAlarm(id, message):
	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	cursor = connection.cursor()
	cursor.execute("INSERT INTO alarmlog (senzor, poruka, vrijeme) VALUES (%s,%s,%s)", (id,message,timestamp,))
	connection.commit()
	cursor.close()
	insertAlarmLog(id, message)

##SAVE data from sensor to table dnevnik
def insertAlarmLog(id, message):
	message_from_func = getSensorInfoMessage(id, message)
	insertLog(message_from_func)

##SAVE data from temperature/humidity sensor to table termolog
def insertTermolog(id, temperature, humidity, message):
	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = connection.cursor()
	cursor.execute("INSERT INTO termolog (temperatura, vlaga, senzor, vrijeme) VALUES (%s, %s, %s, %s)", 
			(temperature, humidity, id, timestamp,))
	connection.commit()
	message_new = getSensorInfoMessage(id, message)
	insertLog(message_new)

##GET USER INFO BASED ON TAG ID
def getUserByTagId(id):
	cursor = connection.cursor()
	cursor.execute("SELECT ime, prezime, korisnicko FROM student WHERE tag = %s", (id,))
	result = cursor.fetchone()
	user = ("{0} {1} - {2}").format(result[0], result[1], result[2])
	cursor.close()
	return user


##CHECK IF STUDENT WITH TAG ID EXISTS IN DATABASE
def checkStudentTagId(tag_id):
	cursor = connection.cursor()
	cursor.execute("SELECT id FROM tag WHERE serijski_broj = %s", (tag_id,))
	result = cursor.fetchone()
	if result == None:
		message = "Pokusaj prijave nepoznatog korisnika sa tag-om serijskog broja: {0}".format(tag_id)
		print(message)
		insertLog(message)
		return False
	elif result[0] % 1 == 0:
		user = getUserByTagId(result[0])
		message = "Prijava studenta {0}".format(user)
		new_message = getSensorInfoMessage(2, message)
		insertLog(new_message)
		return True

##RFID SENSOR ID = 2
def insertStudentLog(tag_id, sensor_id, razlika, ulaz, izlaz):
	cursor = connection.cursor()
        cursor.execute("SELECT id FROM tag WHERE serijski_broj = %s", (tag_id,))
	result = cursor.fetchone()
	id = result[0]
	cursor.execute("INSERT INTO studentlog (tag, senzor, proteklo_vrijeme, vrijeme_ulaza, vrijeme_izlaza) VALUES (%s,%s,%s,%s,%s)", (id,sensor_id,razlika,ulaz,izlaz,))
        connection.commit()
	timeInClass = calculateTime(razlika)
	cursor.execute("UPDATE studentpredmet SET odslusano_sati = odslusano_sati + %s WHERE student = %s", (timeInClass,id,))
	connection.commit()
        cursor.close()

##PIR SENSOR ID = 4
def insertLightLog(sensor_id, razlika, upaljeno, ugaseno):
        cursor = connection.cursor()
        cursor.execute("INSERT INTO svjetlolog (senzor, proteklo_vrijeme, vrijeme_paljenja, vrijeme_gasenja) VALUES (%s,%s,%s,%s)",(sensor_id, razlika, upaljeno, ugaseno,))
        connection.commit()
        cursor.close()


##RETURN TIME IN CLASSROOM FOR DB
def calculateTime(razlika):
	sati, minute, sekunde = map(int,str(razlika).split(':'))
	return sati + minute/60 + sekunde/60


if __name__ == "__main__":
	checkConnection()
	closeConnection()
