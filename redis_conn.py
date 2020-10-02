import redis
import sys

pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
r = redis.Redis(connection_pool=pool)

def checkConnection():
	try:
		r.ping()
		print('Uspjeno spajanje na Redis bazu')
	except redis.exceptions.ConnectionError:
		print('Neuspjesno spajanje na Redis bazu')
		sys.exit(0)

def writeToDb(key, value):
	r.set(key, value)

def getFromDb(key):
	value = r.get(key)
	return value

def deleteFromDb(key):
	r.delete(key)
