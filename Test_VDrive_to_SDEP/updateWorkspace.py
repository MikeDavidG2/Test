#-------------------------------------------------------------------------------
# Name:        updateWorkspace.py
# Purpose:
"""
Loads data from local file geodatabase into Workspace
NOTE: Run script directly on server Southern

UPDATES:
  December 2014:
    To account for new feature datasets in SDE
  February 2017:
    Upgraded ArcGIS to 10.4.1 and new server
  July 2017:
    Allow tables in the loading FGDB (sde_load.gdb) to load into
    Workspace.
    NOTES: Any table in loading FGDB will be loaded into Workspace, however
    any NEW table added to Workspace should be manually added to LUEG_UPDATES
    table in Workspace.  All Tables should have field FEATURE_DATASET = 'None'
    and COUNTY_FDS = 'None'
"""
#
# Author:      Gary Ross
# Editors:     Gary Ross, Mike Grue
#-------------------------------------------------------------------------------

# TODO: Delete the commented out variables added with 'MG 07/07/17' after script has been running successfully in prod for a while.

import sys, string, os, time, math, arcpy
from datetime import date

arcpy.env.overwriteOutput = True  #  MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing

timestart = str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
dateToday = str(time.strftime("%m/%d/%Y", time.localtime()))

try:
    #---------------------------------------------------------------------------
    # START MG 07/07/17: Add to allow 'Tables' (not just Feature Classes) to update Workspace
    # Get a list of Tables (if any) to trigger the rest of the script even
    #   if there are tables, but no feature classes.

    table_update_path = r'D:\sde\sde_load.gdb'
    table_update_path = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_sde_load.gdb'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
    arcpy.env.workspace = table_update_path
    table_list = arcpy.ListTables()

    # END MG 07/07/17
    #---------------------------------------------------------------------------

    fgdb = r"D:\sde\sde_load.gdb\workspace"
    fgdb = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_sde_load.gdb\workspace'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
    arcpy.env.workspace = fgdb
    fcList = arcpy.ListFeatureClasses()

    eMailLogic = 0 # Added line 12/10/2014 - Email logic

    if ((fcList != []) or (table_list != [])) : # There are datasets to move. MG 07/07/17: added 'table_list' check.

        # Create log file
        oldOutput = sys.stdout
        logFileName = str("D:\\sde_maintenance\\log\\updateWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")
        logFileName = str(r"U:\grue\Projects\VDrive_to_SDEP_flow\log\updateWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        logFile = open(logFileName,"w")
        sys.stdout = logFile  # MG 07/07/17: DEV settings.  TODO: Uncomment out after testing, then delete this comment
        print "START TIME " + str(timestart)

        print ""

        dataList = arcpy.ListFeatureClasses()

        pathName  = "Database Connections\\Atlantic Workspace (pds user).sde"
        pathName  = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDW.gdb'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        tableName = pathName + "\\SDW.PDS.LUEG_UPDATES"
        tableName = pathName + "\\LUEG_UPDATES"  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        adminSDE  = "Database Connections\\Atlantic Workspace (sa user).sde"

        # MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
##        # Disconnect users from the database (added 3/12/13)
##        try:
##            print 'Disconnecting Users\n'
##            usrList = arcpy.ListUsers(adminSDE)
##            for user in usrList:
##                if user.Name[1:5] == "BLUE":
##                    arcpy.DisconnectUser(adminSDE,user.ID)
##        except:
##            print "ERROR disconnecting users"
##            print arcpy.GetMessages()

        print '------------------------------------------------'
        print '++++++++++++++++++++++++++++++++++++++++++++++++'
        print '------------------------------------------------'

        # Process Tables below
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # START MG 07/07/17:
        # Added to import any tables in 'sde_load.gdb'

        if (table_list != []):
            print 'Copying {} tables\n'.format(str(len(table_list)))

            lueg_updates_table = tableName  # Change variable name for readability in MG 07/07/17 section

            for table in table_list:
                print 'Copying: "{}"'.format(table)

                load_table = os.path.join(table_update_path, table)
                workspace_table = os.path.join(pathName, table)

                # If table exists in Workspace, delete it
                if arcpy.Exists(workspace_table):
                    print '  Deleting "{}" in "{}"'.format(table, pathName)
                    arcpy.Delete_management(workspace_table)


                # Copy table from 'sde_load.gdb' to Workspace
                print '  Copying "{}" to "{}"'.format(table, workspace_table)
                arcpy.Copy_management(load_table, workspace_table)


                # Test to see if the copied Table already exists in LUEG_UPDATES
                where_clause = '"LAYER_NAME" = \'{}\''.format(table)
                with arcpy.da.SearchCursor(lueg_updates_table, ['LAYER_NAME'], where_clause) as searchCursor:
                    num_rows = 0
                    for row in searchCursor:
                        num_rows = num_rows + 1

                if num_rows == 0:  # Then the table does NOT exist, add it to LUEG_UPDATES w/ values
                    print '  "{}" is not in LUEG_UPDATES table, creating record in LUEG_UPDATES'.format(table)
                    fields = ['LAYER_NAME', 'UPDATE_DATE', 'PUBLIC_ACCESS', 'TOPOLOGY_CODE', 'FEATURE_DATASET', 'COUNTY_FDS', 'EDIT_LOCATION']
                    with arcpy.da.InsertCursor(lueg_updates_table, fields) as insertCursor:
                        LAYER_NAME      = table
                        UPDATE_DATE     = dateToday
                        PUBLIC_ACCESS   = 'Y'
                        TOPOLOGY_CODE   = 'N'
                        FEATURE_DATASET = 'None'
                        COUNTY_FDS      = 'None'
                        EDIT_LOCATION   = 'BLUE'
                        insertCursor.insertRow([LAYER_NAME, UPDATE_DATE, PUBLIC_ACCESS, TOPOLOGY_CODE, FEATURE_DATASET, COUNTY_FDS, EDIT_LOCATION])

                elif num_rows == 1:  # Then the table EXISTS, only update the date
                    with arcpy.da.UpdateCursor(lueg_updates_table, ['LAYER_NAME', 'UPDATE_DATE'], where_clause) as updateCursor:
                        for row in updateCursor:
                            row[1] = dateToday
                            print '  Updating LUEG_UPDATES where ({}) so UPDATE_DATE equals "{}"'.format(where_clause, row[1])
                            updateCursor.updateRow(row)

                elif num_rows > 1:
                    print '*** WARNING! there is more than 1 record for "{}" in LUEG_UPDATES'.format(table)
                    #TODO: Test this out by having more than 1 record in the LUEG_UPDATES table

                # Register table as versioned if needed
                try:
                    desc = arcpy.Describe(workspace_table)
                    if not desc.isVersioned:
                        print '  Registering Table "{}" as versioned'.format(workspace_table)
##                        arcpy.RegisterAsVersioned_management(workspace_table,"NO_EDITS_TO_BASE")

                except Exception as e:
                    print '*** ERROR! In versioning table "{}"'.format(table)
                    print str(e)
                    eMailLogic = 1


                # Grant editing privileges
                try:
                    print '  Changing privileges of table "{}"'.format(workspace_table)
##                    arcpy.ChangePrivileges_management(workspace_table,"SDE_EDITOR","GRANT","GRANT")

                except Exception as e:
                    print '*** ERROR! In granting permissions for table "{}"'.format(table)
                    print str(e)
                    eMailLogic = 1


                # Delete Table from 'sde_load.gdb'
##                print "  Deleting table from loading gdb"
##                arcpy.Delete_management(load_table)  ## TODO: Uncomment out before finish testing and test uncommented.  Delete this comment after testing.
                print '------------------------------------------------'

            print '++++++++++++++++++++++++++++++++++++++++++++++++'

        # END MG 07/07/17
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        #                      Process Feature Classes below

        # Get a list of LAYER_NAME and FEATURE_DATASET from the LUEG_UPDATES table
        where_clause = '"FEATURE_DATASET" <> \'None\''  # Only search non-table records
        with arcpy.da.SearchCursor(tableName,["LAYER_NAME","FEATURE_DATASET"], where_clause) as rowcursor:
            fcfdList = list(rowcursor)
        del rowcursor

        if dataList != []:
            print '------------------------------------------------'
            print 'Copying {} Feature Classes\n'.format(str(len(dataList)))
            fdsToRegister = list([])

            for fc in dataList:

                fdsName = "###"
                for fcfdPair in fcfdList:
                    if fcfdPair[0] == fc:
                        fdsName = pathName + "\\SDW.PDS." + str(fcfdPair[1])
                        fdsName = pathName + "\\" + str(fcfdPair[1])  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete this comment after testing

                if fdsName == "###":
                    print "\n***WARNING***: " + fc + " not found in FCs table --> !!!DATA NOT COPIED!!!"
                    eMailLogic = 1
                else:
                    if not arcpy.Exists(fdsName):
                        print "\n***ERROR***: feature dataset " + str(fcfdPair[1]) + " doesn't exist --> !!!DATA NOT COPIED!!!"
                        eMailLogic = 1

                    else:
                        print 'Copying "{}"'.format(fc)
                        layerName = fdsName + "\\SDW.PDS." + str(fc)
                        layerName = fdsName + "\\" + str(fc)  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete this var after testing
                        topoName  = fdsName + "\\SDW.PDS.topology_" + str(fc)


                        # Delete existing dataset in SDW
                        if arcpy.Exists(layerName):
                            print '  Deleting existing "{}"'.format(layerName)
                            arcpy.Delete_management(layerName)

                        if arcpy.Exists(topoName):
                            print '  Deleting existing "{}"'.format(topoName)
                            arcpy.Delete_management(topoName)


                        # Copy dataset from file gdb to LUEG/PDS SDE
                        print '  Copying "{}" to "{}"'.format(fc, fdsName)
                        arcpy.FeatureClassToGeodatabase_conversion(fc,fdsName)


                        # Check for topology requirements
                        c = arcpy.SearchCursor(tableName, "\"LAYER_NAME\" = '" + str(fc) + "'")
                        topoCode = "N"
                        r = c.next()
                        while r:
                            topoCode = r.getValue("TOPOLOGY_CODE")
                            r = c.next()
                        del r, c

                        # Create topolgy
                        if topoCode != "N":
                            print "  Creating topology..."
                            arcpy.CreateTopology_management(fdsName,"topology_" + str(fc),"1")
                            print "  Adding " + layerName + "  to topology..."
                            arcpy.AddFeatureClassToTopology_management(topoName,layerName,"1","1")
                            print "  Adding rules to topology..."
                            if topoCode == "P1":
                                arcpy.AddRuleToTopology_management(topoName,"Must Not Have Gaps (Area)",layerName)
                                arcpy.AddRuleToTopology_management(topoName,"Must Not Overlap (Area)",layerName)
                            if topoCode == "P2":
                                    arcpy.AddRuleToTopology_management(topoName,"Must Not Overlap (Area)",layerName)
                            if topoCode == "P3":
                                arcpy.AddRuleToTopology_management(topoName,"Must Not Overlap (Line)",layerName)
                                arcpy.AddRuleToTopology_management(topoName,"Must Not Have Dangles (Line)",layerName)
                                arcpy.AddRuleToTopology_management(topoName,"Must Be Single Part (Line)",layerName)

                            print "  Validating topology..."
                            arcpy.ValidateTopology_management(topoName, "FULL_EXTENT")

                        print "  Deleting feature class from loading gdb..."
##                        arcpy.Delete_management(str(fc))  # MG 07/07/17: DEV settings.  TODO: Uncomment out before finish testing and test uncommented.  Delete this comment after testing.

                        print "  Timestamping dataset in LUEG_UPDATES"
                        c1 = arcpy.UpdateCursor(tableName ,"\"LAYER_NAME\" = '" + str(fc) + "'")
                        r1 = c1.next()
                        while r1:
                            r1.UPDATE_DATE = dateToday
                            c1.updateRow(r1)
                            r1 = c1.next()
                        del c1, r1

                        # Get the name of the Feature Dataset (w/o the path)
                        # And add it to the a list so we can register and change
                        # Privileges at the Feature Dataset level
                        fdsToRegister.extend([os.path.basename(fdsName)])

                        print ""
                        print '------------------------------------------------'

        # Register and change privileges for any Feature Classes imported'
        if dataList != []:
            unique_fdsToRegister = set(fdsToRegister)
            print '++++++++++++++++++++++++++++++++++++++++++++++++'
            print '------------------------------------------------'
            print 'Registering Versioning and Change Priviliges for {} Feature Datasets:'.format(str(len(unique_fdsToRegister)))
            print ', '.join(unique_fdsToRegister)
            for fd in unique_fdsToRegister:
                fdsName = pathName + "\\SDW.PDS." + str(fd)
                fdsName = pathName + "\\" + str(fd)  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete this var after testing
                print '\nProcessing FD: "{}"'.format(fdsName)

                # Register feature dataset
                try:
                    desc = arcpy.Describe(fdsName)
                    if not desc.isVersioned:
                        print '  Registering as versioned'
##                        arcpy.RegisterAsVersioned_management(fdsName,"NO_EDITS_TO_BASE")
                except Exception as e:
                    print "*** Error in versioning ***"
                    print str(e)
                    eMailLogic = 1

                # Change privileges
                try:
                    print '  Changing privileges'
##                    arcpy.ChangePrivileges_management(fdsName,"SDE_EDITOR","GRANT","GRANT")
                except Exception as e:
                    print '*** Error in changing privileges ***'
                    print str(e)
                    eMailLogic = 1

                print '------------------------------------------------'

        print ""
        print "Data load to WORKSPACE SDE complete..."
        print "END TIME " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
        logFile.close()
        sys.stdout = oldOutput

# MG 07/07/17: DEV settings.  TODO: remove below 'except' statement after testing
except Exception as e:
    print '***  ERROR!!!  ***'
    print str(e)

#         MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
##    if eMailLogic == 0:
##        import smtplib, ConfigParser
##        from email.mime.text import MIMEText
##
##        config = ConfigParser.ConfigParser()
##        config.read(r"D:\sde_maintenance\scripts\configFiles\accounts.txt")
##        email_usr = config.get("email","usr")
##        email_pwd = config.get("email","pwd")
##
##        fp = open(logFileName,"rb")
##        msg = MIMEText(fp.read())
##        fp.close()
##
##        fromaddr = "dplugis@gmail.com"
##        toaddr = ["gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
##
##        msg['Subject'] = "WORKSPACE has new datasets loaded"
##        msg['From'] = "Python Script"
##        msg['To'] = "SDE Administrator"
##
##        s = smtplib.SMTP('smtp.gmail.com', 587)
##        s.ehlo()
##        s.starttls()
##        s.ehlo()
##        s.login(email_usr,email_pwd)
##        s.sendmail(fromaddr,toaddr,msg.as_string())
##        s.quit()
##    else:
##        import smtplib, ConfigParser
##        from email.mime.text import MIMEText
##
##        config = ConfigParser.ConfigParser()
##        config.read(r"D:\sde_maintenance\scripts\configFiles\accounts.txt")
##        email_usr = config.get("email","usr")
##        email_pwd = config.get("email","pwd")
##
##        fp = open(logFileName,"rb")
##        msg = MIMEText(fp.read())
##        fp.close()
##
##        fromaddr = "dplugis@gmail.com"
##        toaddr = ["gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
##
##        msg['Subject'] = "ERROR when loading WORKSPACE"
##        msg['From'] = "Python Script"
##        msg['To'] = "SDE Administrator"
##
##        s = smtplib.SMTP('smtp.gmail.com', 587)
##        s.ehlo()
##        s.starttls()
##        s.ehlo()
##        s.login(email_usr,email_pwd)
##        s.sendmail(fromaddr,toaddr,msg.as_string())
##        s.quit()
##
##except:
##    print "ERROR OCCURRED"
##    print "D:\\sde_maintenance\\scripts\\updateWorkspace.py"
##    print arcpy.GetMessages()
##    logFile.close()
##    sys.stdout = oldOutput
##
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
##    toaddr = ["gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
##
##    msg['Subject'] = "ERROR when loading WORKSPACE"
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