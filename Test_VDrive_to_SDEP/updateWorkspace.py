#-------------------------------------------------------------------------------
# Name:        updateWorkspace.py
# Purpose:
"""
Loads data from local file geodatabase ('table_update_path' and 'fc_update_path')
into Workspace ('workspace_path')
NOTE: Run script directly on server Southern

UPDATES:
  December 2014:
    To account for new feature datasets in SDE
  February 2017:
    Upgraded ArcGIS to 10.4.1 and new server
  July 2017:
    Allow Tables in the loading FGDB (sde_load.gdb) to load into Workspace.
    NOTES:
      1. Any table in loading FGDB will be loaded into Workspace, and given
    default attributes.
      2. All Tables should have field FEATURE_DATASET = 'None'
         and COUNTY_FDS = 'None'
"""
#
# Author:      Gary Ross
# Editors:     Gary Ross, Mike Grue
#-------------------------------------------------------------------------------

import sys, string, os, time, math, arcpy
from datetime import date

# Set paths to FGDB used to update
table_update_path  = r'D:\sde\sde_load.gdb'
fc_update_path     = table_update_path + '\\workspace'

# Set paths to SDE Workspace to be updated
workspace_path     = r'D:\sde_maintenance\scripts\Database Connections\Atlantic Workspace (pds user).sde'
lueg_updates_table = workspace_path + "\\SDW.PDS.LUEG_UPDATES"

