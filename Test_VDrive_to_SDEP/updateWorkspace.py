# Loads data from local file geodatabase into Workspace
# Run on directly on server Southern
# Update December 2014 to account for new feature datasets in SDE
# Update February 2017 10.4.1 and new server

# MG 07/07/17: I had to make an entry in LUEG_UPDATES table in FALSE_SDW for the SITES_DATA FC to be imported.  TODO: Add the record to the live LUEG_UPDATES table on SDW

import sys, string, os, time, math, arcpy
from datetime import date

arcpy.env.overwriteOutput = True  #  MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing

timestart = str(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()))
dateToday = str(time.strftime("%m/%d/%Y", time.localtime()))

try:
    #---------------------------------------------------------------------------
    # START MG 07/07/17: Added to allow 'Tables' (not just Feature Classes) to update Workspace
    # TODO: Create a DEV and PROD version of the below paths (i.e. fgdb = r'D:\sde\sde_load.gdb')

    fgdb = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_sde_load.gdb'
    arcpy.env.workspace = fgdb
    table_list = arcpy.ListTables()

    # END MG 07/07/17
    #---------------------------------------------------------------------------

    fgdb = r"D:\sde\sde_load.gdb\workspace"
    fgdb = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_sde_load.gdb\workspace'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
    arcpy.env.workspace = fgdb
    fcList = arcpy.ListFeatureClasses()

    eMailLogic = 0 # Added line 12/10/2014 - Email logic

    if ((fcList != []) or (table_list != [])) : # There are datasets to move  # MG 07/07/17: add 'table_list' check.  TODO: show Gary

        # Create log file
        oldOutput = sys.stdout
        logFileName = str("D:\\sde_maintenance\\log\\updateWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")
        logFileName = str(r"U:\grue\Projects\VDrive_to_SDEP_flow\log\updateWorkspace_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        logFile = open(logFileName,"w")
##        sys.stdout = logFile  # MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
        print "START TIME " + str(timestart)

        print ""

        dataList = arcpy.ListFeatureClasses()

        pathName  = "Database Connections\\Atlantic Workspace (pds user).sde"
        pathName  = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDW.gdb'  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
        tableName = pathName + "\\SDW.PDS.LUEG_UPDATES"
        tableName = pathName + "\\LUEG_UPDATES"  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing
##        adminSDE  = "Database Connections\\Atlantic Workspace (sa user).sde"  # MG 07/07/17: Set variable to DEV settings.  TODO: Uncomment out after testing

#         MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
##        # Disconnect users from the database (added 3/12/13)
##        try:
##            usrList = arcpy.ListUsers(adminSDE)
##            for user in usrList:
##                if user.Name[1:5] == "BLUE":
##                    arcpy.DisconnectUser(adminSDE,user.ID)
##        except:
##            print "ERROR disconnecting users"
##            print arcpy.GetMessages()


        with arcpy.da.SearchCursor(tableName,["LAYER_NAME","FEATURE_DATASET"]) as rowcursor:
            fcfdList = list(rowcursor)
        del rowcursor


        fdsToRegister = list([])


        if dataList != []:
            for fc in dataList:

                fdsName = "none"
                for fcfdPair in fcfdList:
                    if fcfdPair[0] == fc:
                        fdsName = pathName + "\\SDW.PDS." + str(fcfdPair[1])
                        fdsName = pathName + "\\" + str(fcfdPair[1])  # MG 07/07/17: Set variable to DEV settings.  TODO: Delete after testing

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

##                        print "  Deleting feature class from loading gdb..."
##                        arcpy.Delete_management(str(fc))  # MG 07/07/17: DEV settings.  TODO: Uncomment out before finish testing and test uncommented.  Delete after testing.

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

#         MG 07/07/17: DEV settings.  TODO: Uncomment out after testing
##        if dataList != []:
##            for fd in fdsToRegister:
##                print "pathName",pathName
##                print "fd",fd
##                fdsName = pathName + "\\SDW.PDS." + str(fd)
##
##                # Register feature dataset
##                try:
##                    desc = arcpy.Describe(fdsName)
##                    if not desc.isVersioned:
##                        arcpy.RegisterAsVersioned_management(fdsName,"NO_EDITS_TO_BASE")
##                        print "Feature dataset " + str(fd) + " registered as versioned..."
##                except:
##                    print "error in versioning"
##                    eMailLogic = 1
##
##                # Change privileges
##                arcpy.ChangePrivileges_management(fdsName,"SDE_EDITOR","GRANT","GRANT")
##                print "Feature dataset " + str(fd) + " privileges changed..."

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
##        toaddr = ["gary.ross@sdcounty.ca.gov",]
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
##        toaddr = ["gary.ross@sdcounty.ca.gov",]
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
##    toaddr = ["gary.ross@sdcounty.ca.gov",]
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
