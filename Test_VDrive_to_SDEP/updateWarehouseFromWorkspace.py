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
# TODO: remove the commented out settings from the DEV environment after script has been working in PROD for a while

import sys, string, os, time, math, arcpy
from datetime import datetime, date

##arcpy.env.overwriteOutput = True  #  MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing

try:
    #---------------------------------------------------------------------------
    #                             Set Variables
    # Set paths
    outputSDE  = r"D:\sde_maintenance\scripts\Database Connections\Atlantic Warehouse (sangis user).sde"
##    outputSDE  = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDE.gdb'  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
    outTable   = outputSDE + "\\SDE.SANGIS.LUEG_UPDATES"
##    outTable   = outputSDE + '\\LUEG_UPDATES'  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
    inputSDE   = r"D:\sde_maintenance\scripts\Database Connections\Atlantic Workspace (pds user).sde"
##    inputSDE   = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDW.gdb'  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
    inputTable = inputSDE + "\\SDW.PDS.LUEG_UPDATES"
##    inputTable = inputSDE + '\\LUEG_UPDATES'  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
    adminSDE   = "Database Connections\\Atlantic Warehouse (sa user).sde"

    logFileName = "D:\\sde_maintenance\\log\\updateWarehouseFromWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt"
##    logFileName = r"U:\grue\Projects\VDrive_to_SDEP_flow\log\updateWarehouseFromWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt"  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing

    lueg_admin_email = ["gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
    lueg_admin_email = ['michael.grue@sdcounty.ca.gov']  # TODO: Delete this line when done testing

    # Get the Query used to find recently updated datasets
    updateWindow = 7 # Number of days in past to look for updates
    startDate = date.fromordinal(date.toordinal(date.today()) - updateWindow)
    endDate = date.today()
    theQ = "\"UPDATE_DATE\" >= '" + str(startDate) + "' AND \"UPDATE_DATE\" <= '" + str(endDate) + "' AND \"PUBLIC_ACCESS\" = 'Y'"
##    theQ = "\"UPDATE_DATE\" >= date '" + str(startDate) + "' AND \"UPDATE_DATE\" <= date '" + str(endDate) + "' AND \"PUBLIC_ACCESS\" = 'Y'"  # MG 07/12/17: Set variable to DEV settings.  TODO: Why did I need to do this?  How is it working on SOUTHERN?
    #---------------------------------------------------------------------------

    # Get start time
    timestart = str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))

    # Check to see if there have been any updates
    s1 = arcpy.SearchCursor(str(inputTable), str(theQ))
    s1row = s1.next()
    layerCount = 0
    while s1row:
        layerCount = layerCount + 1
        s1row = s1.next()
    del s1, s1row

    # Check to make sure there are datasets that need to be copied
    if (layerCount > 0):

        # create log file
        oldOutput = sys.stdout
        logFile = open(logFileName,"w")
        sys.stdout = logFile  # MG 07/12/17: Set variable to DEV settings.  TODO: uncomment out after done testing

        # Starting print statements
        print "START TIME: " + str(timestart)
        print 'Copying "{}" datasets updated between {} and {}'.format(str(layerCount), str(startDate), str(endDate))
        print '----------------------------------------------------------------'

        # Disconnect users from the database (added 3/12/13)
        # TODO: uncomment out when done testing
##        try:
##            usrList = arcpy.ListUsers(adminSDE)
##            for user in usrList:
##                if user.Name[1:5] == "BLUE":
##                    arcpy.DisconnectUser(adminSDE,user.ID)
##        except Exception as e:
##            print "*** ERROR with Disconnecting users from the database ***"
##            print str(e)
##            print arcpy.GetMessages()


        # Go through each dataset recently updated
        c = arcpy.SearchCursor(inputTable,theQ)
        r = c.next()
        processed = 0  # Counter for successfully processed datasets
        while r:
            try:
                print 'Processing "{}"\n'.format(r.LAYER_NAME)

                # Set path for the output
                outLayer = outputSDE + "\\SDE.SANGIS.{}".format(r.LAYER_NAME)
##                outLayer = outputSDE + "\\{}".format(r.LAYER_NAME)  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
                #---------------------------------------------------------------
                #---------------------------------------------------------------
                # Below section is for Tables that are in SDW that should
                #   be copied over to SDE

                # If FEATURE_DATASET == 'None' then the SDE path should  be added
                #   to the LAYER_NAME w/o a Dataset between the SDE and the Table
                #   (See inLayer below for the concatenation)
                if r.FEATURE_DATASET == 'None':
                    inputDS = inputSDE

                # If FEATURE_DATASET doesn't equal 'None' add the FEATURE_DATASET
                #   to the input path
                else:
                    inputDS = inputSDE + "\\SDW.PDS.{}".format(r.FEATURE_DATASET)
