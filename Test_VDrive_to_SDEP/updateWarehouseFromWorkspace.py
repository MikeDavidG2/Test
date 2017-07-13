#-------------------------------------------------------------------------------
# Name:        updateWarehouseFromWorkspace.py
# Purpose:
"""
Updates Warehouse instance with Workspace instance
NOTE: Run directly on server Southern

UPDATES:
  February 2017:
    Upgraded ArcGIS to 10.4.1 and new server
  July 2017:
    Allowed tables in SDW (Workspace) to update SDE (Warehouse).
    The process is controlled by the data in the LUEG_UPDATES table in SDW.
    Any dataset within the 'updateWindow' will be copied over.
"""
#
# Author:      Gary Ross
# Editors:     Gary Ross, Mike Grue
#-------------------------------------------------------------------------------

import sys, string, os, time, math, arcpy
from datetime import datetime, date

arcpy.env.overwriteOutput = True  #  MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing

timestart = str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))

try:
    # figure out the date range to search for updates
    updateWindow = 7 # Number of days in past to look for updates
    startDate = date.fromordinal(date.toordinal(date.today()) - updateWindow)
    endDate = date.today()
    theQ = "\"UPDATE_DATE\" >= '" + str(startDate) + "' AND \"UPDATE_DATE\" <= '" + str(endDate) + "' AND \"PUBLIC_ACCESS\" = 'Y'"
    theQ = "\"UPDATE_DATE\" >= date '" + str(startDate) + "' AND \"UPDATE_DATE\" <= date '" + str(endDate) + "' AND \"PUBLIC_ACCESS\" = 'Y'"  # MG 07/12/17: Set variable to DEV settings.  TODO: Why did I need to do this?  How is it working on SOUTHERN?

    # set source tables for dataset updates
    outputSDE  = "Database Connections\\Atlantic Warehouse (sangis user).sde"
    outputSDE  = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDE.gdb'  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
##    outputGDB  = "D:\\sde_maintenance\\pds_out.gdb"  # MG 07/12/17: I believe that this variable isn't needed and can be deleted.  TODO: Ask Gary
    outTable   = outputSDE + "\\SDE.SANGIS.LUEG_UPDATES"
    outTable   = outputSDE + '\\LUEG_UPDATES'  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
    inputSDE   = "Database Connections\\Atlantic Workspace (pds user).sde"
    inputSDE   = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDW.gdb'
    inputTable = inputSDE + "\\SDW.PDS.LUEG_UPDATES"
    inputTable = inputSDE + '\\LUEG_UPDATES'  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
    adminSDE   = "Database Connections\\Atlantic Warehouse (sa user).sde"

