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
    table in Workspace.
"""
#
# Author:      Gary Ross
# Editors:     Gary Ross, Mike Grue
#-------------------------------------------------------------------------------

# TODO: Delete the commented out variables added with 'MG 07/07/17' after script has been running successfully in prod for a while.

import sys, string, os, time, math, arcpy
from datetime import date

##arcpy.env.overwriteOutput = True  #  MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing

timestart = str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
dateToday = str(time.strftime("%m/%d/%Y", time.localtime()))

try:
    #---------------------------------------------------------------------------
    # START MG 07/07/17: Add to allow 'Tables' (not just Feature Classes) to update Workspace
    # Get a list of Tables (if any) to trigger the rest of the script even
    #   if there are tables, but no feature classes.

    table_update_path = r'D:\sde\sde_load.gdb'
##    table_update_path = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_sde_load.gdb'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
    arcpy.env.workspace = table_update_path
    table_list = arcpy.ListTables()

    # END MG 07/07/17
    #---------------------------------------------------------------------------

    fgdb = r"D:\sde\sde_load.gdb\workspace"
##    fgdb = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_sde_load.gdb\workspace'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
    arcpy.env.workspace = fgdb
    fcList = arcpy.ListFeatureClasses()

    eMailLogic = 0 # Added line 12/10/2014 - Email logic

    if ((fcList != []) or (table_list != [])) : # There are datasets to move. MG 07/07/17: added 'table_list' check.  TODO: show Gary this section and any 'MG 07/07/17' changes

        # Create log file
        oldOutput = sys.stdout
        logFileName = str("D:\\sde_maintenance\\log\\updateWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")
##        logFileName = str(r"U:\grue\Projects\VDrive_to_SDEP_flow\log\updateWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        logFile = open(logFileName,"w")
        sys.stdout = logFile  ## MG 07/07/17: DEV settings.  TODO: Uncomment out after testing, then delete this comment
        print "START TIME " + str(timestart)

        print ""

        dataList = arcpy.ListFeatureClasses()

        pathName  = "Database Connections\\Atlantic Workspace (pds user).sde"
##        pathName  = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDW.gdb'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        tableName = pathName + "\\SDW.PDS.LUEG_UPDATES"
##        tableName = pathName + "\\LUEG_UPDATES"  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        adminSDE  = "Database Connections\\Atlantic Workspace (sa user).sde"

##        MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
        # Disconnect users from the database (added 3/12/13)
        try:
            usrList = arcpy.ListUsers(adminSDE)
            for user in usrList:
                if user.Name[1:5] == "BLUE":
                    arcpy.DisconnectUser(adminSDE,user.ID)
        except:
            print "ERROR disconnecting users"
            print arcpy.GetMessages()

        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        # START MG 07/07/17:  Added to import any tables in 'sde_load.gdb'

        if (table_list != []):
            print 'Processing {} tables'.format(str(len(table_list)))
            print '--------------------------------------------------------'

            lueg_updates_table = tableName  # Change variable name for readability in MG 07/07/17 section

            for table in table_list:
                print 'Processing table: {}'.format(table)

                load_table = os.path.join(table_update_path, table)
                workspace_table = os.path.join(pathName, table)

                # If table exists in Workspace, delete it
                if arcpy.Exists(workspace_table):
                    print '  Deleting "{}" in "{}"'.format(table, pathName)
                    arcpy.Delete_management(workspace_table)
                    print '    ...Deleted'


                # Copy table from 'sde_load.gdb' to Workspace
                print '  Copying "{}" to "{}"'.format(table, workspace_table)
                arcpy.Copy_management(load_table, workspace_table)
                print '    ...Copied'


                # Date stamp the table in the Workspace's LUEG_UPDATES table
                where_clause = '"LAYER_NAME" = \'{}\''.format(table)
                with arcpy.da.UpdateCursor(lueg_updates_table, ['LAYER_NAME', 'UPDATE_DATE'], where_clause) as cursor:
                    num_rows = 0
                    for row in cursor:
                        row[1] = dateToday
                        print '  Updating LUEG_UPDATES where ({}) so UPDATE_DATE equals "{}"'.format(where_clause, row[1])
                        cursor.updateRow(row)
                        print '    ...Updated'
                        num_rows = num_rows + 1

                    # Warn user if no row in LUEG_UPDATES satisfied the where_clause
                    if num_rows != 1:
                        print '*** WARNING! UPDATE_DATE "{}" wasn\'t updated in LUEG_UPDATES, please confirm table in LUEG_UPDATES ***'.format(table)


                # Register table as versioned if needed
                try:
                    desc = arcpy.Describe(workspace_table)
                    if not desc.isVersioned:
                        print '  Registering Table "{}" as versioned'.format(workspace_table)
                        arcpy.RegisterAsVersioned_management(workspace_table,"NO_EDITS_TO_BASE")  ## TODO: Uncomment out before finish testing and test uncommented.  Delete this comment after testing.
                        print '    ...Registered'

                except:
                    print '*** ERROR! In versioning table "{}"'.format(table)
                    eMailLogic = 1


                # Grant editing privileges
                try:
                    print '  Changing privileges of table "{}"'.format(workspace_table)
                    arcpy.ChangePrivileges_management(workspace_table,"SDE_EDITOR","GRANT","GRANT")  ## TODO: Uncomment out before finish testing and test uncommented.  Delete this comment after testing.
                    print '    ...Privileges changed'

                except:
                    print '*** ERROR! In granting permissions for table "{}"'.format(table)
                    eMailLogic = 1


                # Delete Table from 'sde_load.gdb'
                print "  Deleting table from loading gdb"
                arcpy.Delete_management(load_table)  ## TODO: Uncomment out before finish testing and test uncommented.  Delete this comment after testing.
                print '    ...Deleted'
                print '--------------------------------------------------------'

            print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

        # END MG 07/07/17
        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------

        with arcpy.da.SearchCursor(tableName,["LAYER_NAME","FEATURE_DATASET"]) as rowcursor:
            fcfdList = list(rowcursor)
        del rowcursor

        fdsToRegister = list([])

        if dataList != []:
            print 'Processing {} Feature Classes'.format(str(len(dataList)))  # MG 07/07/17: Added print statement
            for fc in dataList:

                fdsName = "none"
                for fcfdPair in fcfdList:
                    if fcfdPair[0] == fc:
                        fdsName = pathName + "\\SDW.PDS." + str(fcfdPair[1])
##                        fdsName = pathName + "\\" + str(fcfdPair[1])  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete this comment after testing

                if fdsName == "none":
                    print "\n***WARNING***: " + fc + " not found in FCs table --> !!!DATA NOT COPIED!!!"
                    eMailLogic = 1
                else:
                    if not arcpy.Exists(fdsName):
                        print "\n***ERROR***: feature dataset " + str(fcfdPair[1]) + " doesn't exist --> !!!DATA NOT COPIED!!!"
                        eMailLogic = 1
                    else:
                        fdsToRegister.extend([str(fcfdPair[1])])
                        print "fdsName",fdsName
                        print "fc",fc
                        layerName = fdsName + "\\SDW.PDS." + str(fc)
                        topoName  = fdsName + "\\SDW.PDS.topology_" + str(fc)

                        if arcpy.Exists(topoName):
                            arcpy.Delete_management(topoName)
                        if arcpy.Exists(layerName):
                            arcpy.Delete_management(layerName)
                        if arcpy.Exists(topoName):
                            arcpy.Delete_management(topoName)

                        # Copy dataset from file gdb to LUEG/PDS SDE
                        print "Copying " + str(fc) + " to WORKSPACE SDE..."
                        arcpy.Copy_management(fc,fdsName + "\\" + fc)
                        print fc + " copied to " + fdsName + "\\" + fc

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
                        arcpy.Delete_management(str(fc))  ## MG 07/07/17: DEV settings.  TODO: Uncomment out before finish testing and test uncommented.  Delete this comment after testing.

                        print "  Timestamping dataset..."
                        theCount = 0
                        c1 = arcpy.UpdateCursor(tableName ,"\"LAYER_NAME\" = '" + str(fc) + "'")
                        r1 = c1.next()
                        while r1:
                            theCount = theCount + 1
                            r1.UPDATE_DATE = dateToday
                            c1.updateRow(r1)
                            r1 = c1.next()
                        del c1, r1

                        del theCount
                        print ""

##         MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
        if dataList != []:
            for fd in fdsToRegister:
                print "pathName",pathName
                print "fd",fd
                fdsName = pathName + "\\SDW.PDS." + str(fd)

                # Register feature dataset
                try:
                    desc = arcpy.Describe(fdsName)
                    if not desc.isVersioned:
                        arcpy.RegisterAsVersioned_management(fdsName,"NO_EDITS_TO_BASE")
                        print "Feature dataset " + str(fd) + " registered as versioned..."
                except:
                    print "error in versioning"
                    eMailLogic = 1

                # Change privileges
                arcpy.ChangePrivileges_management(fdsName,"SDE_EDITOR","GRANT","GRANT")
                print "Feature dataset " + str(fd) + " privileges changed..."

        print ""
        print "Data load to WORKSPACE SDE complete..."
        print "END TIME " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
        logFile.close()
        sys.stdout = oldOutput

### MG 07/07/17: DEV settings.  TODO: remove below 'except' statement after testing
##except Exception as e:
##    print '***  ERROR!!!  ***'
##    print str(e)

##         MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
    if eMailLogic == 0:
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

        msg['Subject'] = "WORKSPACE has new datasets loaded"
        msg['From'] = "Python Script"
        msg['To'] = "SDE Administrator"

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(email_usr,email_pwd)
        s.sendmail(fromaddr,toaddr,msg.as_string())
        s.quit()
    else:
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

        msg['Subject'] = "ERROR when loading WORKSPACE"
        msg['From'] = "Python Script"
        msg['To'] = "SDE Administrator"

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(email_usr,email_pwd)
        s.sendmail(fromaddr,toaddr,msg.as_string())
        s.quit()

except:
    print "ERROR OCCURRED"
    print "D:\\sde_maintenance\\scripts\\updateWorkspace.py"
    print arcpy.GetMessages()
    logFile.close()
    sys.stdout = oldOutput

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

    msg['Subject'] = "ERROR when loading WORKSPACE"
    msg['From'] = "Python Script"
    msg['To'] = "SDE Administrator"

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(email_usr,email_pwd)
    s.sendmail(fromaddr,toaddr,msg.as_string())
    s.quit()