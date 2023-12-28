import socket
import json
from time import sleep
from machine import ADC,Pin

##for moisture reading
soilReading = ADC(Pin(26))

def getInput(prompt,errPrompt):
    result = None
    userIn = input(prompt)
    
    if userIn == "Y":
        result = userIn
    else:
        print(errPrompt)
        result = getInput(prompt,errPrompt)
    
    return result

def calibrateSensor(count):
    avgReading = 0
    readingSum = 0
    for x in range(count):
        reading = soilReading.read_u16()
        readingSum += reading
        sleep(0.5)
        print(reading)
    
    avgReading = readingSum/count
    
    return int(avgReading)

def main():
    print("Calibration System:Please hold clean sensor in air")

    airRequest = "Press Y and Enter when Sensor is Ready for Air Reading:"
    airErr = "Please Place Clean Sensor In Air"

    waterRequest = "Press Y and Enter when sensor is ready for Water Reading:"
    waterErr = "Please Place Sensor In Water"

    ##Prompt calibrations
    airPrompt = getInput(airRequest,airErr)

    airCal = calibrateSensor(5)
    print(f"airCal is {airCal}\n")


    print("Calibration System: Please sumberge clean sensor in water\nUp To BUT NOT OVER 'V1.2'")

    waterPrompt = getInput(waterRequest,waterErr)

    waterCal = calibrateSensor(5)
    print(f"waterCal is {waterCal}")
    
    return (airCal,waterCal)


if __name__ == '__main__':
    main()