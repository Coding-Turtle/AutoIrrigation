import requests
import json
import time
import datetime

class Weather():
    #initialize class
	def __init__(self,lat,lon,key):
		self.lat = lat
		self.lon = lon
		self.apikey = key
		self.date = None
		self.apiLink = f'https://api.openweathermap.org/data/3.0/onecall?lat={self.lat}&lon={self.lon}&date={self.date}&exclude=current,daily,minutely,alerts&units=imperial&appid={self.apikey}'
		self.lastCall = None #stores last time API was called, will help avoid charges
		self.timeBetweenCall = 20 #time limit between calls
		self.lastRes = None #stores last query 
		
	#print formating for class
	def __str__(self):
		return f"latitude = {self.lat}\nlongitude = {self.lon}\nkey = {self.apikey}"
	
	#make call to api to get result treat as private func
	def __queryWeather(self):
		#set response to -1 to account for failure
		response = None
		#get current time 
		currTime = (time.time())/60
		#check that this is the first call, or appropriate time has passed between calls
		if (
			self.lastCall is None or 
			((currTime-self.lastCall) > self.timeBetweenCall)
			):
			#set last call to current time
			self.lastCall = currTime
			#try to request data from weather api
			try:
				response = requests.get(self.apiLink)
			#if connection error print error set response -2 for connection error
			except requests.exceptions.ConnectionError:
				print("Error with Connection")
				response = -2
			#if no connection error, set class var lastRes to result, set response code to 1 for success
			else:
				self.lastRes = json.dumps(response.json())
				response = 1
		#if call made to  soon, set result to -1
		#avoids API overage Fees
		else:
			response = -1
		#return response code
		return response


	def __setDate(self):
		self.date = datetime.datetime.today().strftime("%Y-%m-%d")

	def getWeather(self):
		#call to set date
		dateResponse = self.__setDate()
		#call to query weather
		response = self.__queryWeather()
		#Return tuple with query result(if one exists) and response
		return (self.lastRes,response)
		