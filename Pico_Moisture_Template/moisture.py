import socket
import network
import json
from time import sleep
from machine import ADC,Pin,reset,deepsleep
from umqtt.simple import MQTTClient
import os

##for moisture reading
soilReading = ADC(Pin(26))
request = 2
logError = open('log.txt', 'a')

def connect(wifi,password):
    #connect to WLAN
    attempt = 0
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(wlan.isconnected())
    wlan.connect(wifi,password)
    
    #try to connect to network
    while wlan.isconnected() == False:
        print('waiting for internet')
        sleep(5)
        if attempt == 50:
            logfile.write("Connection Timeout, Restarting")
            wlan.disconnect()
            reset()
        attempt = attempt + 1
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return wlan

#taken from arduino Map function->https://reference.arduino.cc
def mapReading(val,in_min,in_max,out_min,out_max):
    return(val-in_min)*(out_max-out_min)/(in_max-in_min)+out_min

#used to get the average of the moisture level over a given ammount of readings
def getAvgMoist(readings,highCal,lowCal):
    #variables for index,summation of readings,list for readings, and average
    i = 0
    storedReadings = []
    levelSum = 0.0
    average = 0.0
    #gather readings,
    while i < readings:
        level = mapReading(soilReading.read_u16(),highCal,lowCal,0,100)
        #check if bad reading less than 0, if so read again
        if level < 0 or level > 100:
            continue
        #sum readings for mean
        levelSum += level
        #add reading to list(maybe use if finding outliers)
        storedReadings.append(level)
        i += 1
        sleep(1)
    # ignore outliers larger than 1% diff(to start)?
    
    #calculate average of moisture levels
    average = (levelSum/readings)
    return round(average,2)

def subMain(topic,message):
    global request
    print(f'Message Received: {message.decode()}')
    request = int(message.decode())
    print(type(request))
    


def main(completeConfig):
    global request
    #get dictionary with config from other program
    configDict = completeConfig

    subTopic = f"Water/{configDict.get('clientName')}/instructions"
    connection = connect(configDict.get('wifiName'),configDict.get('wifiPassword'))
    #not secure params, need to fix
    sslparams = {'server_hostname': configDict.get('hiveBroker')}
    
    client = MQTTClient(client_id = configDict.get('clientName'),
                        server = configDict.get('hiveBroker'),
                        port = configDict.get('hivePort'),
                        user = configDict.get('hiveUserName'),
                        password = configDict.get('hivePass'),
                        keepalive=3600,
                        ssl = True,
                        ssl_params = sslparams)
    client.connect()
    print('connected')
    os.dupterm(Errorfile)
    
    conMessage = json.dumps("Client Connected")
    client.set_callback(subMain)
    client.subscribe(subTopic)
    client.publish(f'Water/{configDict.get('clientName')}/Connection',conMessage,False,1)
    
    ####FUNCTION TO SEND DATA while there is an active internet connection
    while connection.isconnected():
        #try to send message with active connection
        try:
            #Receive request from server
            inMessage = client.check_msg()
            print(f"request is:{request}")
            #if requests 0 or 1, device is giving routine check or needs water and is in queue
            #send info, sleep 30 min
            if request == 0:
                #reset request to 2
                request = 2
                print('sleep')
                connection.disconnect()
                sleep(1800)
                reset()
                
            
            #if device was just watered, wait 5 minutes and get better reading
            elif request == -1:
                #reset request to 2
                request = 2
                connection.disconnect()
                sleep(300)
                reset()

                
            #send messages on default 2
            elif request == 2:
                measurement = getAvgMoist(5,configDict.get('air'),configDict.get('water'))
                message = str(measurement)
                client.publish(f'Water/{configDict.get("clientName")}/data',message,False,1)
                #wait 10 seconds for response
                sleep(10)
            else:
                request == 2
                sleep(5)
                print("error")
                
        #if error with message restart machine
        except OSError:
            print("connection error resetting")
            connection.disconnect()
            sleep(1)
            reset()

    #if connection dropped restart machine
    if connection.isconnected() == False:
        connection.disconnect()
        reset()

if __name__ == '__main__':
    main()