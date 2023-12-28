import dbtools
import json
import shutil
import os
import creds_and_settings as f1

def newPlant(dbobject):
    # return list with new plant information
    rc = []
    # assign db object
    db = dbobject
    # request data from user
    pName = input("Please Enter Plant Name:").lower()
    lowerBound = input("Enter Lower Moisture Limit:")
    upperBound = input("Enter Upper Moisture Limit:")
    # try-catch to ensure proper entry from users
    try:
        # if the entry is valid, set rc to user given data
        if lowerBound.isdigit and upperBound.isdigit and int(upperBound) < 100 and int(lowerBound) > 0 and (int(upperBound)-int(lowerBound)) > 0 and pName.isalpha:
            # check that name does not already exist in db
            checkAvailable = db.checkPlantExists(pName)
            # if name not used assign input to rc
            if checkAvailable:
                rc = [pName, int(lowerBound), int(upperBound)]
            # if name is used, call function to create new plant
            else:
                print("Plant name taken, please choose new name")
                rc = newPlant(db)

        # if entry is invalid call function to request data again
        else:
            print("please check that lower and upper bounds are accurate")
            rc = newPlant(db)
    # call function to request data if value error
    except ValueError:
        print("newPlant input Error")
        rc = newPlant(db)
    # return user input
    return rc

def getIntChoice(prompt, errorPrompt, upperBound):
    # return int with user choice
    rc = 0
    # data for recursive call if error
    passPrompt = prompt
    passError = errorPrompt
    passBound = upperBound
    # request input from user
    userInput = input(prompt)
    # try-catch to ensure proper entry from user
    try:
        # if valid entry set rc to input
        if userInput.isdigit and (1 <= int(userInput) <= upperBound):
            rc = userInput
        # if entry invalid call function to request data again
        else:
            print(errorPrompt)
            userInput = getIntChoice(passPrompt, passError, passBound)
    # call function to request data if value error
    except ValueError:
        print(errorPrompt)
        rc = getIntChoice(passPrompt, passError, passBound)
    # return user input cast as int
    return int(rc)

def getListChoice(listLen, offset, job):
    # return int with user choice
    rc = 0
    # data for recursive call if error
    selfLength = listLen
    selfOffset = offset
    selfJob = job
    # request input from user
    userInput = input(f"Select {job}:")
    # try-cath to ensure proper entry from user
    try:
        # if valid entry set rc to input
        if (userInput.isdigit() and 0 < int(userInput) <= (listLen+offset)):
            rc = userInput
        # if entry invalid call function to request data again
        else:
            print(f"Select {job} from list")
            rc = getListChoice(selfLength, selfOffset, selfJob)
    # call function to request data if value error
    except ValueError:
        print("getChoice input Error")
        rc = getListChoice(selfLength, selfOffset, selfJob)
    # return user input cast as int
    return int(rc)

def printAndLoadDict(workingList, maxRow, index, createOption, createName):
    # create dictionary to store list and index key
    workingDict = dict()
    # loop through length of the list
    for x in range(len(workingList)):
        # print newline if maxrow size is met
        # if (x % maxRow == 0) and x != 0:
        # print("\n",end='')
        # print index and choice
        print(f"{x+1}.{workingList[x][index]}", end=' ')
        # add index as key, and value as choice
        workingDict.update({(x+1): workingList[x]})
    # this flow is for the option to add a new entry
    if createOption:
        # create option for new entry
        print(f'\n{len(workingList)+ 1}.{createName}')
    else:
        # print new line if no option for new entry
        print('\n')
    # return the dictionary with all index/choices entered
    return workingDict

def copyFile(source, dest):
    try:
        shutil.copy(source, dest)
    except FileNotFoundError:
        print(f"Error: File on Path: {source} Does Not Exist")
    except FileExistsError:
        print(f"Error: File on Path: {dest} Already Exists")

def copyFolder(source, dest):
    try:
        shutil.copytree(source, dest)
    except FileNotFoundError:
        print(f"Error: Folder on Path: {source} Does Not Exist")
    except FileExistsError:
        print(f"Error: Folder on Path: {dest} Already Exists")


