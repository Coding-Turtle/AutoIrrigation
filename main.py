#importing my programs/classes
import weatherClass
import dbtools
import creds_and_settings as f1

#importing other libraries for access
import json
import threading
import subprocess
import time
import paho.mqtt.client as mqtt

#testing api call
test = weatherClass.Weather(f1.CONST_LAT,f1.CONST_LON,f1.CONST_APIKEY)
result = test.getWeather()
print(result)