# Misc Variables
adminSDE           = "Database Connections\\Atlantic Workspace (sa user).sde"
logFileName        = str("D:\\sde_maintenance\\log\\updateWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")
lueg_admin_email   = ["gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
no_errors          = True

# Get time and date
timestart = str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
dateToday = str(time.strftime("%m/%d/%Y", time.localtime()))

try:
    #---------------------------------------------------------------------------
    # START MG 07/07/17: Add to allow 'Tables' (not just Feature Classes) to update Workspace
    # Get a list of Tables (if any) in the loading FGDB
    arcpy.env.workspace = table_update_path
    table_list = arcpy.ListTables()

    # Get a list of Feature Classes (if any) in the loading FGDB
    arcpy.env.workspace = fc_update_path
    fcList = arcpy.ListFeatureClasses()

    if ((fcList != []) or (table_list != [])) : # Test to see if there are datasets to move

        # Create log file
        oldOutput = sys.stdout
        logFile = open(logFileName,"w")
        sys.stdout = logFile

        # Starting print statements
        print "START TIME " + str(timestart)
        print ""
        print 'Table List:'
        print table_list
        print ''
        print 'Feature Class List:'
        print fcList

        # Disconnect users from the database (added 3/12/13)
        try:
            print 'Disconnecting Users'
            usrList = arcpy.ListUsers(adminSDE)
            for user in usrList:
                if user.Name[1:5] == "BLUE":
                    arcpy.DisconnectUser(adminSDE,user.ID)
            print 'Users disconnected\n'

        except:
            print "ERROR disconnecting users"
            print arcpy.GetMessages()

        print '------------------------------------------------'
        print '++++++++++++++++++++++++++++++++++++++++++++++++'
        print '------------------------------------------------'


        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        #                     Process TABLES below
        if (table_list != []):
            print 'Processing {} tables\n'.format(str(len(table_list)))

            for table in table_list:
                try:
                    print 'Processing: "{}"'.format(table)

                    # Set paths
                    load_table = os.path.join(table_update_path, table)
                    workspace_table = os.path.join(workspace_path, table)

                    # If table exists in Workspace, delete it
                    if arcpy.Exists(workspace_table):
                        print '  Deleting "{}" in "{}"'.format(table, workspace_path)
                        arcpy.Delete_management(workspace_table)

                    # Copy table from 'sde_load.gdb' to Workspace
                    print '  Copying  "{}" to "{}"'.format(table, workspace_table)
                    arcpy.Copy_management(load_table, workspace_table)


                    # Test to see if the copied Table already exists in LUEG_UPDATES
                    where_clause = '"LAYER_NAME" = \'{}\''.format(table)
                    with arcpy.da.SearchCursor(lueg_updates_table, ['LAYER_NAME'], where_clause) as searchCursor:
                        num_rows = 0
                        for row in searchCursor:
                            num_rows = num_rows + 1

                    if num_rows == 0:  # Then the table does NOT exist, add it to LUEG_UPDATES w/ values
                        try:
                            print '  Creating record w/attributes in "{}"'.format(lueg_updates_table)
                            iCursor = arcpy.InsertCursor(lueg_updates_table)
                            new_row = iCursor.newRow()
                            new_row.LAYER_NAME      = table
                            new_row.UPDATE_DATE     = dateToday
                            new_row.PUBLIC_ACCESS   = 'Y'
                            new_row.TOPOLOGY_CODE   = 'N'
                            new_row.FEATURE_DATASET = 'None'
                            new_row.COUNTY_FDS      = 'None'
                            new_row.EDIT_LOCATION   = 'BLUE'
                            iCursor.insertRow(new_row)
                            del iCursor, new_row

                        except Exception as e:
                            print '*** ERROR creating record in LUEG_UPDATES table ***'
                            print str(e)
                            no_errors = False

                    elif num_rows == 1:  # Then the table EXISTS, only update the date
                        try:
                            print '  Updating date in for Table in   "{}"'.format(lueg_updates_table)
                            uCursor = arcpy.UpdateCursor(lueg_updates_table, where_clause)
                            row = uCursor.next()
                            while row:
                                row.UPDATE_DATE = dateToday
                                uCursor.updateRow(row)
                                row = uCursor.next()
                            del uCursor, row

                        except Exception as e:
                            print '*** ERROR updating record in LUEG_UPDATES table ***'
                            print str(e)
                            no_errors = False

                    elif num_rows > 1:
                        print '*** WARNING! there is more than 1 record for "{}" in LUEG_UPDATES.\
                        Please delete duplicate AND ensure correct UPDATE_DATE'.format(table)
                        no_errors = False

                    # Register table as versioned if needed
                    try:
                        desc = arcpy.Describe(workspace_table)
                        if not desc.isVersioned:
                            print '  Registering as versioned Table  "{}"'.format(workspace_table)
                            arcpy.RegisterAsVersioned_management(workspace_table,"NO_EDITS_TO_BASE")

                    except Exception as e:
                        print '*** ERROR! In versioning table "{}"'.format(table)
                        print str(e)
                        no_errors = False


                    # Grant editing privileges
                    try:
                        print '  Changing privileges of table    "{}"'.format(workspace_table)
                        arcpy.ChangePrivileges_management(workspace_table,"SDE_EDITOR","GRANT","GRANT")

                    except Exception as e:
                        print '*** ERROR! In granting permissions for table "{}"'.format(table)
                        print str(e)
                        no_errors = False


                    # Delete Table from 'sde_load.gdb' if everything is successful
                    if no_errors == True:
                        print '  Deleting table from             "{}"'.format(load_table)
                        arcpy.Delete_management(load_table)

                    print '------------------------------------------------'

                except Exception as e:
                    print '*** ERROR! With Table "{}" ***'.format(table)
                    print str(e)

            print '++++++++++++++++++++++++++++++++++++++++++++++++'

        #-----------------------------------------------------------------------
        #-----------------------------------------------------------------------
        #                      Process FEATURE CLASSES below
        if fcList != []:
            print '------------------------------------------------'
            print 'Processing {} Feature Classes\n'.format(str(len(fcList)))

            # Get a list of LAYER_NAME and FEATURE_DATASET from the LUEG_UPDATES table
            where_clause = '"FEATURE_DATASET" <> \'None\''  # Only search non-table records
            with arcpy.da.SearchCursor(lueg_updates_table,["LAYER_NAME","FEATURE_DATASET"], where_clause) as rowcursor:
                fcfdList = list(rowcursor)
            del rowcursor

            fdsToRegister = []

            for fc in fcList:
                try:
                    fdsName = "###"
                    for fcfdPair in fcfdList:
                        if fcfdPair[0] == fc:  # Then  the FDS name is set to = SDW path + FDS Name
                            fdsName = workspace_path + "\\SDW.PDS." + str(fcfdPair[1])

                    # Catch errors (if any)
                    if fdsName == "###":  # Then the FDS name wasn't found for this FC in LUEG_UPDATES table
                        print "\n***WARNING***: " + fc + " not found in LUEG_UPDATES table --> !!!DATA NOT COPIED!!!"
                        no_errors = False
                    if not arcpy.Exists(fdsName):  # Then the FDS in LUEG_UPDATES isn't in SDW (Workspace)
                        print "\n***ERROR***: feature dataset " + str(fcfdPair[1]) + " doesn't exist --> !!!DATA NOT COPIED!!!"
                        no_errors = False

                    if no_errors == True:  # Then no errors caught, continue
                        print 'Processing "{}"'.format(fc)
                        layerName = fdsName + "\\SDW.PDS." + str(fc)
                        topoName  = fdsName + "\\SDW.PDS.topology_" + str(fc)

                        # Delete existing dataset in SDW
                        if arcpy.Exists(layerName):
                            print '  Deleting existing         "{}"'.format(layerName)
                            arcpy.Delete_management(layerName)
                        if arcpy.Exists(topoName):
                            print '  Deleting existing         "{}"'.format(topoName)
                            arcpy.Delete_management(topoName)

                        # Copy dataset from FGDB to LUEG/PDS SDE
                        print '  Copying "{}" to "{}"'.format(fc, fdsName)
                        arcpy.FeatureClassToGeodatabase_conversion(fc,fdsName)

                        # Check for topology requirements
                        c = arcpy.SearchCursor(lueg_updates_table, "\"LAYER_NAME\" = '" + str(fc) + "'")
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

                       # Updating date for FC in LUEG_UPDATES table
                        print "  Updating date for Feature Class in '{}'".format(lueg_updates_table)
                        c1 = arcpy.UpdateCursor(lueg_updates_table ,"\"LAYER_NAME\" = '" + str(fc) + "'")
                        r1 = c1.next()
                        while r1:
                            r1.UPDATE_DATE = dateToday
                            c1.updateRow(r1)
                            r1 = c1.next()
                        del c1, r1

                        # Delete FC from loading gdb
                        print '  Deleting feature class from "{}"'.format(fc)
                        arcpy.Delete_management(fc)

                        # Get the name of the Feature Dataset (w/o the path)
                        # And add it to the a list so we can register and change
                        # Privileges at the Feature Dataset level
                        fdsToRegister.extend([os.path.basename(fdsName)])

                        print ""
                        print '------------------------------------------------'

                except Exception as e:
                    print '*** ERROR! With Feature Class "{}" ***'.format(fc)
                    print str(e)

            #-------------------------------------------------------------------
            # Register and change privileges for any Feature Classes imported'
            unique_fdsToRegister = set(fdsToRegister)  # Set() gets a unique list-no duplicates returned
            print '++++++++++++++++++++++++++++++++++++++++++++++++'
            print '------------------------------------------------'
            print 'Registering Versioning and Change Priviliges for {} Feature Datasets:'.format(str(len(unique_fdsToRegister)))
            print ', '.join(unique_fdsToRegister)

            for fd in unique_fdsToRegister:
                try:
                    fdsName = workspace_path + "\\" + str(fd)
                    print '\nProcessing FD: "{}"'.format(fdsName)

                    # Register feature dataset
                    try:
                        desc = arcpy.Describe(fdsName)
                        if not desc.isVersioned:
                            print '  Registering as versioned'
                            arcpy.RegisterAsVersioned_management(fdsName,"NO_EDITS_TO_BASE")
                    except Exception as e:
                        print "*** Error in versioning ***"
                        print str(e)
                        no_errors = False

                    # Change privileges
                    try:
                        print '  Changing privileges'
                        arcpy.ChangePrivileges_management(fdsName,"SDE_EDITOR","GRANT","GRANT")
                    except Exception as e:
                        print '*** Error in changing privileges ***'
                        print str(e)
                        no_errors = False

                    print '------------------------------------------------'

                except Exception as e:
                    print '*** ERROR! With Feature Dataset "{}" ***'.format(fd)
                    print str(e)

        print ""
        print "Data load to WORKSPACE SDE complete..."
        if no_errors == True:
            print 'SUCCESSFULLY Completed'
        else:
            print 'ERRORS with script'
        print "END TIME " + str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
        logFile.close()
        sys.stdout = oldOutput

    if no_errors == True:
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
    else:  # Then no_errors False and there was an ERROR
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

except Exception as e:
    print "ERROR OCCURRED"
    print "D:\\sde_maintenance\\scripts\\updateWorkspace.py"
    print str(e)
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
    toaddr = lueg_admin_email

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