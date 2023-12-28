import time
import re
import dbtools
import subprocess
import paho.mqtt.client as mqtt
import ssl
import creds_and_settings as f1

#create dbtools object for storing and accessing database
irigDB = dbtools.DBTools(f1.db,f1.backupdb)

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    client.subscribe("Water/+/data", qos = 1)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message_from_moisture(client, userdata, msg):
    #create global reference to database object
    global irigDB
    #store reading in database
    txt = msg.topic
    #find where device id starts and stops in topic
    start_stop = re.search("moisture[0-9]+",txt) 
    #assign device variable to device id by indexing into topic
    device = txt[start_stop.start():start_stop.end()]
    #convert payload to float to store moisture level
    reading = float(msg.payload.decode("utf-8"))    
    print(f"device is {device}")
    print(f'length of device is: {len(device)}')
    #add reading from device to data base for storage
    irigDB.addReading(device,reading)
    
    #check if calibrated, get device record so we can pass deviceID to calTable
    deviceInfo = irigDB.getDevice(device)
    #check if device record exists
    if deviceInfo != None:
        
        #if status == 0 just put device to sleep for 30 min
        #Add to queue if needed
        needWater = irigDB.checkWater(device,reading)
        if deviceInfo[6] == 0:
            #check if has yet to be calibrated
            if deviceInfo[7] == None:
                #check if needs to be calibratet(first watering below thresh or 4 hours has passed)
                result = irigDB.getCalibrate(deviceInfo[0],reading,needWater)
                #if we need to calibrate and waternow
                if result == True:
                    #add device to watering queue if needs watering
                    #set device status to watering so it cant be re-added to the job table
                    irigDB.setStatus(deviceInfo[0],1)
                    irigDB.createJob(device)
            #if device has already been calibrated check if it needs watered
            elif irigDB.checkWater(device,reading) == 1:
                #set devices status to watering so it cant be re-added to the job table
                irigDB.setStatus(deviceInfo[0],1)
                irigDB.createJob(device)
                
            else:
                print("no water needed")
            
            #PUBLISH 30 min sleep code
            client.publish(f"Water/{device}/instructions",0)
        #else if status == 1, device is in queue for watering
        #device to sleep for 30 min dont add to queue even if needed
        elif deviceInfo[6] == 1:
            #PUBLISH 30 MIN SLEEP
            client.publish(f"Water/{device}/instructions",0)
            print('back to sleep')
        #else if status == -1, device has been watered recently, 
        #put device to sleep for 5 mins dont add to queue and set status = 0
        elif deviceInfo[6] == -1:
            #publish message for device to sleep for 5 min
            client.publish(f"Water/{device}/instructions",-1)
            #set status to 0
            irigDB.setStatus(deviceInfo[0],0)
        
        else:
            print(f"Device Status ERROR -> Not Valid -1,0, or 1:{deviceInfo[6]}")

def main():
    #set main loop, restarts if handle error
    while True:
        #try to start mqtt system
        try:
            #ensure that the database is created,if not new database will be created
            irigDB.createDB()

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
            client.message_callback_add("Water/#",on_message_from_moisture)

            #have the main system subscribe to all moisture sensors, will receive each message at most once

            #set system to loop forever
            client.loop_forever()
        
        #handle exception if handle error
        except ssl.SSLEOFError:
            print("error with handshake, restarting")
            time.sleep(1)
            
            

if __name__ == '__main__':
    main()
