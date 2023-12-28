import myQueue
import dbtools
import time
import creds_and_settings as f1
import paho.mqtt.client as mqtt
import weatherClass as wc
import ssl
import itertools
import math
import json

#status if system is currently watering other plants set to false
running = False
#last Job time
lastJob = None
#relay currently being worked on 
valveRelay = None
#create queue for storing plants that need to be watered
waterQueue = myQueue.Queue()
#create weather class object to get weather data
weather = wc.Weather(f1.CONST_LAT,f1.CONST_LON,f1.CONST_APIKEY)

weather.getWeather()

#create dbtools object for storing and accessing database
irigDB = dbtools.DBTools(f1.db,f1.backupdb)
#ensure that the database is created,if not new database will be created

#TODO Check weather if device outside day/too hot dont


#check if device should be watered based on weather(Rain)
def shouldWaterRain(weather, deviceLoc):
    #set rc to true, if inside wont enter loop to check weather
    rc = 1
    #check if device located outside
    if deviceLoc == 0:
        # Use the weather object to get weather data
        check = weather.getWeather()
        res = json.loads(check[0])
        #check if API call successfull and query made
        if check[0] != None:
			#check if next few hours has rain/stormy weather codes 2xx,3xx,5xx,6xx
			#check next 5 hours 
            for data in itertools.islice(res['hourly'],5):
				#get starting number from weather code given
                codeStart = math.floor(data['weather'][0]['id']/100)
				#if the code starts with a rain-ish code set water to false and break, wont water
                if codeStart in (2,3,5,6):
					#return why not watering
                    rc = data['weather'][0]['main']
                    break
    #return if device can be watered
    return rc

def timeCheck(lastCheck,timeAllowed):
    #rc set to false default
    rc = False
    currentTime = (time.time())
    
    if (lastCheck is not None) and (currentTime-lastCheck)>timeAllowed:
        rc = True
    return rc

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    client.subscribe("Valve/+/+/data", qos = 1)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

#this will be used for recieving water used from system
def on_message_from_valve(client, userdata, msg):
	
	message = json.loads(msg.payload.decode("utf-8"))
	print(f"received from valve: {message}")
    #recieve list with [systemrunning,usage,leak?]

    #set flag if system still running
	global running
	global lastJob
	global waterQueue
	if message[1] != 99:
		leak = message[1]
		running = message[2]
		vID = message[3]
		usage = message[0]
		#store reading in database
		irigDB.addWaterUsage(usage,vID)
		#if we are in calibration mode increment water used
		if message[4] == -1:
			irigDB.setCalibrate(vID,usage)

		#this was a succesfull run, remove item from front of queue
		finishedDevice = waterQueue.dequeue()
		#set status of moisture sensor to -1 to give 5 min delay after watering
		irigDB.setStatus(finishedDevice[0],-1)
	#change lastJob if not running
	if message[2] == False:
		lastJob = None
	
	#check if there is a leak in the system
	if leak == True:
		#if there is a leak, disable valve
		print("theres a leak")
		#log leak

		#send alert via email to email list

#Valve/devicename/relay/request

#create client object to recieve mqtt messages
client = mqtt.Client(client_id='Queue', userdata=None,protocol=mqtt.MQTTv5)
#set on_connect callback
client.on_connect = on_connect

#tls required for hiveMq cloud connection
client.tls_set(tls_version=ssl.PROTOCOL_TLS)
# set creds for system
client.username_pw_set(f1.waterUN,f1.waterPass)
#connect to the broker 
client.connect(f1.broker,f1.port,keepalive=60)

#set callbacks for mqtt events
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.message_callback_add("Valve/#",on_message_from_valve)
#have the main system subscribe to all moisture sensors, will receive each message at most once





while True:

	#get list of all jobs in database and delete after recovered
	temp = irigDB.getJobs()
	
	#add new jobs to queue for watering
	waterQueue.addLoad(temp)

	#loop client to wait for finish flag to be updated 
	client.loop(5)
	while len(waterQueue) > 0 and not running:
		#get oldest job (device_ID) from queue look at device and try to water it
		workingJob = waterQueue.peakFront()
		print(f"now working on {workingJob}")
		#find location of device
		print(workingJob)
		devLoc = irigDB.getLocation(workingJob[0])

		#check to see if able to water device due to Rain
		rainTest = shouldWaterRain(weather, devLoc[0])
		#if able to do watering, start system
		if rainTest == 1:
			#set running to true, stops loop untill system finishes watering
			running = True
			#set lastJob time
			lastJob = (time.time())
			#find clients water valve via the database
			valveRelay = irigDB.getValve(workingJob[0])
			#print devices being watered
			print(valveRelay)
			#check that relay returned and relay is active
			if valveRelay != None and valveRelay[4] == 1:
				#send valve information and instruction code 1 to water and calFlag 
				message = json.dumps([valveRelay,1,workingJob[1]])
				print(message)
				client.publish(f"Valve/{valveRelay[3]}/{valveRelay[2]}/instructions",message)
			time.sleep(1)
		#if not able to wate plant tell reason and move on
		else:
			print(f"Not watering plant, Reason: {rainTest}")

	#if time greater than 1 minute, check leak, send error, move on
	#TODO Send Error 
	if timeCheck(lastJob,60):
		print("error: time overlap")
		#Set running to false, and lastJob to current time
		running = False
		lastJob = None
		#shutdown valve
		if valveRelay != None:
			message = json.dumps([valveRelay,2])
			client.publish(f"Valve/{valveRelay[3]}/{valveRelay[2]}/instructions",message)

			#remove item from queue and set status to 0
			popped = waterQueue.dequeue()
			irigDB.setStatus(popped[0],0)