def createDeviceFile(deviceName):
    # name to add to new config file
    nameToAdd = deviceName
    rc = False
    sourceMoistureMain = "Pico_Moisture_Template/main.py"
    sourceMoistureFile = "Pico_Moisture_Template/moisture.py"
    sourceMoistureCal = "Pico_Moisture_Template/calibration.py"
    sourceMoistureLib = "Pico_Moisture_Template/importLibs"
    sourceValveMain = "Pico_Valve_Template/main.py"
    sourceValveFile = "Pico_Valve_Template/valve.py"
    sourceValveLib = "Pico_Valve_Template/importLibs"
    #sourceTempMain = "Pico_Temp_Template/main.py"
    #sourceTempFile = "Pico_Temp_Template/temp.py"
    #sourceTempLib = "Pico_Temp_Template/importLibs"
    newDir = f'NewConfiguredDevices/Pico_{nameToAdd}'
    

    # open template file and gather all configs
    with open('configTemplate.json', 'r') as file:
        configTemp = json.load(file)

    # set device name in config file
    configTemp['clientName'] = nameToAdd

    # create folder for new device to be added to
    try:
        os.mkdir(newDir)
    except FileExistsError:
        print(f"Error: File on Path: {newDir} Already Exists,Over-Writing")

    # copy template to new device folder
    if "valve" in nameToAdd:
        copyFile(sourceValveFile, newDir)
        copyFile(sourceValveMain, newDir)
        copyFolder(sourceValveLib, f"{newDir}/lib/")

    elif "moist" in nameToAdd:
        copyFile(sourceMoistureFile, newDir)
        copyFile(sourceMoistureMain, newDir)
        copyFile(sourceMoistureCal, newDir)
        copyFolder(sourceMoistureLib, f"{newDir}/lib/")
    elif "light" in nameToAdd:
        copyFile(sourceTempFile, newDir)
        copyFile(sourceTempMain, newDir)
        copyFolder(sourceTempLib, f"{newDir}/lib/")
    else:
        print("No Device Added")

    # save updated config file to new config device folder
    with open(newDir+f"/{nameToAdd}_config.json", 'w') as file:
        json.dump(configTemp, file)

    # check that new config file created and appropriate main.py
    # and moisture.py or valve.py pulled in
    if (
        os.path.isfile(newDir+f"/{nameToAdd}_config.json")
        and (os.path.isfile(newDir+"/main.py"))
        and (os.path.isfile(newDir+"/moisture.py")) or (os.path.isfile(newDir+"/valve.py"))
    ):
        rc = True
    # return if success or not
    return rc

