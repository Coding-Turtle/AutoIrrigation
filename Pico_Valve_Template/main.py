import valve
import os
import json
from time import sleep

def checkConfig(config):
    #flag to check that all fields are filled
    fieldsFilled = True

    #loop though json entries
    #check that all fields are properly filled out
    for x in config:
        if config[x] == None or config[x] == "None":
            #if a field is not filled out set flag to false
            fieldsFilled = False
            #TODO set this to log the values not filled out eventually
            print(f"{x} is not filled out")
    #return if all fields filled or not
    return fieldsFilled

def getJsonFile():
    #List to store all files of type .json
    jsonList = []
    #get a list of all files in current dir
    fileList = os.listdir()
    #loop through list adding to jsonList if the file type ends in .json
    for x in fileList:
        if ".json" in x:
            jsonList.append(x)
    #return list of json files in directory
    return jsonList

def pullJson():
    #get list of all json files in directory
    jsonList = getJsonFile()
    #check that there is only one .json file to confirm that
    #the correct file is being chosen
    if len(jsonList) == 1:
        #create config
        with open(jsonList[0],'r') as file:
            configTemp = json.load(file)
            
    elif len(jsonList)>1:
        print("Error More Than One Config")
    else:
        print("No Config Available")
    #return config item
    return configTemp

def saveConfigUpdates(config):
    saved = False
    jsonList = getJsonFile()
    
    #check that there is only one .json file to confirm that
    #the correct file is being chosen
    if len(jsonList) == 1:
        #create config
        with open(jsonList[0],'w') as file:
            json.dump(config,file)
            
        saved = True
    elif len(jsonList)>1:
        print("Error More Than One Config")
    else:
        print("No Config Available")
    #return if saved or not
    return saved

def assignConfig(configFilled,configDict):
    #loop through filled out config data
    for field in configFilled:
        #assign values to the dict keys passed
        configDict.update({field:configFilled[field]})
    #return filled out settings
    return configDict


def main():
    #TODO MAKE MAIN, CONFIGURATOR
    ##data settings for client
    configDict = {
        "hiveBroker":None,
        "hivePort": None,
        "clientName":None,
        "hiveUserName":None,
        "hivePass":None,
        "wifiName":None,
        "wifiPassword":None,
        "water":None,
        "air":None,
    }

    #pull config File 
    configFields = pullJson()
    print(configFields)
    #check that all fields in config file have been filled
    if checkConfig(configFields):
        #fill data settings from config file
        configDict = assignConfig(configFields,configDict)
        print(configDict)
        #check that all data settings have been filled
        if checkConfig(configDict):
            #TODO need to log
            print("Configurations Filled Good to GO")
            #check if config success:Run Program if Success
            print("Running")
            #pass dictionary to moisture program to start monitoring levels
            valve.main(configDict)
        #set flag to false if dictionary not filled
        else:
            print("Dict Not Filled")
    #if fields have not been filled  set flag to false
    else:
        ConfigFlag = False
        print("Not All Configs filled, Not Running")

    #check if config success:Run Program if Success

if __name__ == '__main__':
    main()