# MG 07/12/17: I believe that the commented out below isn't used and can be deleted.  TODO: Ask Gary
##    # Delete old working GDB, if exists
##    if arcpy.Exists(outputGDB):
##        arcpy.Delete_management(outputGDB)

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
        logFileName = r"U:\grue\Projects\VDrive_to_SDEP_flow\log\updateWarehouseFromWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt"  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
        logFile = open(logFileName,"w")
        sys.stdout = logFile

        print "START TIME: " + str(timestart)
        print "Copying datasets updated between " + str(startDate) + " and " + str(endDate)
        print '----------------------------------------------------------------'  # MG 07/12/17:  Added print statement

        # Disconnect users from the database (added 3/12/13)
        try:
            usrList = arcpy.ListUsers(adminSDE)
            for user in usrList:
                if user.Name[1:5] == "BLUE":
                    arcpy.DisconnectUser(adminSDE,user.ID)
        except:
            print "*** ERROR with Disconnecting users from the database ***"
            print arcpy.GetMessages()


        # Go through each dataset recently updated
        c = arcpy.SearchCursor(inputTable,theQ)
        r = c.next()
        while r:
            try:
                # Set path for the output
                outLayer = outputSDE + "\\SDE.SANGIS.{}".format(r.LAYER_NAME)
                outLayer = outputSDE + "\\SDE.SANGIS.{}".format(r.LAYER_NAME)  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
                #---------------------------------------------------------------
                #---------------------------------------------------------------
                # START MG 07/12/17:  Added below to account for Tables that are
                #   in SDW that should be copied over to SDE
                # If FEATURE_DATASET doesn't equal 'None' add the FEATURE_DATASET
                #   to the input path
                if r.FEATURE_DATASET != 'None':
                    inputDS = inputSDE + "\\SDW.PDS.{}".format(r.FEATURE_DATASET)
                    inputDS = inputSDE + '\\{}'.format(r.FEATURE_DATASET)  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
                # If FEATURE_DATASET == 'None' then the SDE path should  be added
                #   to the LAYER_NAME w/o a Dataset between the SDE and the Table
                #   (See inLayer below for the concatenation)
                else:
                    inputDS = inputSDE
                # END MG 07/12/17
                #---------------------------------------------------------------
                #---------------------------------------------------------------

                arcpy.env.workspace = inputDS
                inLayer  = inputDS + "\\SDW.PDS.{}".format(r.LAYER_NAME)
                inLayer  = inputDS + '\\{}'.format(r.LAYER_NAME)  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing

                # Delete old version if it exists
                if arcpy.Exists(outLayer):
                    print 'Deleting {} from Warehouse'.format(r.LAYER_NAME)
                    arcpy.Delete_management(outLayer)

                # Copy dataset from Workspace to Warehouse for distribution
                #---------------------------------------------------------------
                #---------------------------------------------------------------
                # START MG 07/12/17:  Added below to account for Tables that are
                #   in SDW that should be copied over to SDE

                output_dataset = os.path.join(outputSDE, r.LAYER_NAME)
                print 'Copying "{}"\n  From: {}\n  To:   {}'.format(r.LAYER_NAME, inLayer, output_dataset)

                # Try to copy FC to FC, if that fails, try to copy Table to Table
                try:
                    arcpy.FeatureClassToFeatureClass_conversion(inLayer, output_dataset)
                except:
                    arcpy.CopyRows_management(inLayer, output_dataset)

                # END MG 07/12/17
                #---------------------------------------------------------------
                #---------------------------------------------------------------

                # Change privileges
                print "Granting privileges to {}".format(r.LAYER_NAME)
                try:
                    arcpy.ChangePrivileges_management(outLayer,"SDE_VIEWER","GRANT","AS_IS")
                except:
                    print '*** ERROR with Granting Privileges ***'

                print ""
            except:
                print "*********************** ERROR WITH " + str(r.LAYER_NAME) + " *****************"
                print arcpy.GetMessages()
            r = c.next()
        del c, r

        # Update the dates in WAREHOUSE's LUEG_UPDATES table
        #   with the dates in WORKSPACE's LUEG_UPDATES table
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

            # Add to WAREHOUSE's LUEG_UPDATES if doesn't exist
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
except Exception as e:  # MG 07/12/17: Added the 'Exception as e' to print exception to screen
    print "ERROR in D:\\sde_maintenance\\scripts\\updateWarehouseFromWorkspace.py at " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
    print arcpy.GetMessages()
    print str(e)  # MG 07/12/17: Added the print statement
    logFile.close()
    sys.stdout = oldOutput

# MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
##    # email
##    import smtplib, ConfigParser
##    from email.mime.text import MIMEText
##
##    config = ConfigParser.ConfigParser()
##    config.read(r"D:\sde_maintenance\scripts\configFiles\accounts.txt")
##    email_usr = config.get("email","usr")
##    email_pwd = config.get("email","pwd")
##
##    fp = open(logFileName,"rb")
##    msg = MIMEText(fp.read())
##    fp.close()
##
##    fromaddr = "dplugis@gmail.com"
##    toaddr = ["gary.ross@sdcounty.ca.gov",]
##
##    msg['Subject'] = "ERROR when updating WAREHOUSE with WORKSPACE"
##    msg['From'] = "Python Script"
##    msg['To'] = "SDE Administrator"
##
##    s = smtplib.SMTP('smtp.gmail.com', 587)
##    s.ehlo()
##    s.starttls()
##    s.ehlo()
##    s.login(email_usr,email_pwd)
##    s.sendmail(fromaddr,toaddr,msg.as_string())
##    s.quit()