def main():
    # create dbtools object for storing and accessing database
    irigDB = dbtools.DBTools(f1.db, f1.backupdb)
    # ensure that the database is created,if not new database will be created
    irigDB.createDB()
    # set flags to loop untill user is finished and enters valid input
    running = True
    badEntry = True
    # Prompts for UserInput
    mainPrompt = "Please Choose:\n1. Create Device\n2. Create New Plant Record\n3. Activate/Deactivate Valve\n4. Leave\n"
    createPrompt = "What kind of Device?\n1. Pico-Valve\n2. Moisture Sensor\n"
    locationPrompt = "Location of Device:\n1. Inside\n2. Outside\n"
    statusPrompt = "1. Activate Valve\n2. Deactivate Valve\n"
    relayPrompt = "How many Relays on Device?:"
    # prompts for UserInput Errors
    relayErrorPrompt = "please check that relay count is a number larger than 0 and is less or equal to 15"
    genErrorPrompt = "Please choose correct option"

    while running:
        # check what user wants to do
        firstInput = getIntChoice(mainPrompt, genErrorPrompt, 4)
        if firstInput == 1:
            # get user input for choice
            secondInput = getIntChoice(createPrompt, genErrorPrompt, 2)
            if secondInput == 1:
                # check how many relays are being added?
                relayCount = getIntChoice(relayPrompt, relayErrorPrompt, 15)
                # add new device to db and ValveLut entry
                newDevID = irigDB.addDevice(2, 0, 0, 1)
                newRelayID = irigDB.addValveLut(newDevID, relayCount)

            elif secondInput == 2:
                # What plant?(List all plants in DB and their IDs)
                plantList = irigDB.getAllPlants()
                # dictionary that will hold input values and map them to the plant/id
                plantDict = dict()
                plantDict = printAndLoadDict(
                    plantList, 3, 1, True, "New Plant")
                # get and store users choice for plant
                plantChoice = getListChoice(len(plantList), 1, "Plant")

                # Exists(If selected from list add to device)
                if (int(plantChoice) != len(plantList)+1):
                    # find Plant ID for plant choice
                    plantRecord = plantDict.get(plantChoice)
                    plantID = plantRecord[0]
                # Not on List -> create new plant
                else:
                    print("Adding New Plant")
                    # get new plant from user pass db object for validity check
                    result = newPlant(irigDB)
                    # create plant entry  into database and get new plantID
                    NewPlantEntry = irigDB.createPlant(
                        result[0], result[1], result[2])
                    plantID = NewPlantEntry
                while badEntry:
                    # What valve?->link valve to moisture
                    # Get list of all watervalve Picos and add to dictionary
                    valveList = irigDB.getAllDevicesOfType(2)
                    # if the valveList is empty, then there are no valves setup
                    # prompt to create new valve
                    if not valveList:
                        print("No Relay Devices Created, Creating New Device")
                        # check how many relays are being added?
                        relayCount = getIntChoice(relayPrompt, relayErrorPrompt, 15)
                        # add new device to db and ValveLut entry
                        newDevID = irigDB.addDevice(2, 0, 0, 1)
                        newRelayID = irigDB.addValveLut(newDevID, relayCount)
                        # get valvList again with
                        valveList = irigDB.getAllDevicesOfType(2)
                        # check that device created,display data, and create config file
                        if newDevID != -1:
                            print("New Device Added:")
                            # print device data and get dictionary result
                            devDict = irigDB.displayDevice(newDevID)
                            # attempt to create device config file, check for success or failure
                            if (createDeviceFile(devDict['Name:'])):
                                print("Device Configuration File Created")
                            else:
                                print(
                                    "Error Creating Device Configuration\nPlease build using config templates given")

                    # create dictionary and display options of valves
                    valveDict = dict()
                    valveDict = printAndLoadDict(valveList, 0, 1, False, " ")

                    # Select device that controls relay
                    valveDeviceChoice = getListChoice(
                        len(valveList), 0, "Device")
                    # get dictionary entry and pull out valveID
                    valveRecord = valveDict.get(valveDeviceChoice)
                    valveID = valveRecord[0]

                    # select relay that conrols valve
                    # Get list of all relays that are connected to the picoID
                    relayList = irigDB.getRelaysFromDevice(valveID)
                    relayDict = dict()
                    relayDict = printAndLoadDict(relayList, 0, 2, False, " ")
                    # Select relay from list
                    relayChoice = getListChoice(len(relayList), 0, "Relay")
                    # get dictionary entry and pull out relaID
                    relayRecord = relayDict.get(relayChoice)
                    relayID = relayRecord[0]

                    # check if relay has already been used
                    relayAvailable = irigDB.checkRelayAvailable(relayID)
                    # if relay is available break out of loop
                    if relayAvailable:
                        badEntry = False
                    # if relay is in use promp to pick new relay and continue loop
                    else:
                        print("Relay in use,pick new relay")
                # pull from user if device is inside or outside
                location = getIntChoice(locationPrompt, genErrorPrompt, 2)
                # create new device from user input
                newDevID = irigDB.addDevice(1, relayID, plantID, location)
                # check that device was created and display data
            #if selected to create light/temp monitor
            elif secondInput == 3:
                print("Not Implemented")
                # add new device to db and ValveLut entry Default to outside location
                #newDevID = irigDB.addDevice(3, 0, 0, 1)
            else:
                print("Invalid Entry, Try Again")
            # check that device created, display data, and create config file
            if newDevID != -1:
                print("New Device Added:")
                # print device data and get dictionary result
                devDict = irigDB.displayDevice(newDevID)
                # attempt to create device config file, check for success or failure
                if (createDeviceFile(devDict['Name:'])):
                    print("Device Configuration File Created")
                else:
                    print(
                        "Error Creating Device Configuration.\nPlease build using config templates given")

            else:
                print("ENTRY FAILED")
            print("Please Continue or Quit")
        elif firstInput == 2:
            result = newPlant(irigDB)
            entry = irigDB.createPlant(result[0], result[1], result[2])
        elif firstInput == 3:
            #set badentry to true, will be false when finished to break loop
            badEntry = True
            while badEntry:
                    # What valve?->link valve to moisture
                    # Get list of all watervalve Picos and add to dictionary
                    valveList = irigDB.getAllDevicesOfType(2)
                    # if the valveList is empty say no adjusting and restart
                    if not valveList:
                        badEntry = False
                        print("No Devices to Adjust")
                        break

                    # create dictionary and display options of valves
                    valveDict = dict()
                    valveDict = printAndLoadDict(valveList, 0, 1, False, " ")

                    # Select device that controls relay
                    valveDeviceChoice = getListChoice(
                        len(valveList), 0, "Device")
                    # get dictionary entry and pull out valveID
                    valveRecord = valveDict.get(valveDeviceChoice)
                    valveID = valveRecord[0]

                    # select relay that conrols valve
                    # Get list of all relays that are connected to the picoID
                    relayList = irigDB.getRelaysFromDevice(valveID)
                    relayDict = dict()
                    relayDict = printAndLoadDict(relayList, 0, 2, False, " ")
                    # Select relay from list
                    relayChoice = getListChoice(len(relayList), 0, "Relay")
                    # get dictionary entry and pull out relaID
                    relayRecord = relayDict.get(relayChoice)
                    relayID = relayRecord[0]
                    
                    #set status of device and chosen valve(relay) 
                    statusInput = getIntChoice(statusPrompt, genErrorPrompt, 2)
                    if statusInput == 1:
                        if irigDB.setValveStatus(valveID,relayID,1):
                            badEntry = False
                    elif statusInput == 2:
                        if irigDB.setValveStatus(valveID,relayID,-1):
                            badEntry = False
        elif firstInput == 4:
            print("Leaving...Goodbye :)")
            running = False
        else:
            print("invalid entry please try again")

if __name__ == '__main__':
    main()