##                    inputDS = inputSDE + '\\{}'.format(r.FEATURE_DATASET)  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing

                arcpy.env.workspace = inputDS  # TODO: can this be removed?  Comment out and test.

                # Set the path for the input dataset to be copied
                inLayer  = inputDS + "\\SDW.PDS.{}".format(r.LAYER_NAME)
##                inLayer  = inputDS + '\\{}'.format(r.LAYER_NAME)  # MG 07/12/17: Set variable to DEV settings.  TODO: Delete after testing
                # END section
                #---------------------------------------------------------------
                #---------------------------------------------------------------


                # Delete old version if it exists
                if arcpy.Exists(outLayer):
                    print 'Deleting "{}" from "{}"'.format(r.LAYER_NAME, outLayer)
                    arcpy.Delete_management(outLayer)


                # Get the dataset type to decide how to copy the dataset
                #   (i.e. as a Feature Class or as a Table)
                desc = arcpy.Describe(inLayer)
                dataset_type = desc.datasetType
                output_dataset = os.path.join(outputSDE, r.LAYER_NAME)

                # Copy the dataset if it is a FeatureClass
                if dataset_type == 'FeatureClass':
                    print 'Copying "{}"\n  From: {}\n  To:   {}\\{}\n  As:   A {}'.format(r.LAYER_NAME, inLayer, outputSDE, r.LAYER_NAME, dataset_type)
                    arcpy.FeatureClassToFeatureClass_conversion(inLayer, outputSDE, r.LAYER_NAME)

                # Copy the dataset if it is a Table
                if dataset_type == 'Table':
                    print 'Copying "{}"\n  From: {}\n  To:   {}\n  As:   A {}'.format(r.LAYER_NAME, inLayer, output_dataset, dataset_type)
                    arcpy.CopyRows_management(inLayer, output_dataset)

                if (dataset_type != 'FeatureClass') or (dataset_type != 'Table'):
                    '*** WARNING! Datasets with types of "{}" cannot currently be copied'.format(dataset_type)


                # Change privileges
                print "Granting privileges to '{}'".format(output_dataset)
                try:
                    arcpy.ChangePrivileges_management(outLayer,"SDE_VIEWER","GRANT","AS_IS")
                    processed += 1  # Can only reach this line if dataset processed successfully
                except Exception as e:
                    print '*** ERROR with Granting Privileges ***'
                    print str(e)


                print '--------------------------------------------------------'

            except Exception as e:
                print "*********************** ERROR WITH " + str(r.LAYER_NAME) + " *****************"
                print str(e)
                print arcpy.GetMessages()
                print ''
            r = c.next()
        del c, r

        print 'There were {} datasets to be copied from Workspace to Warehouse'.format(str(layerCount))
        print '  {} were processed 100% successfully'.format(str(processed))
        if str(layerCount) != str(processed):
            print '\n*** WARNING there were datasets that were not successfully processed ***\n'

        #-----------------------------------------------------------------------
        # Update the dates in WAREHOUSE's LUEG_UPDATES table
        #   with the dates in WORKSPACE's LUEG_UPDATES table
        print '--------------------------------------------------------'
        print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        print '--------------------------------------------------------'
        print 'Update the dates in WAREHOUSE\'s LUEG_UPDATES table'
        print '  with the dates in WORKSPACE\'s LUEG_UPDATES table\n'

        inputTable_cursor = arcpy.SearchCursor(inputTable)
        inputTable_row = inputTable_cursor.next()
        while inputTable_row:
            theName = inputTable_row.LAYER_NAME
            theDate = inputTable_row.UPDATE_DATE
            inputTable_row = inputTable_cursor.next()

            print 'Updating "{}" with date "{}"'.format(theName, str(theDate)[:10])

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

        del inputTable_cursor, inputTable_row

    print ""
    print "END TIME: " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))

    logFile.close()
    sys.stdout = oldOutput
except Exception as e:
    print "ERROR in D:\\sde_maintenance\\scripts\\updateWarehouseFromWorkspace.py at " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
    print str(e)
    print arcpy.GetMessages()
    logFile.close()
    sys.stdout = oldOutput

# MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
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
    toaddr = lueg_admin_email

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
