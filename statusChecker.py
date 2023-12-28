import time
import re
import dbtools
import paho.mqtt.client as mqtt
import ssl
import creds_and_settings as f1
import json


#send email as server sending email, as oru server is next up the line
#relay host: 
#resolve address as where to pass mail through to
#get ip address of device and mac of wifi channel

#sending functions
import smtplib

#email messages
from email.message import EmailMessage

#create dbtools object for storing and accessing database
irigDB = dbtools.DBTools(f1.db,f1.backupdb)
recievedMessages = None


def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    client.subscribe("Valve/+/+/data", qos = 1)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message_from_valve(client, userdata, msg):
    #create global reference to database object
    global irigDB
    global recievedMessages
    recievedMessages = json.loads(msg.payload.decode("utf-8"))
    print(f"recieved callBack from:{recievedMessages}")


#request callback from valves to check that valve pico connected
def valveCallBack(client):
    #bring in global reference to database and recieved messages
    global irigDB
    global recievedMessages
    #get all valves that are active
    activeValves = irigDB.getAllDevicesOfType(2)
    hearBackList = []
    #print all active valves
    for x in activeValves:
        print(x)
    #loop through all active valves
    for valve in activeValves:
        curTime = time.time()
        hearBack = False
        #while not heard back and time less than 2 minutes keep trying to get message through
        while (time.time() - curTime)/60 < 0.1 and hearBack == False: 
            
            message = json.dumps([valve[1],99])
            print(valve[1])
            client.publish(f"Valve/{valve[1]}/callBack/instructions",message)
            
            client.message_callback_add("Valve/+/callBack/data",on_message_from_valve)
            client.loop_start()
            time.sleep(5)
            client.loop_stop()
            
            #if message has been recieved
            if recievedMessages != None:
                #if successCode and current item in list matches message sender
                if recievedMessages[1] == 1 and valve[1] == recievedMessages[0]:
                    #set hearBack to true and remove value from list
                    print(f"valves looking at {valve}, valves deleting {recievedMessages[0]}")
                    hearBack = True
                    hearBackList.append(valve)
        time.sleep(1)
    #if valve recieved message back, or valve is set to inactive in DB remove from list
    for valve in activeValves:
        if valve in hearBackList:
            activeValves.remove(valve)
        elif valve[6] == 0:
            activeValves.remove(valve)

    #return all active valves that did not get callback
    return activeValves
        
def main():
    #set main loop, restarts if handle error
    running = True
    while running:
        #try to start mqtt system
        try:
            #create client object to recieve mqtt messages
            client = mqtt.Client(client_id='main', userdata=None,protocol=mqtt.MQTTv5)
            #set on_connect callback
            client.on_connect = on_connect
            time.sleep(1)

            #tls required for hiveMq cloud connection
            client.tls_set(tls_version=ssl.PROTOCOL_TLS)
            # set creds for system
            client.username_pw_set(f1.userName,f1.credPassWord)
            #connect to the broker 
            client.connect(f1.broker,f1.port,keepalive=60)

            #set callbacks for mqtt events
            client.on_subscribe = on_subscribe
            client.on_publish = on_publish
            
            client.message_callback_add(f"Valve/#",on_message_from_valve)

            #get all active moisture recorders that have not been heard from in 30 minutes
            notTouched = irigDB.getNotTouched(30)
            
                
            valveNoAnswer = valveCallBack(client)
            
            for valve in valveNoAnswer:
                print(f"No Hearback:{valve}")
            
            
            for noTouch in notTouched:
                print(noTouch)
            #set running to false to break loop
            running = False
        #handle exception if handle error
        except ssl.SSLEOFError:
            print("error with handshake, restarting")
            time.sleep(1)
            
            
if __name__ == '__main__':
    main()
