# Updates Warehouse instance with Workspace instance
# Run directly on server Southern
# Updated 2/2017 for new server

import sys, string, os, time, math, arcpy
from datetime import datetime, date

timestart = str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))

try:
    # figure out the date range to search for updates
    updateWindow = 7 # Number of days in past to look for updates
    startDate = date.fromordinal(date.toordinal(date.today()) - updateWindow)
    endDate = date.today()
    theQ = "\"UPDATE_DATE\" >= '" + str(startDate) + "' AND \"UPDATE_DATE\" <= '" + str(endDate) + "' AND \"PUBLIC_ACCESS\" = 'Y'"

    # set source tables for dataset updates
    outputSDE  = "Database Connections\\Atlantic Warehouse (sangis user).sde"    
    outputGDB  = "D:\\sde_maintenance\\pds_out.gdb"
    outTable   = outputSDE + "\\SDE.SANGIS.LUEG_UPDATES"
    inputSDE   = "Database Connections\\Atlantic Workspace (pds user).sde"
    inputTable = inputSDE + "\\SDW.PDS.LUEG_UPDATES"
    adminSDE   = "Database Connections\\Atlantic Warehouse (sa user).sde"
    
    # Delete old working GDB, if exists
    if arcpy.Exists(outputGDB):
        arcpy.Delete_management(outputGDB)
    
    # check to see if there have been any updates
    s1 = arcpy.SearchCursor(str(inputTable), str(theQ))
    s1row = s1.next()
    layerCount = 0
    while s1row:
        layerCount = layerCount + 1
        s1row = s1.next()
    del s1, s1row
    print "Layer count: " + str(layerCount)
        
    # check to make sure there are datasets that need to be copied
    if (layerCount > 0):
        # create log file
        oldOutput = sys.stdout
        logFileName = "D:\\sde_maintenance\\log\\updateWarehouseFromWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt"
        logFile = open(logFileName,"w")
        sys.stdout = logFile
        
        print "START TIME: " + str(timestart)
        print "Copying datasets updated between " + str(startDate) + " and " + str(endDate)

        # Disconnect users from the database (added 3/12/13)
        try:
            usrList = arcpy.ListUsers(adminSDE)
            for user in usrList:
                if user.Name[1:5] == "BLUE":
                    arcpy.DisconnectUser(adminSDE,user.ID)
        except:
            print "ERROR"
            print arcpy.GetMessages()
    
        
        # Go through each dataset recently updated
        c = arcpy.SearchCursor(inputTable,theQ)
        r = c.next()
        while r:
            try:
                # Delete old version if it exists
                outLayer = outputSDE + "\\SDE.SANGIS." + str(r.LAYER_NAME)
                inputDS = inputSDE + "\\SDW.PDS." + str(r.FEATURE_DATASET)
                arcpy.env.workspace = inputDS
                inLayer  = inputDS + "\\SDW.PDS." + str(r.LAYER_NAME)
                
                if arcpy.Exists(outLayer):
                    print "Deleting " + str(r.LAYER_NAME) + " from Warehouse..."
                    arcpy.Delete_management(outLayer)
                
                # Copy dataset from LUEG and create fc for distribution
                print "Copying " + str(r.LAYER_NAME) + " from Workspace to Warehouse..."
                arcpy.FeatureClassToFeatureClass_conversion(inLayer, outputSDE, str(r.LAYER_NAME))
                
                # Change privileges
                print "Granting privileges to " + str(r.LAYER_NAME) + "..."
                arcpy.ChangePrivileges_management(outLayer,"SDE_VIEWER","GRANT","AS_IS")
                print ""
            except:
                print "*********************** ERROR WITH " + str(r.LAYER_NAME) + " *****************"
                print arcpy.GetMessages()
            r = c.next()
        del c, r
        
        # Update WAREHOUSE table with PDS table
        c1 = arcpy.SearchCursor(inputTable)
        r1 = c1.next()
        while r1:
            theName = r1.LAYER_NAME
            theDate = r1.UPDATE_DATE
            r1 = c1.next()

            print "Checking " + str(theName) + " for " + str(theDate) + "..."

            itExists = "N"
            c2 = arcpy.UpdateCursor(outTable,"\"LAYER_NAME\" = '" + theName + "'")
            r2 = c2.next()
            while r2:
                itExists = "Y"
                r2.LAYER_NAME = theName
                r2.UPDATE_DATE = str(theDate)
                r2.RESPONSIBLE_PARTY = "LUEG"
                c2.updateRow(r2)
                r2 = c2.next()
            del c2,r2
            
            # Add to the manifest if doesn't exist
            if itExists == "N":
                print "Adding " + str(theName) + " to the Warehouse table..."
                c3 = arcpy.InsertCursor(outTable)
                r3 = c3.newRow()
                r3.LAYER_NAME = theName
                r3.UPDATE_DATE = str(theDate)
                r3.RESPONSIBLE_PARTY = "LUEG"
                c3.insertRow(r3)
                del c3, r3
            
        del c1, r1
            
    print ""
    print "Copied " + str(layerCount) + " datasets from Workspace to Warehouse..."
    print "END TIME: " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))

    logFile.close()
    sys.stdout = oldOutput
except:
    print "ERROR in D:\\sde_maintenance\\scripts\\updateWarehouseFromWorkspace.py at " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
    print arcpy.GetMessages()
    logFile.close()
    sys.stdout = oldOutput

    # email
    import smtplib, ConfigParser
    from email.mime.text import MIMEText
    
    config = ConfigParser.ConfigParser()
    config.read(r"D:\sde_maintenance\scripts\configFiles\accounts.txt")
    email_usr = config.get("email","usr")
    email_pwd = config.get("email","pwd")
    
    fp = open(logFileName,"rb")
    msg = MIMEText(fp.read())
    fp.close()
    
    fromaddr = "dplugis@gmail.com"
    toaddr = ["gary.ross@sdcounty.ca.gov",]
    
    msg['Subject'] = "ERROR when updating WAREHOUSE with WORKSPACE"
    msg['From'] = "Python Script"
    msg['To'] = "SDE Administrator"
    
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(email_usr,email_pwd)
    s.sendmail(fromaddr,toaddr,msg.as_string())
    s.quit()
