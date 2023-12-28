import socket
import network
import json
import os
from time import sleep,ticks_ms,time
from machine import ADC,Pin,reset
from umqtt.simple import MQTTClient

#Pins for relay control for SB Components 4 relay board
relay1 = Pin(18,Pin.OUT)
relay2 = Pin(19,Pin.OUT)
relay3 = Pin(20,Pin.OUT)
relay4 = Pin(21,Pin.OUT)

#Active array to store active relays
activeRelays = [True,True,True,True]

#pins for waterFlow Check
waterFlow = Pin(13,Pin.IN)

#Global variables for codes and relays
instructionCode = 0
relay = 0
vID = 0
waterCal = 0
calCode = 0
activeSet = True

#Global Pulse Tracker
pulse = 0

logErrors = open('log.txt', 'a')

def connect(wifi,password):
    attempt = 0
    #connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(wlan.isconnected())
    wlan.connect(wifi,password)
    #try to connect to network
    while wlan.isconnected() == False:
        #print('waiting for internet')
        sleep(5)
        #if no connection made in 50 tries, restart system and try again
        if attempt == 50:
            logfile.write("Connection Timeout, Restart")
            wlan.disconnect()
            reset()
        attempt = attempt + 1
        
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return wlan

def subMain(topic,message):
    print(f"Recieved Message:{message.decode()}")
    #decode instructions
    instructions = json.loads(message.decode())
    print(instructions)
    global instructionCode
    global relay
    global vID
    global waterCal
    global calCode
    global activeSet
    global touched
    print(instructions[1])
    
    #if code == 88 set status of relay
    #manual send 1 == activate 0 == deactivate
    if instructions[1] == 88:
        instructionCode == 88
        relay = instructions[0][2]
        activeSet = instructions[2]
        
    #if code == 99 callback check
    elif instructions[1] == 99:
        instructionCode = 99
        relay = 0
    #if code is 1, enable water and get relay to turn on
    elif instructions[1] == 1:
        relay = instructions[0][2]
        instructionCode = instructions[1]
        vID = instructions[0][0]
        #if not kill all command, get calibration
        if instructionCode != 2:
            calCode = instructions[2]
            #if calibration flag set, water 0.01 liters, 
            #else use calibrated ammount
            if calCode == -1:
                waterCal = 0.1
            else:
                waterCal = instructions[2]
    
        
        

#This is built for SB Components 4 Relay board
def waterDevice(relay,waterUsage):
    global activeRelays
    #check which relay called and that relay is active
    #Open valve,record usage 10 seconds, close valve
    if relay == 1:
        relay1.value(1)
        usage = recordUsage(10,5.5,waterUsage)
        relay1.value(0)
    elif relay == 2:
        relay2.value(1)
        usage = recordUsage(10,5.5,waterUsage)
        relay2.value(0)
    elif relay == 3:
        relay3.value(1)
        usage = recordUsage(10,5.5,waterUsage)
        relay3.value(0)
    elif relay == 4:
        relay4.value(1)
        usage = recordUsage(10,5.5,waterUsage)
        relay4.value(0)
    #account for delay in water shutoff and continue recording
    backFillUsed = recordUsage(5,5.5,1)
    totalUsed = backFillUsed + usage
    #return total used water 
    return totalUsed        

    
def shut(relay):
    if relay == 1:
        relay1.value(0)
    elif relay == 2:
        relay2.value(0)
    elif relay == 3:
        relay3.value(0)
    elif relay == 4:
        relay4.value(0)
    else:
        print("valve does not exist")
        
def cycleSystem():
    #turn on all relays for 0.5 seconds and shut them down after
    relay1.value(1)
    sleep(0.1)
    relay1.value(0)
    sleep(0.1)
    relay2.value(1)
    sleep(0.1)
    relay2.value(0)
    sleep(0.1)
    relay3.value(1)
    sleep(0.1)
    relay3.value(0)
    sleep(0.1)
    relay4.value(1)
    sleep(0.1)
    relay4.value(0)

        
    
#must pass pin for irq handler, not used though
def pulseIncrement(pin):
    global pulse
    pulse = pulse + 1

