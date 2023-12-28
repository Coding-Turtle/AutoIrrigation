import sqlite3
import time
import datetime

class DBTools():
    def __init__(self, dbname, backupName):
        self.dbname = dbname
        self.backupName = backupName

    def __str__(self):
        return f"db name = {self.dbname}"
    #DONE
    def dbConnect(self):
        # set default cursor to None
        connection = None
        # try to connect to the database
        try:
            connection = sqlite3.connect(
                f"file:{self.dbname}.db?mode=rw", uri=True)
        except sqlite3.OperationalError:
            print('SQL ERROR with connect')
        # return connection object if made, else return None
        return connection

    def createDB(self):
        # try to connect to the database if exists
        try:
            connection = sqlite3.connect(
                f"file:{self.dbname}.db?mode=rw", uri=True)
        # if the database does not exist, send flag and create new db
        except sqlite3.OperationalError:
            print("db doesnt exist, creating new")
            # make new database file
            connection = sqlite3.connect(f"{self.dbname}.db")
            # make a cursor
            cur = connection.cursor()

            # create tables(make to check if exists?)

            cur.execute("""CREATE TABLE "Job" (
				"Job_ID"	INTEGER NOT NULL,
				"Job_Name"	TEXT NOT NULL,
				PRIMARY KEY("Job_ID" AUTOINCREMENT)
			)""")

            cur.execute("""CREATE TABLE "PlantSettings" (
				"Plant_ID"	INTEGER NOT NULL,
				"Plant_Name"	TEXT NOT NULL,
				"MoistureLow"	INTEGER NOT NULL,
				"MoistureHigh"	INTEGER NOT NULL,
				PRIMARY KEY("Plant_ID" AUTOINCREMENT)
			)""")

            cur.execute("""CREATE TABLE "Devices" (
				"Device_ID"		INTEGER NOT NULL,
				"Device_Name"	TEXT NOT NULL,
				"Plant_ID"	INTEGER,
				"Job_ID"	INTEGER NOT NULL,
				"Valve_ID" INTEGER,
				"INOUT" INTEGER NOT NULL,
				"Status"	INTEGER NOT NULL,
                "Cal"       Integer,
				"Last_Touched" TIMESTAMP,
				PRIMARY KEY("Device_ID" AUTOINCREMENT),
				FOREIGN KEY("Plant_ID") REFERENCES "PlantSettings"("Plant_ID"),
				FOREIGN KEY("Job_ID") REFERENCES "Job"("Job_ID"),
				FOREIGN KEY("Valve_ID") REFERENCES "ValveLut"("Valve_ID")
			)""")

            cur.execute("""CREATE TABLE "ValveLut"(
				"Valve_ID" INTEGER NOT NULL,
				"Device_ID" INTEGER NOT	NULL,
				"Relay" INTEGER NOT NULL,
                "Status" INTEGER NOT NULL,
				PRIMARY KEY("Valve_ID" AUTOINCREMENT),
				FOREIGN KEY("Device_ID") REFERENCES "Devices"("Device_ID")
			)""")
            
            cur.execute("""CREATE TABLE "MoistCalTable"(
				"Device_ID" INTEGER NOT NULL,
				"LastTotal" INTEGER NOT NULL,
                "LastTime" TIMESTAMP,
				PRIMARY KEY("Device_ID")
			)""")

            cur.execute("""CREATE TABLE "HistoricalMoisture" (
				"Plant_ID"	INTEGER NOT NULL,
				"Time"	TIMESTAMP NOT NULL,
				"Device_ID"	INTEGER NOT NULL,
				"MoistureRecord"	INTEGER NOT NULL,
				PRIMARY KEY("Plant_ID","Time","Device_ID")
			)""")

            cur.execute("""CREATE TABLE "HistoricalWater" (
				"Device_ID"	INTEGER NOT NULL,
				"Time"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				"Gallons"	INTEGER NOT NULL,
				PRIMARY KEY("Device_ID","Time")
			)""")

            cur.execute("""CREATE TABLE "TodoList" (
				"Device_ID"	INTEGER NOT NULL,
                "CalFlag" INTEGER NOT NULL,
				"Time"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				PRIMARY KEY("Device_ID")
			)""")

            # commit to database
            connection.commit()

            # close the connection
            connection.close()
        # note if db exists
        else:
            print(self.dbname)
            connection.close()

    def backupDB(self):
        source = sqlite3.connect(f"{self.dbname}.db")
        destination = sqlite3.connect(f"{self.backupName}.db")

        with destination:
            source.backup(destination, pages=1)
        destination.close()
        source.close()
        print("backed up")

    # DONE
    def createJob(self, clientID):
        # set rc to false if job not created
        rc = False
        calFlag = 0
        insertRecord = None
        deviceRecord = None
        # QUERIES
        selectQuery = f"SELECT * FROM Devices WHERE Device_Name = '{clientID}';"

        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that connection exists
        if cur != None:
            # Find device being read
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            # check that query pulls a record
            if deviceRecord != None:
                # sleep to avoid duplicate entry
                time.sleep(1)
                #check if device needs calibrated, if so set flag
                if deviceRecord[7] == None:
                    calFlag = -1
                #else pass ammount of water to use
                else:
                    calFlag = deviceRecord[7]
                # try to insert device into job table, if a job exists throws integrity error
                # for device do nothing
                insertQuery = f"INSERT INTO TodoList (Device_ID,CalFlag) Values({deviceRecord[0]},{calFlag});"
                insertRecord = self.tryChange(insertQuery, cur)
        # commit to db and close for finishing
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)
        
        print(f'insertRecord is {insertRecord}')
        
        # Check that commit,close, and insert success
        if (insertRecord != False) and insertRecord != None and commitCode and closeCode:
            print(f"{clientID} logged to Todo List")
            # set rc to true
            rc = True

        # return if job created or not
        return rc

    # DONE
    def getJobs(self):
        # make list to store jobs
        tempList = []

        # select Query
        selectJob = f"SELECT * FROM TodoList ORDER BY Time DESC;"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # Find device being read Check that connection made
        if cur != None:
            # get all jobs in todo List
            jobRecord = self.trySearch(selectJob, cur, "all")
            # check that records exist
            if jobRecord != None:
                # loop through records
                for x in jobRecord:
                    # add job and calibrate flag to list
                    tempList.append((x[0],x[1]))
                    print(tempList)
                    # try to delete job from todoList
                    deleteQuery = f"DELETE FROM TodoList WHERE Device_ID = {x[0]}"
                    deleteRecord = self.trySearch(deleteQuery, cur, "one")
        # commit changes to db and close connection
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)
        # return list of jobs to do
        return tempList

    # DONE
    def addReading(self, clientName, moistureLvl):
        # set rc
        rc = False
        deviceRecord = None
        insertRecord = None
        timeRecord = None
        # select Query
        selectQuery = f"SELECT * FROM Devices WHERE Device_Name = '{clientName}';"
        updateQuery = f"UPDATE Devices SET Last_Touched = CURRENT_TIMESTAMP WHERE Device_Name = '{clientName}';"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find device being read
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            print(deviceRecord)
            # Check that device exists in db
            if deviceRecord != None:
                # add sleep time to ensure duplicate entry is not entered into database when computer comes back up from sleep mode
                time.sleep(1)
                insertQuery = f"INSERT INTO HistoricalMoisture VALUES({deviceRecord[2]},CURRENT_TIMESTAMP,{deviceRecord[0]},{moistureLvl})"
                # insert reading to moisture levels historical tracker
                insertRecord = self.tryChange(insertQuery, cur)
                if insertRecord:
                    # set last touched on device
                    timeRecord = self.tryChange(updateQuery, cur)
                    # set rc to True if entry made
                    rc = True
        # commit to db and close for finishing
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)
        # check that db commit,closed, and insert success
        if (insertRecord != False) and (timeRecord != False) and commitCode and closeCode:
            rc = True
        # return if add success or failed
        return rc

    # DONE
    def checkWater(self, clientName, moistureLvl):
        # return code will be 1 if needs water, 0 if doesnt need water,-1 if Error
        rc = -1

        # select query for devices and settings
        selectDeviceSettings = f"""SELECT d.Device_Name,d.Plant_ID,p.MoistureLow,p.MoistureHigh
						FROM Devices d
						INNER JOIN PlantSettings p
						ON d.Plant_ID = p.Plant_ID
						WHERE d.Device_Name = '{clientName}';
					"""
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that connection made
        if cur != None:
            # get record as tuple to check through moisture level requirements
            deviceRecord = self.trySearch(selectDeviceSettings, cur, "one")
            # close db
            closeCode = self.closeConnection(connection)
            # check that record exists
            if deviceRecord != None:
                # check if device below threshold of water requirements
                if moistureLvl < deviceRecord[2]:
                    rc = 1
                # if not below requirements, doesnt need water
                else:
                    rc = 0
        # return status of water
        print(f'returnCode is :{rc}')
        return rc

    def getWaterReqs(self,clientID):
        #set record to None, will return if query fails
        deviceRecord = None

        # select query for devices and settings
        selectDeviceSettings = f"""SELECT d.Device_ID,d.Plant_ID,p.MoistureLow,p.MoistureHigh
						FROM Devices d
						INNER JOIN PlantSettings p
						ON d.Plant_ID = p.Plant_ID
						WHERE d.Device_ID = '{clientID}';
					"""
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that connection made
        if cur != None:
            # get record as tuple to check through moisture level requirements
            deviceRecord = self.trySearch(selectDeviceSettings, cur, "one")
            # close db
            closeCode = self.closeConnection(connection)

        #return device water settings
        return deviceRecord
        
    def getValveStatus(self,valveID):
        deviceRecord = None
        
        selectQuery = f"SELECT Status FROM ValveLUT WHERE Valve_ID = '{valveID}';"
        
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find device being read
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            # check that device exists
            if deviceRecord == None:
                print("no record")
            else:
                print(deviceRecord)
                # close db
        closeCode = self.closeConnection(connection)
        # return record of valve, if no record return None
        return deviceRecord
        
        
    def setValveStatus(self,deviceID,relay,code):
        deviceRecord = None
        rc = False
        updateQuery = f"UPDATE ValveLut SET Status = {code} WHERE Device_ID = {deviceID} and Relay = {relay};"
        #print(updateQuery)
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # try update
            deviceRecord = self.tryChange(updateQuery, cur)
            # check that change happened
            if deviceRecord == False:
                print("Update Failed")
            else:
                rc = True
                # commit db
                commitCode = self.commitQuery(connection)
                #print(deviceRecord)
        #close db
        closeCode = self.closeConnection(connection)
        # return record of valve, if no record return None
        return rc
        
        
    def setStatus(self,deviceID,code):
        deviceRecord = None
        rc = False
        updateQuery = f"UPDATE Devices SET Status = {code} WHERE Device_ID = {deviceID};"
        print(updateQuery)
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # try update
            deviceRecord = self.tryChange(updateQuery, cur)
            # check that change happened
            if deviceRecord == False:
                print("Update Failed")
            else:
                rc = True
                # commit db
                commitCode = self.commitQuery(connection)
                print(deviceRecord)
        #close db
        closeCode = self.closeConnection(connection)
        # return record of valve, if no record return None
        return rc
    #Done
    def getDevice(self,clientName):
        deviceRecord = None
        
        selectQuery = f"SELECT * FROM Devices WHERE Device_Name = '{clientName}';"
        
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find device being read
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            # check that device exists
            if deviceRecord == None:
                print("no record")
            else:
                print(deviceRecord)
                # close db
        closeCode = self.closeConnection(connection)
        # return record of valve, if no record return None
        return deviceRecord
    
    #TODO else if update fails fix
    def getCalibrate(self,deviceID,currMoist,needWater):
        shouldCal = False
        maxWait = 7200
        calibrationRecord = None
        selectQuery = f"SELECT * FROM MoistCalTable WHERE Device_ID = {deviceID}"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            calibrationRecord = self.trySearch(selectQuery,cur,"one")
            #get if device needs watered
            
            print(f"calibrationRecord is {calibrationRecord}")
            #check table, if no record, and below threshold create new
            if calibrationRecord == None and needWater == 1:
                createQuery = f"INSERT INTO MoistCalTable (Device_ID, LastTotal, LastTime) VALUES ({deviceID},0,CURRENT_TIMESTAMP)"
                change = self.tryChange(createQuery,cur)
                print(f"change is {change}")
                #if time access within x hours, calibrate
                # commit to db and close for finishing
                #set should Cal if insert and commit worked
                commitCode = self.commitQuery(connection)
                #close DB
                closeCode = self.closeConnection(connection)
                if change == True and commitCode == True:
                    shouldCal = True

            #else if record check time access
            else:
                curTime = datetime.datetime.now(datetime.timezone.utc) 
                lastCalTime = datetime.datetime.strptime(calibrationRecord[2], '%Y-%m-%d %H:%M:%S')
                diff = curTime - lastCalTime.replace(tzinfo=datetime.timezone.utc)
                print(f"last cal time is {lastCalTime}")
                print(f"curTime is {curTime}")
                print(type(diff))
                print(f"diftime is {diff.total_seconds()}")
                print(f"maxwait is {maxWait}")
                #close DB
                closeCode = self.closeConnection(connection)
                #if has been longer than 2 hours since last calibration set cal to true
                if diff.total_seconds() > maxWait:
                    #check if our moisture is passed the upper
                    moistSettings = self.getWaterReqs(deviceID)
                    #we have met the requirements calibration finished
                    if moistSettings != None and moistSettings[3] < currMoist:
                        #take 20% off water used, and add remainder to final cal to account for error
                        calculatedUsed = calibrationRecord[1]-calibrationRecord[1]*0.20
                        finishRes = self.finalCal(deviceID,calculatedUsed)
                        #if updated delete from calibration table
                        if finishRes == True:
                            deleteRes = self.deleteCal(deviceID)
                    #if we have not met requirements, calibrate
                    else:
                        shouldCal = True

        
        return shouldCal
    #Done
    def setCalibrate(self,valveID,used):
        deviceID = None
        updateRecord = None
        selectQuery = f"""SELECT Device_ID FROM Devices WHERE Valve_ID = {valveID}
					"""

        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # add sleep time to ensure duplicate entry is not entered into database when computer comes back up from sleep mode
            time.sleep(1)
            # Check that clientID exists
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            # check that clientID in database
            if deviceRecord != None:
                updateQuery = f"""UPDATE MoistCalTable Set LastTotal = LastTotal + {used},
                            LastTime = CURRENT_TIMESTAMP WHERE Device_ID = {deviceRecord[0]}
                            """
                #update record with new water calibration
                calRecord = self.tryChange(updateQuery, cur)
        # commit to db and close for finishing
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)
        # check that db commit, closed, and Record has been returned showing success in assign
        if commitCode and (calRecord != None):
            # set assigned to true, plant has been assigned to device
            updated = True

        # return if assigned or not
        return updated
    
    def deleteCal(self,deviceID):
        #set success to false, if no delete will return
        success = False
        deviceRecord = None

        #delete query for calibration table
        deleteCalibrationRecord = f"""DELETE FROM MoistCalTable WHERE Device_ID = '{deviceID}';
					"""
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that connection made
        if cur != None:
            # get record as tuple to check through moisture level requirements
            deviceRecord = self.tryChange(deleteCalibrationRecord, cur)
            # close db
            commitCode = self.commitQuery(connection)
            closeCode = self.closeConnection(connection)
            #check that we have a record of change and commit to db if so success
            if deviceRecord == True and commitCode == True:
                success = True
        #return successfull delete
        return success

    def finalCal(self,deviceID,calWater):
        # set assigned to False return if no plant assigned
        updated = False
        deviceRecord = None
        calRecord = None
        # query to select devices
        selectQuery = f"SELECT * FROM DEVICES WHERE Device_ID = {deviceID}"
        # query to update plant to device
        updateQuery = f"UPDATE Devices SET Cal = {calWater} WHERE Device_ID = {deviceID};"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # add sleep time to ensure duplicate entry is not entered into database when computer comes back up from sleep mode
            time.sleep(1)
            # Check that clientID exists
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            # check that clientID in database
            if deviceRecord != None:
                #update record with new water calibration
                calRecord = self.tryChange(updateQuery, cur)
        # commit to db and close for finishing
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)
        # check that db commit, closed, and record has been returned showing success in assign
        if commitCode and (calRecord != None):
            # set assigned to true, plant has been assigned to device
            updated = True

        # return if assigned or not
        return updated
    # DONE
    def getValve(self, clientID):
        # set record to none, returns if no valve found
        lutRecord = None
        deviceRecord = None
        # selectQuery for device
        selectQuery = f"SELECT * FROM Devices WHERE Device_ID = '{clientID}';"

        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find device being read
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            # check that device exists
            if deviceRecord != None:
                name = deviceRecord[1]
                # get LUT ID Query
                lutIDQuery = f"""SELECT v.Valve_ID,v.Device_ID,v.Relay,d.Device_Name,v.Status
							FROM ValveLut v
							INNER JOIN Devices d
							ON v.Device_ID = d.Device_ID
							WHERE v.Valve_ID = '{deviceRecord[4]}'
						    """
                # RETURN with LUTID, DEV_ID,RELAY NUMBER, & device name
                lutRecord = self.trySearch(lutIDQuery, cur, "one")
                # TODO TEMP SET FOR DISPLAYING TROUBLSHOOTING, LOG IF NO RECORD
                if lutRecord == None:
                    print("no record")
                else:
                    print(
                        f"Need to water using device {lutRecord[3]}, Relay {lutRecord[2]} to water device {name}")
                # close db
        closeCode = self.closeConnection(connection)
        # return record of valve, if no record return None
        return lutRecord

    # TODO Dont allow duplicate
    def addValveLut(self, clientID, relayCount):
        # return list of newIDs added to LUT
        newID = []
        insertRecord = None
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            print("cur")
            # add sleep time to ensure duplicate entry is not entered into database when computer comes back up from sleep mode
            time.sleep(1)
            # Try to create list of NewIDs entered to ValveLut
            for x in range(relayCount):
                # Removing zero based index for database purposes
                relayEntry = x + 1
                # insert adjusted relay entry into Valve lut
                insertQuery = f"INSERT INTO ValveLut (Device_ID,Relay,Status) VALUES ({clientID},{relayEntry},1)"
                insertRecord = self.tryChange(insertQuery, cur)

                if insertRecord:
                    print(cur.lastrowid)
                    # add newId to list
                    newID.append(cur.lastrowid)
                    print(newID)
                else:
                    # add -1 if error inserting record
                    newID.append(-1)
        # check if error with adding valve
        if -1 not in newID:
            # if no error, commit query
            codeCommit = self.commitQuery(connection)
        else:
            # if error, set commit to false and dont commit query to db
            codeCommit = False
        codeClose = self.closeConnection(connection)
        # check that commit success
        if codeCommit != True:
            # if no success clear id list and append -1
            newID.clear()
            newID.append(-1)
        # returns newID List, if error with adding newID will add -1 to list
        return newID

    # DONE
    def addDevice(self, jobID, valveID, plantID, location):
        # set newID to -1 default if error
        newID = -1
        lastID = -1

        # DataPoints
        newDeviceName = None

        # Oueries
        selectQuery = f"SELECT * FROM DEVICES WHERE Job_ID = {jobID} ORDER BY  Device_ID DESC"

        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)

        # check that the connection was made
        if cur != None:
            # add sleep time to ensure duplicate entry is not entered into database when computer comes back up from sleep mode
            time.sleep(1)
            # get all devices of job type
            jobRecord = self.trySearch(selectQuery, cur, "one")
            # check if there is an entry in the database and assign newDeviceName
            if jobRecord == None:
                #if light/temp meter
                if jobID == 3:
                    valveID = 'Null'
                    plantID = 'Null'
                    newDeviceName ='light_temp1'
                # if valveJob
                elif jobID == 2:
                    valveID = 'Null'
                    plantID = 'Null'
                    newDeviceName = 'valve1'
                # if moisture job
                elif jobID == 1:
                    newDeviceName = 'moisture1'
                else:
                    print("incorrect entry, no Device added")
            # there already exists a device of this type in the database
            else:
                # get name from record
                name = jobRecord[1]
                #if light/temp meter
                if jobID == 3:
                    valveID = 'Null'
                    plantID = 'Null'
                    # index to number that device name is cast as int
                    count = int(name[10:])
                    # increment count for new device being added
                    count = count + 1
                    # create new device name
                    newDeviceName = f"light_temp{count}"
                
                # if job is a valve, enter this controll flow
                elif jobID == 2:
                    valveID = 'Null'
                    plantID = 'Null'
                    # index to number that device name is cast as int
                    count = int(name[5:])
                    # increment count for new device being added
                    count = count + 1
                    # create new device name
                    newDeviceName = f"valve{count}"

                # if jobe is moisture meter enter here
                elif jobID == 1:
                    # index to number that device name is cast as int
                    count = int(name[8:])
                    # increment count for new device being added
                    count = count + 1
                    # create new device name
                    newDeviceName = f"moisture{count}"
                # print if incorrect entry
                else:
                    print("incorrect entry, no Device added")
            # try to execute insert
            insertQuery = f"""INSERT INTO Devices(Device_Name,Plant_ID,Job_ID,Valve_ID,INOUT,Status) VALUES ("{newDeviceName}",{plantID},{jobID},{valveID},{location},1)"""
            insertRecord = self.tryChange(insertQuery, cur)

            if insertRecord != False:
                # get id of recently created entry
                lastID = cur.lastrowid

        # commit to db and close for finishing
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)

        # Check that db commited, closed, and lastID exists
        if commitCode and closeCode and (lastID != -1):
            newID = lastID
        print(newID)
        # return deviceID
        return newID

    # DONE
    def getNextID(self, table):
        # set nextID default to -1
        nextID = -1
        # nextID Query
        nextIDQuery = f"SELECT * FROM sqlite_sequence WHERE name = '{table}' ORDER BY DESC;"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made, if no connection made l
        if cur != None:
            # get next ID that will be made in the given table
            nextIDRecord = self.trySearch(nextIDQuery, cur, "one")
            # check if ID returned
            if nextIDRecord != None:
                # increment ID and return nextID
                nextID = int(nextIDRecord[1])+1
            # if None returned, set nextID to 1
            elif nextIDRecord == None:
                nextID = 1
        # close db
        closeCode = self.closeConnection(connection)

        # return next ID to be used, -1 if error occured
        return nextID

    # DONE
    def getAllPlants(self):
        # pull all plant names and Plant_ID add to List
        plantRecords = None

        # query to get all plants
        plantQuery = f"SELECT Plant_ID,Plant_Name FROM PlantSettings ORDER BY Plant_Name ASC;"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find all plants in database, order list by earliest created
            plantRecords = self.trySearch(plantQuery, cur, "all")

            # close db
        closeCode = self.closeConnection(connection)
        # return record of all plants in database, None if error or No plants
        return plantRecords

    # DONE
    def getAllDevicesOfType(self, job):
        #Record to return 
        deviceRecord = None
        # select devices of jobtype query
        selectOfJob = f"SELECT * FROM Devices WHERE Job_ID = {job} ORDER BY Device_ID Desc;"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find all plants in database, order list by earliest created
            deviceRecord = self.trySearch(selectOfJob, cur, "all")

        # close db
        connection.close()
        # return device record if success, else return None
        return deviceRecord
    
    def getLocation(self,clientID):
        
        #Record to return 
        deviceRecord = None
        # select devices of jobtype query
        selectLocation = f"SELECT INOUT FROM Devices WHERE Device_ID = '{clientID}';"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find all plants in database, order list by earliest created
            deviceRecord = self.trySearch(selectLocation, cur, "one")

        # close db
        connection.close()
        # return device record if success, else return None
        return deviceRecord

    # DONE
    def assignPlant(self, clientID, PlantID):
        # set assigned to False return if no plant assigned
        assigned = False
        deviceRecord = None
        plantRecord = None
        # query to select devices
        selectQuery = f"SELECT * FROM DEVICES WHERE Device_ID = {clientID}"
        # query to update plant to device
        updateQuery = f"UPDATE Devices SET Plant_ID = {PlantID} WHERE Device_ID = {clientID};"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # add sleep time to ensure duplicate entry is not entered into database when computer comes back up from sleep mode
            time.sleep(1)
            # Check that clientID exists
            deviceRecord = self.trySearch(selectQuery, cur, "one")
            # check that clientID in database
            if deviceRecord != None:
                # add plant type to device
                plantRecord = self.trySearch(updateQuery, cur, "one")
        # commit to db and close for finishing
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)
        # check that db commit, closed, and plantRecord has been returned showing success in assign
        if commitCode and closeCode and (plantRecord != None):
            # set assigned to true, plant has been assigned to device
            assigned = True

        # return if assigned or not
        return assigned

    # DONE
    def createPlant(self, plantName, lowerBound, upperBound):
        # newID set to -1 returns if error
        newID = -1
        # query to insert into db
        insertQuery = f"INSERT INTO PlantSettings (Plant_Name,MoistureLow,MoistureHigh) Values('{plantName}',{lowerBound},{upperBound});"
        # make connection to database
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # sleep to avoid duplicate entry
            time.sleep(1)
            # try to insert device into job table, if a job exists already for device do nothing
            insertRecord = self.tryChange(insertQuery, cur)
            newID = cur.lastrowid
        # commit to db
        commitCode = self.commitQuery(connection)
        # check that commit success and insert success
        if commitCode and (insertRecord != False):
            # if success set newID to last id created
            newID = cur.lastrowid
        # close db connection
        closeCode = self.closeConnection(connection)
        # return newID if created, else return -1
        return newID

    # DONE
    def getRelaysFromDevice(self, deviceID):
        relayRecord = None
        # query to select relay from ValveLUT
        selectRelayQuery = f"SELECT * FROM ValveLut WHERE Device_ID = {deviceID} ORDER BY Device_ID ASC;"
        # pull all plant names and Plant_ID add to List
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find all plants in database, order list by earliest created
            relayRecord = self.trySearch(selectRelayQuery, cur, "all")

        # close db
        closeCode = self.closeConnection(connection)
        # return relays or None if no relays created
        return relayRecord

    # DONE
    def checkRelayAvailable(self, relayID):
        # set rc to default False for relay not available
        rc = False
        relayRecord = None
        # query for getting device
        selectRelayQuery = f"SELECT * FROM Devices WHERE Valve_ID = {relayID};"
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)

        # check that the connection was made
        if cur != None:
            # Find any device that uses this valveID
            # get record of device that uses valveID, returns None if not used
            relayRecord = self.trySearch(selectRelayQuery, cur, "one")
        # close db
        closeCode = self.closeConnection(connection)
        # check if valveID is not used
        if relayRecord == None:
            # set rc to true as the valveID is free
            rc = True
        # return if valve can be assigned or not
        return rc

    # DONE
    def checkPlantExists(self, plantName):
        # default rc to false, return if name not available
        rc = False
        selectPlantQuery = f"""SELECT * FROM PlantSettings WHERE Plant_Name = '{plantName}';"""
        # try-catch to connect to database
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find if plant Name is in database
            # get record of plant that uses given name, returns None if not used
            plantRecord = self.trySearch(selectPlantQuery, cur, "one")
            # close db
            closeCode = self.closeConnection(connection)
            # check if plant name  is not used
            if plantRecord == None:
                # set rc to true as the plant name is free
                rc = True
            # return if plant name can be assigned or not
            return rc

    # DONE
    def displayDevice(self, deviceID):
        # store string to print and dictionary to store records
        deviceString = ''
        deviceDict = dict()

        selectJobQuery = f"""
                        SELECT d.Device_Name, j.Job_Name, d.Valve_ID,d.INOUT 
                        FROM Devices d Left JOIN Job j 
                        ON d.Job_ID =  j.Job_ID
                        WHERE d.Device_ID = {deviceID}
                        """

        selectPlantQuery = f"""
                        SELECT d.Device_Name, p.Plant_Name 
						FROM Devices d
						Left JOIN PlantSettings p
						ON d.Plant_ID =  p.Plant_ID
						WHERE d.Device_ID = {deviceID}
                        """
        selectRelayQuery = f"""
                            SELECT d.Device_Name, v.Relay, v.Device_ID
                            FROM Devices d
                            LEFT JOIN ValveLut v
                            ON d.Valve_ID= v.Valve_ID
                            WHERE d.Device_ID = {deviceID} ;
                            """

        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find device job from db for device
            jobRecord = self.trySearch(selectJobQuery, cur, "one")
            # Check that record has been returned
            if jobRecord != None:
                # store record and add to dictionary
                deviceDict.update({"Name:": jobRecord[0]})
                deviceDict.update({"Job:": jobRecord[1]})
                # add record to dictionary if inside or outside
                if (jobRecord[3] == 0):
                    deviceDict.update({"Location:": "Outside"})
                elif (jobRecord[3] == 1):
                    deviceDict.update({"Location:": "Inside"})
                else:
                    print("no choice")
                # Find device plant from db for device
                plantRecord = self.trySearch(selectPlantQuery, cur, "one")
                # check that record has been returned
                if plantRecord != None:
                    # store plant name to dictionary
                    deviceDict.update({"Plant: ": plantRecord[1]})
                    # check that device has a valve or not, if the device has a valve
                    # add valve and relay to records
                    if jobRecord[2] != None:
                        # get record of relay
                        relayRecord = self.trySearch(
                            selectRelayQuery, cur, "one")
                        # check that record returnes value
                        if relayRecord != None:
                            selectDeviceRelay = f"""SELECT Device_Name
                                            FROM Devices
                                            WHERE Device_ID = {relayRecord[2]}
                                            """
                            # get device information from relay record
                            controllerRecord = self.trySearch(
                                selectDeviceRelay, cur, "one")
                        # add controller and relay to dictionary if record returnes value
                            if controllerRecord != None:
                                deviceDict.update(
                                    {"Valve-Controller:": controllerRecord[0]})
                                deviceDict.update(
                                    {"Relay:": str(relayRecord[1])})

            # close db
            closeCode = self.closeConnection(connection)
            # loop through dictionary and append key/value to string for use with display
            for item in deviceDict:
                if deviceDict[item] != None:
                    deviceString = deviceString + item + deviceDict[item] + " "
        print(deviceString)
        # return the formatted string
        return deviceDict

    # DONE
    def addWaterUsage(self, usage, valveID):
        # set rc to False
        rc = False
        # set records to None
        recordSelect = None
        recordInsert = None

        # Queries for getting device
        selectQuery = f"SELECT * FROM Devices WHERE Valve_ID = '{valveID}';"

        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)

        # check that the connection was made
        if cur != None:
            # Find device that has matching valveID
            recordSelect = self.trySearch(selectQuery, cur, "one")
            # add sleep time to ensure duplicate entry is not entered into database when computer comes back up from sleep mode
            time.sleep(1)
            # check that record from first query was returned
            if recordSelect != None:
                # Query for inserting water usage to historical tracker
                insertQuery = f"INSERT INTO HistoricalWater (Device_ID,Time,Gallons) VALUES({recordSelect[0]},CURRENT_TIMESTAMP,{usage})"
                # insert reading of water usage levels to historical tracker
                recordInsert = self.tryChange(insertQuery, cur)

        # commit to db and close for finishing
        commitCode = self.commitQuery(connection)
        closeCode = self.closeConnection(connection)

        # check that record was inserted, commited, and connection closed
        if commitCode and closeCode and (recordInsert != False):
            rc = True
        # return record if inserted, None if nothing inserted
        return rc

    # DONE
    def commitQuery(self, connection):
        # set rc to false assume failure
        rc = False
        # try to commit query to database
        try:
            rc = connection.commit()
        # return error if unable to commit
        except sqlite3.OperationalError:
            print("Error: unabe to commit Query")
        # if commit succeeded set rc to true
        else:
            rc = True

        # return rc
        return rc

    # DONE
    def closeConnection(self, connection):
        # set rc to false assume failure
        rc = False
        # try to close database connection
        try:
            rc = connection.close()
        # return error if unable to close databasde
        except sqlite3.OperationalError:
            print("Error: unabe to Close Database")
        # if close succeeded set rc to true
        else:
            rc = True
        # return rc
        return rc

    # DONE
    def trySearch(self, query, cursor, fetch="one"):
        # set record to none
        record = None
        # try to execute the query given
        try:
            cursor.execute(query)
            # if error with query print error
        except sqlite3.OperationalError:
            print(f"Query Error: {query}")
        # if query successfull, set record to one, many, or all records
        else:
            if fetch == "one":
                record = cursor.fetchone()
            elif fetch == "many":
                record = cursor.fetchmany()
            elif fetch == "all":
                record = cursor.fetchall()
            else:
                record = None
        # return the record of the query that has been made
        return record

    def tryChange(self, query, cursor):
        # set success to false default
        success = False
        # try to execute the query given
        try:
            cursor.execute(query)
            # if error with query print error
        except sqlite3.OperationalError:
            print(f"Query Error: {query}")
        except sqlite3.IntegrityError:
            print(f"Integrity Error: {query}")
        # if query successfull, set record to one, many, or all records
        else:
            success = True
        # return the record of the query that has been made
        return success
    # DONE

    def createCursor(self, connection):
        # set default cursor to None
        cursor = None
        # try to create cursor from connection given
        try:
            cursor = connection.cursor()
        # print error if cursor unable to be created
        except sqlite3.OperationalError:
            print("Error: Cursor Not Created")
        # return cursor if created, none if unable to be created
        return cursor
    
    #look at last touched moisture recording, if outside time in minutes
    def getNotTouched(self,time):
        missedRecord = None
        
        #Query to select devices where they have not been touched it time limit given
        selectNotTouchedQuery = f"""SELECT Device_Name, Job_ID,strftime('%s',Last_Touched) as Past,strftime('%s','now') as Cur
                                    FROM  Devices 
                                    WHERE (Job_ID == 1 and Status == 1 and (Cur - Past)/60 > {time}) or (Job_ID == 1 and Status == 1 and Last_Touched IS NULL);"""
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find Record of all devices not touched in given Time
            missedRecord = self.trySearch(selectNotTouchedQuery, cur, "all")
            # close db
            closeCode = self.closeConnection(connection)
            
        #Return Record of devices outide time limit, None if no record exists
        return missedRecord
    
    
    #get sum of water usage for Grouped by week
    def getYtdWaterUsage(self):
        waterUsage = None
        #get current year
        year = datetime.datetime.now().year
        #query to get ytd water usage
        selectWaterQuery = f"""SELECT sum(w.Gallons),strftime('%Y-%m', w.Time) AS Month
                    FROM  HistoricalWater w LEFT JOIN Devices d
                    ON d.Device_ID =  w.Device_ID
                    WHERE strftime('%Y', w.Time) = '{year}'
                    GROUP BY Month;"""
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find Record of water usage
            waterUsage= self.trySearch(selectWaterQuery, cur, "all")
            # close db
            closeCode = self.closeConnection(connection)
            
        #Return Record of water usage ytd
        return waterUsage
    
    
    #TODO: get sum of devices per day for the last week
    def getWtdUsage(self):
        #variable to store water usage
        weeklyUsage = None
        #calculate 7 days ago date
        todayDate = datetime.datetime.now()
        pastWeek = todayDate - datetime.timedelta(days=7)
        pastWeek = pastWeek.strftime('%Y-%m-%d')
        print(pastWeek)
        #query to get weekly water usage
        selectWTDQuery = f"""SELECT SUM(w.Gallons) AS Gallons,strftime('%Y-%m-%d',w.time) AS Week
                            FROM HistoricalWater w
                            WHERE w.time > '{pastWeek}'
                            GROUP BY Week;"""
        
        
        #creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find Record of all waterUsage
            waterUsage = self.trySearch(selectWTDQuery, cur, "all")
            # close db
            closeCode = self.closeConnection(connection)
            
        #Return Record of water usage wtd
        return waterUsage
    
    def getMoisture(self,deviceName):
        waterUsage = None
        year = datetime.datetime.now().year

        selectWaterQuery = f"""SELECT d.Device_Name, m.Time, m.MoistureRecord
                            FROM HistoricalMoisture m LEFT JOIN Devices d
                            ON m.Device_ID = d.Device_ID
                            WHERE d.Device_Name = "{deviceName}"
                            ORDER BY m.Time ASC;"""
        # creat connection do database
        connection = self.dbConnect()
        # create cursor
        cur = self.createCursor(connection)
        # check that the connection was made
        if cur != None:
            # Find Record of all devices not touched in given Time
            waterUsage= self.trySearch(selectWaterQuery, cur, "all")
            # close db
            closeCode = self.closeConnection(connection)
            
        #Return Record of devices outide time limit, None if no record exists
        return waterUsage
    
    