#pass time in seconds  
def recordUsage(time,factor,usageLimit):
    #pulse tracker for hall measurement and totalUsage variable tracker
    global pulse

    timeInMili = time*1000
    #get current time TODO
    startTime = ticks_ms()
    #previousTime = 0
    
    pulse = 0
    totalUsage = 0.0
    #factor for waterFlow Sensor
    f=factor
    #continue recording while device has not hit usage limit or time limit
    while((ticks_ms()-startTime) < timeInMili and totalUsage < usageLimit):
        sleep(1)
        flowRate = (pulse/f)/60
        #set pulse = 0
        pulse = 0
        
        #set time change to seconds
        #timeChange = (ticks_ms()-previousTime)*0.001
        #Only stop read for 1 second, converted to water used per second 
        totalUsage = totalUsage + (flowRate)
        #previousTime = ticks_ms()
        print(f"totalusage:{totalUsage}")
        print(f"checking usage:{ticks_ms()-startTime}<{timeInMili}")
    return totalUsage


def checkLeak():
    global pulse
    pulse = 0
    #set leak variable to false
    leak = False
    
    #interupt for reading of waterFlow Sensor
    
    sleep(5)
    #if after 10 seconds pulses have been tracked there is a leak
    print(f"pulses:{pulse}")
    if pulse > 0:
        leak = True
    #return if a leak occures
    print(f"leak:{leak}")
    return leak 
    
def killAll():
    print("shutdown all valves")
    for i in range(1,5):
        shut(i)
        print(i)
    
    
def main(completeConfig):
    
    #global code for status message from main server
    configDict = completeConfig
    global instructionCode
    global relay
    global vID
    global waterCal
    global calCode
    global activeSet
    global activeRelays
    
    lastPing = 0
    
    os.dupterm(logErrors)
    #check message has set value
    touched = False
    #set interrupt on water meter
    waterFlow.irq(trigger=Pin.IRQ_RISING, handler=pulseIncrement)
    
    subTopic = f"Valve/{configDict.get('clientName')}/+/instructions"
    
    connection = connect(configDict.get('wifiName'),configDict.get('wifiPassword'))
    #not secure params, need to fix
    sslparams = {'server_hostname': configDict.get('hiveBroker')}
    client = MQTTClient(client_id = configDict.get('clientName'),
                        server = configDict.get('hiveBroker'),
                        port = configDict.get('hivePort'),
                        user = configDict.get('hiveUserName'),
                        password = configDict.get('hivePass'),
                        keepalive=7200,
                        ssl = True,
                        ssl_params = sslparams)
    #connect client and set callback/subscription
    client.connect(clean_session=True)
    conMessage = json.dumps("Client Connected")
    client.set_callback(subMain)
    client.subscribe(subTopic)
    
    client.publish(f'Valve/{configDict.get("clientName")}/Connection',conMessage,False,1)
    while connection.isconnected():
        try:
            #check if need to ping server to keep connection 40 second pings
            #to avoid disconnect
            if lastPing < time():
                pingMessage = json.dumps(1)
                client.publish(f'Valve/{configDict.get("clientName")}/ping',pingMessage,False,1)
                lastPing = time() + 40
            #check if message from server
            client.check_msg()
            sleep(5)
            
            #instructionu to open valve
            if instructionCode == 1:
                touched = True
                #check that relay active
                if activeRelays[relay-1]:
                    #temp variables for returning data
                    #functions to water device
                    usage = waterDevice(relay,waterCal)
                    #function to check for leak,
                    leak = checkLeak()
                    #set running to false
                    running = False  
                    #use json to pack message and publish usage
                    message = json.dumps([usage,leak,running,vID,calCode])
                    client.publish(f'Valve/{configDict.get("clientName")}/{relay}/data',message,False,1)
                    sleep(1)
                
            #instruction to disable/enable relay
            elif instructionCode == 88:
                touched = True
                #set status of relay, adjusted for 0 index, default active
                activeRelays[relay-1] = True if activeSet == 1 else False if activeSet == 0 else True
                message = json.dumps([configDict.get("clientName"),"Enabled" if activeSet == True else "Disabled"])
                client.publish(f'Valve/{configDict.get("clientName")}/ValveStatSet',message,False,1)
                
            #instruction for status callback checker    
            elif instructionCode == 99:
                touched = True
                message = json.dumps([configDict.get("clientName"),1])
                client.publish(f'Valve/{configDict.get("clientName")}/callBack/data',message,False,1)
            
            #instruction to kill all watering TODO log used water?
            elif instructionCode == 2:
                touched = True
                killAll();
            
            #if we have done work, set all globals to 0 for next message
            if touched:
                instructionCode = 0
                relay = 0
                vID = 0
                calCode = 0
                waterCal = 0
                activeSet = False
                
        except OSError:
            print("connection error resetting")
            connection.disconnect()
            sleep(1)
            reset()
    
    #if connection dropped restart machine
    if connection.isconnected() == False:
        logfile.write("Connection Dropped, Restart")
        connection.disconnect()
        sleep(1)
        reset()
        

if __name__ == '__main__':
    main()