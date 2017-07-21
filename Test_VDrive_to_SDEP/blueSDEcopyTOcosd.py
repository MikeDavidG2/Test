#-------------------------------------------------------------------------------
# Name:        blueSDEcopyTOcosd.py
# Purpose:
"""
Updates the SanGIS FTP site with zipped FGDBs of each FC or Table from
SDW (Workspace) that has been recently updated.  There is a companion script
that pulls the zipped FGDBs from the FTP site and updates SDEP2 on the County
network.

The Datasets that are sent to the FTP site are controlled by the
LUEG_UPDATES table in SDW (Workspace).  Datasets that are sent to the FTP site
must have been updated within the 'dcutoff', and must satisfy the 'whereClause'

NOTE: Run directly on SOUTHERN server

UPDATES:
  July 2017:
    Significant editing by MG to allow recently updated Tables in SDW to be sent
    to the FTP site.

    Also edited to remove many permanently commented out lines of code,
    reorganized print statements and altered the flow of the script for
    readability.
"""
#
# Author:      Karen Chadwick
# Editors:     Karen Chadwick, Gary Ross, Mike Grue
#-------------------------------------------------------------------------------

import arcpy
import ConfigParser
import datetime
import ftplib
import math
import os
import smtplib
import string
import sys
import time
import zipfile
from email.mime.text import MIMEText

#-------------------------------------------------------------------------------
#                            Set variables
# Set paths
path            = r"D:\sde_maintenance\blue_copyTOcosd"
##path            = r"U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_blue_copyTOcosd"  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing
sdeWorkspace    = r"D:\sde_maintenance\scripts\Database Connections\Atlantic Workspace (pds user).sde"
##sdeWorkspace    = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_SDW.gdb'  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing
tablePath       = os.path.join(sdeWorkspace,"SDW.PDS.LUEG_UPDATES")
##tablePath       = os.path.join(sdeWorkspace,"LUEG_UPDATES")  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing
table_workspace = "manifest_blue2cosd"
#table_warehouse = "blueWarehouse2cosd"  # MG 07/13/17: I don't believe this variable is being used anymore.  Can probably delete.  TODO: ask Gary
ftpfolder       = "ftp/LUEG/transfer_to_cosd"
#ftpfldrwhse     = "ftp/LUEG/transfer_to_blue"  # MG 07/13/17: I don't believe this variable is being used anymore.  Can probably delete.  TODO: ask Gary
cfgfile         = r"D:\sde_maintenance\scripts\configFiles\ftp.txt"
##cfgfile         = r"M:\scripts\configFiles\ftp.txt"  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing

# Log settings
logFileName = os.path.join("D:\sde_maintenance","log","blueSDEcopyTOcosd" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")
##logFileName = os.path.join('U:\grue\Projects\VDrive_to_SDEP_flow\log',"blueSDEcopyTOcosd" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing

# Email settings
email_config_file = r"D:\sde_maintenance\scripts\configFiles\accounts.txt"
##email_config_file = r'M:\scripts\configFiles\accounts.txt'  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing
lueg_admin_email  = ["gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
##lueg_admin_email = ['michael.grue@sdcounty.ca.gov'] # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing

# Misc variables
fcstosend       = 0
delerror        = 0
dcutoff         = 14    #  <-- Change the number of days cutoff here!
delete_files    = True  # If 'True', the FGDB (zipped and unzipped) will be deleted after transfering to FTP site
errors          = False
arcpy.env.overwriteOutput = True
timestart = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
times = time.time()

# List of Feature Classes that shouldn't be sent to FTP
fc2ignore = [
    "ROAD_CHANNELIZERS",
    "ROAD_CHANNELS",
    "ROAD_CULVERTS",
    "ROAD_CURB_MARKINGS",
    "ROAD_CURBS_GUTTERS",
    "ROAD_FEATURES",
    "ROAD_FLASHERS",
    "ROAD_GUARDRAILS",
    "ROAD_INTERSECTIONS",
    "ROAD_LEGENDS","ROAD_SEGMENTS",
    "ROAD_SIDEWALKS",
    "ROAD_SIGNAL_DEVICES",
    "ROAD_SIGNS",
    "ROAD_STATIONS",
    "ROAD_STREET_LIGHTS",
    "ROAD_STREET_NAME_SIGNS",
    "ROAD_STRIPING",
    "ROAD_STRUCTURES",
    "ROAD_TRAFFIC_SIGNALS"]

# Create a log file and send print statements to it
logFile     = open(logFileName,"w")
old_output = sys.stdout
sys.stdout  = logFile  # TODO: uncomment before moving to PROD

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                             DEFINE FUNCTIONS
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION: zipFGDB()
def zipFGDB(fgdb):
    infolder = fgdb
    outfile = fgdb + ".zip"
    try:
        zip = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
        zipws(infolder, zip, True)
        zip.close()
    except:
        # Delete zip file if exists
        if os.path.exists(outfile):
            os.unlink(outfile)
            zip = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_STORED)
            zipws(infolder, zip, True)
            zip.close()
            print "Unable to compress zip file contents"

#-------------------------------------------------------------------------------
#                           FUNCTION: zipws()
def zipws(path, zip, keep):
    path = os.path.normpath(path)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            if not file.endswith('.lock'):
                try:
                    if keep:
                        zip.write(os.path.join(dirpath, file).encode("latin-1"),os.path.join(os.path.basename(path), os.path.join(dirpath, file)[len(path)+len(os.sep):]))
                    else:
                        zip.write(os.path.join(dirpath, file).encode("latin-1"),os.path.join(dirpath[len(path):], file).encode("latin-1"))

                except:
                    print "Error adding " + str(file)
                    errors = True
    return None

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                               RUN SCRIPT
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
print '************************************************************************'
print "                   blueSDEcopyTOcosd.py "
print 'Now: {}\n'.format(str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
arcpy.env.workspace = path

# Check for Datasets to be copied from SDW (Workspace) to FTP site
try:
    # Get the dataset info
    blueFDlist = list([])
    blueFClist = list([])
    blueDATElist = list([])
    cntyFDlist = list([])
##    ftplist = []  # TODO: Delete this line if script works.  No need to have
    whereClause = '"EDIT_LOCATION" = ' + "'BLUE'" + ' AND "COUNTY_FDS" IS NOT NULL'
    print 'Getting dataset info from table: "{}"\n  Where: {}\n'.format(tablePath, whereClause)
    with arcpy.da.SearchCursor(tablePath,["FEATURE_DATASET","LAYER_NAME","UPDATE_DATE","COUNTY_FDS"],whereClause) as rowcursor:
        for row in rowcursor:
            blueFDlist.extend([str(row[0])])
            blueFClist.extend([str(row[1])])
            blueDATElist.extend([str(row[2])])
            cntyFDlist.extend([str(row[3])])
    del rowcursor
except Exception as e:
    print '*** ERROR with getting info from table. ***'
    print str(e)
    errors = True

# MG 07/13/17: I moved the below commented out section to the Copy/ftp the LUEG_UPDATES (workspace) table section below.  This comment and the commented out section below can be deleted if below works
##    # Create a GDB for the copy table, if it doesn't exist already
##    table_workspace_gdb = table_workspace + ".gdb"
##    table_workspace_gdb_path = os.path.join(path,table_workspace_gdb)
##    print table_workspace_gdb_path
##    if arcpy.Exists(table_workspace_gdb_path):
##        print 'table_workspace_gdb_path exists'  # TODO: Delete print statement
##        arcpy.management.Delete(table_workspace_gdb_path)
##    else:
##        print 'table_workspace_gdb_path DOES NOT exist'  # TODO: Delete print statement
##        arcpy.management.CreateFileGDB(path,table_workspace_gdb)
##        print "\nInitializing copy table: " + str(table_workspace)
##        # Then create a table, add fields, and initialize InsertCursor
##        arcpy.management.CreateTable(table_workspace_gdb_path,table_workspace)
##        arcpy.env.workspace = table_workspace_gdb_path
##        arcpy.management.AddField(table_workspace,"COUNTY_FDS","TEXT","","",50)
##        arcpy.management.AddField(table_workspace,"FEATURE_CLASS","TEXT","","",50)

# MG 07/13/17: I dedented the below section (to the 'except') after commenting out the above section.  This comment can be deleted if it works

for key, fcname in enumerate(blueFClist):
    try:
        # Get the number of days since the last update (deltadays)
        temp = blueDATElist[key].split(" ")  # i.e. splits '2017-03-27 00:00:00'
        datepart = temp[0]                   # get only    '2017-03-27'
        temp = datepart.split("-")           # split the   'YYYY MM DD'
        dateblue = datetime.date(int(temp[0]),int(temp[1]),int(temp[2]))  # Get a dt object of when fc last updated
        datenow = datetime.date.today()
        deltadate = datenow - dateblue  # Get # of days between today and last update date in BLUE
        deltadays = int(deltadate.days)

        # If the num of days since last update (deltadays) is less than the cutoff,
        #   copy the Dataset then zip and FTP
        if deltadays <= dcutoff:  # Then send the dataset to the FTP site
            print '------------------------------------------------------------'
            print 'Processing {}\n'.format(fcname)
            print '  Dataset: "{}" was updated "{}" day/s ago on "{}".  Will send to FTP.'.format(fcname, str(deltadays), str(dateblue))


            # Get the FDS of the dataset from list and join the paths for those not in a FDS ('None' in LUEG_UPDATES table)
            if blueFDlist[key] == 'None':  # if FEATURE_DATASET == 'None', it is probably a Table.  Do not insert a FDS in the path
                infcpath = os.path.join(sdeWorkspace, "SDW.PDS." + fcname)
##                infcpath = os.path.join(sdeWorkspace, fcname)  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing

            if blueFDlist[key] != 'None':  # Add the FEATURE_DATASET (blueFDlist[key]) between 'sdeWorkspace' and 'fcname'
                infcpath = os.path.join(sdeWorkspace,"SDW.PDS." + blueFDlist[key],"SDW.PDS." + fcname)
##                infcpath = os.path.join(sdeWorkspace, blueFDlist[key], fcname)  # MG 07/13/17: Set variable to DEV settings.  TODO: Delete after testing


            # Make sure the Dataset exists in the listed location
            if not arcpy.Exists(infcpath):
                print '\n***!!!ERROR!!!*** Dataset: "{}" not found in FD: "{}"'.format(fcname, blueFDlist[key])
                errors = True
            else:
                if fcname in fc2ignore:  # Ignore items in 'fc2ignore' list
                    print '"{}" in fc2ignore list.  Not sending to FTP'.format(fcname)

                else:
                    # Set paths
                    gdbname = fcname + ".gdb"
                    gdbpath = os.path.join(path,gdbname)
                    outfcpath = os.path.join(gdbpath,fcname)


                    # Create empty FGDB
                    print '  Creating FGDB: "{}\{}"'.format(path, gdbname)
                    arcpy.management.CreateFileGDB(path,gdbname)


                    # Get the dataset type to decide how to copy the dataset
                    #   (i.e. as a Feature Class or as a Table)
                    desc = arcpy.Describe(infcpath)
                    dataset_type = desc.datasetType

                    # Copy the dataset depending on what data type it is
                    if dataset_type == 'FeatureClass':
                        arcpy.management.CopyFeatures(infcpath,outfcpath)
                        print '  Copied "{}":\n    From: "{}"\n      To: "{}"\n      As: A {}'.format(fcname, infcpath, outfcpath, dataset_type)
                    if dataset_type == 'Table':
                        arcpy.CopyRows_management(infcpath, outfcpath)
                        print '  Copied "{}":\n    From: "{}"\n      To: "{}"\n      As: A {}'.format(fcname, infcpath, outfcpath, dataset_type)

                    # Warn users if the dataset_type is not a 'Table' or a 'FeatureClass'
                    if (dataset_type != 'Table') or (dataset_type != 'FeatureClass'):
                        '*** WARNING! Datasets with types of "{}" cannot currently be copied'.format(dataset_type)


                    # Delete old zip file if needed
                    zippath = str(gdbpath) + ".zip"
                    if arcpy.Exists(zippath):
                        print '  Deleting old zipfile at: "{}"'.format(zippath)
                        os.unlink(zippath) # Delete_management fails (zipfile) --> use unlink

                    # Zip the FGDB
                    print '  Zipping FGDB to: "{}.zip"'.format(gdbpath)
                    zipFGDB(gdbpath)

                    # Send the zipped FGDB to the FTP site
                    if arcpy.Exists(zippath):
                    # MG 07/13/17: Commented out.  TODO: Uncomment out when done testing. and delete this comment when working
                        config = ConfigParser.ConfigParser()
                        config.read(cfgfile)
                        usr = config.get("sangis","usr")
                        pwd = config.get("sangis","pwd")
                        adr = config.get("sangis","adr")
                        os.chdir(path)
                        ftp = ftplib.FTP(adr)
                        ftp.login(usr,pwd)
                        ftp.cwd(ftpfolder)
                        print '  FTPing dataset'
                        zipname = str(gdbname) + ".zip"
                        try: ftp.delete(zipname)
                        except: d = 0 ### no action if file not on ftp site
                        with open(zippath,"rb") as openFile:
                            ftp.storbinary("STOR " + str(zipname),openFile)
                        ftp.quit()
##                        ftplist.append(str(fcname))  # TODO: remove this line if script works, no need to have this list

                        # Delete the unzipped FGDB
                        if arcpy.Exists(gdbpath) and delete_files:
                            print '  Deleting the unzipped FGDB at: {}'.format(gdbpath)
                            arcpy.management.Delete(gdbpath)

                        # Delete the zipped FGDB
                        if arcpy.Exists(zippath) and delete_files:
                            print '  Deleting the   zipped FGDB at: {}'.format(zippath)
                            os.unlink(zippath)

            fcstosend += 1

            print ''

    except Exception as e:
        print "*** ERROR Processing Dataset ***"
        print str(e)
        print arcpy.GetMessages()
        errors = True

#-------------------------------------------------------------------------------
#                     Copy the workspace LUEG_UPDATES table
# Send it even if there are no Datasets to ftp
#   (the table may be used by multiple scripts on CoSD)
try:
    # Copy/ftp the LUEG_UPDATES (workspace) table
    print '---------------------------------------------------------------------'
    print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '---------------------------------------------------------------------'
    print 'Copying / FTPing the LUEG_UPDATES (workspace) table'
    table_workspace_gdb = table_workspace + ".gdb"
    table_workspace_gdb_path = os.path.join(path,table_workspace_gdb)

    # Delete Old FGDB if it exists
    if arcpy.Exists(table_workspace_gdb_path):
        print 'Deleting Old FGDB: "{}"'.format(table_workspace_gdb_path)
        arcpy.management.Delete(table_workspace_gdb_path)

    # Create a FGDB to contain the table
    print 'Creating FGDB: "{}\{}"\n'.format(path, table_workspace_gdb)
    arcpy.management.CreateFileGDB(path,table_workspace_gdb)

    # Copy the LUEG_UPDATE table from SDW (workspace) to the working folder (path)
    copytblpath = os.path.join(table_workspace_gdb_path,table_workspace)
    print 'Copying: "{}"\n     To: "{}"'.format(tablePath, copytblpath)
    arcpy.CopyRows_management(tablePath, copytblpath)

    # Determine whether any Datasets were prepared for ftp
    if fcstosend == 0:
        print "*** WARNING: No Datasets prepared for ftp; date search window = " + str(dcutoff) + " days"
        print "FTPing data table anyway..."

    # Zip/ftp the copy table
    zippath = table_workspace_gdb_path + ".zip"

    if arcpy.Exists(zippath):
        try:
            print 'Deleting Old: "{}"'.format(zippath)
            os.unlink(zippath) # Delete_management fails --> use unlink
        except:
            print "*** WARNING: delete not sucessful! ***"
            delerror = 1
            errors = True

    if delerror == 0:
        print '\nZipping: "{}"'.format(table_workspace_gdb_path)
        zipFGDB(table_workspace_gdb_path)
    else:
        print "\nWARNING: skipping workspace table gdb zip --> sending old table ...!!!..."
    if arcpy.Exists(zippath):
        # MG TODO: Uncomment out before done testing, then try testing before going to PROD, and delete this comment
        config = ConfigParser.ConfigParser()
        config.read(cfgfile)
        usr = config.get("sangis","usr")
        pwd = config.get("sangis","pwd")
        adr = config.get("sangis","adr")
        os.chdir(path)
        ftp = ftplib.FTP(adr)
        ftp.login(usr,pwd)
        ftp.cwd(ftpfolder)
        print "FTPing copy (workspace) table\n"
        zipname = table_workspace_gdb + ".zip"
        try: ftp.delete(zipname)
        except: d = 0 ### no action if file not on ftp site
        openFile = open(zippath,"rb")
        ftp.storbinary("STOR " + str(zipname),openFile)
        ftp.quit()

        # Clean up the files...
        #   Delete the unzipped FGDB
        if arcpy.Exists(table_workspace_gdb_path) and delete_files:
            print '  Deleting the unzipped FGDB at: "{}"'.format(table_workspace_gdb_path)
            arcpy.management.Delete(table_workspace_gdb_path)

        # Below is commented out because the script is unable to delete this zipped FGDB, I wonder why... TODO: find out.
##        # MG TODO: Ask Gary if the below delete should be kept.  The orig script didn't delete this zipped FGDB, but I'm not sure why not...
##        #   Delete the zipped FGDB
##        if arcpy.Exists(zippath) and delete_files:
##            print '  Deleting the   zipped FGDB at: "{}"'.format(zippath)
##            os.unlink(zippath)

    else:
        print "\nERROR: zip file does not exist at: '{}'".format(zippath)

except Exception as e:
    print "*** ERROR processing LUEG_UPDATES ***"
    print str(e)
    print arcpy.GetMessages()
    errors = True

# MG TODO: The below was already commented out when I got the script, ask Gary if we can delete.
##### Copy/ftp the LUEG_UPDATES (warehouse) table
##try:
##    # Copy the warehouse LUEG_UPDATES table
##    # Send it even if there are no FCs to ftp (the table may be used by multiple scripts on CoSD)
##    # Create a gdb for the table
##    table_warehouse_gdb = table_warehouse + ".gdb"
##    table_warehouse_gdb_path = os.path.join(path,table_warehouse_gdb)
##    if arcpy.Exists(table_warehouse_gdb_path):
##        arcpy.management.Delete(table_warehouse_gdb_path)
##    arcpy.management.CreateFileGDB_management(path,table_warehouse_gdb)
##    # Copy the table to the gdb
##    arcpy.management.MakeTableView(tableWarehouse,"whseUPDATEview")
##    copytwhspth = os.path.join(table_warehouse_gdb_path,table_warehouse)
##    arcpy.management.CopyRows("whseUPDATEview",copytwhspth)
##    print "\nCopied LUEG_UPDATE (warehouse) table..."
##    # Zip/ftp the copy table
##    zipname = str(table_warehouse_gdb) + ".zip"
##    zippath = str(table_warehouse_gdb_path) + ".zip"
##    if arcpy.Exists(zippath):
##        delerror = 1
##        print "   table zipfile (warehouse) needs deleting"
##        try:
##            os.unlink(zippath) # Delete_management fails --> use unlink
##            print "   delete sucessful"
##            delerror = 0
##        except:
##            print "   WARNING: delete not sucessful!"
##    if delerror == 0:
##        print "\nZipping warehouse table gdb ..."
##        zipFGDB(table_warehouse_gdb_path)
##    else:
##        print "\nWARNING: skipping warehouse table gdb zip --> sending old table ...!!!..."
##    if arcpy.Exists(zippath):
##        if arcpy.Exists(table_warehouse_gdb_path):
##            arcpy.Delete_management(table_warehouse_gdb_path)
##        config = ConfigParser.ConfigParser()
##        config.read(cfgfile)
##        usr = config.get("sangis","usr")
##        pwd = config.get("sangis","pwd")
##        adr = config.get("sangis","adr")
##        os.chdir(path)
##        ftp = ftplib.FTP(adr)
##        ftp.login(usr,pwd)
##        ftp.cwd(ftpfldrwhse)
##        print "FTPing copy (warehouse) table ...\n"
##        try: ftp.delete(zipname)
##        except: d = 0 ### no action if file not on ftp site
##        openFile = open(zippath,"rb")
##        ftp.storbinary("STOR " + str(zipname),openFile)
##        ftp.quit()
##    else:
##        print "\nERROR: when sending warehouse table ..."
##except:
##    errors = True
##    print "********* FAILED TO COPY/FTP THE WAREHOUSE TABLE *********\n"

# Clean up zipfiles

# MG commented out:  The below section handles deleting the zipped FGDB.  However, I have handled that above (right after a zip file is sent to the FTP).  Recommend removing.  TODO: Ask Gary
##try:
##    # Delete Dataset zipfiles
##    for fc in ftplist:
##        zipname = fc + ".gdb.zip"
##        zippath = path + zipname
##        if arcpy.Exists(zippath):
##            print "  cleaning up: deleting zipfile " + str(zipname)
##            os.unlink(zippath) # Delete_management fails (zipfile) --> use unlink
##            print "    zipfile deleted..."
##    # Delete the workspace table zipfile
##    tblzipname = str(table_workspace_gdb) + ".zip"
##    tblzippath = str(table_workspace_gdb_path) + ".zip"
##    # Table zipfile won't delete --> leave in folder
##    print "  IGNORING workspace table zipfile: " + str(tblzipname)

# MG: The below commented out section was already commented out when I started editing.  Recommend removing.  TODO: Ask Gary
##    # Delete the warehouse table zipfile #KC added section 7/24/2015
##    tblzipwhsn = table_warehouse_gdb + ".zip"
##    tblzwhspth = table_warehouse_gdb_path + ".zip"
##    # Table zipfile won't delete --> leave in folder
##    print "  IGNORING warehouse table zipfile: " + str(tblzipwhsn)

# MG commented out: Unsure if this is a reminant, doesn't look to be doing anything now.  Recommend removing.  TODO: Ask Gary
##    # Clean up any ancillary files (.cpg, .dbf, .dbf.xml)
##    dirFiles = os.listdir(path)
##    for dirFile in dirFiles:
##        if os.path.isfile(dirFile) and str(table_workspace) in str(dirFile) and str(dirFile) != str(tblzipname):
##            dirFilePath = path + str(dirFile)
##            print "  cleaning up: deleting file " + str(dirFile)
##            os.unlink(dirFilePath)

# MG commented out:  Not needed if the whole 'try' is commented out (to be deleted).  TODO: Ask Gary
##except:
##    errors = True
##    print "********* FAILED TO DELETE ZIPFILES *********"

try:
    # END processing - do clerical messaging
    timeendSDEC = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    timeeSDEC = time.time()
    # Calculate time duration
    timeElapsed = timeeSDEC - times
    dhours = int(math.floor(timeElapsed/3600))
    if dhours < 10:
        strdhours = "0" + str(dhours)
    else:
        strdhours = str(dhours)
    deltam = timeElapsed - (dhours*3600)
    dminutes = int(math.floor(deltam/60))
    if dminutes < 10:
        strdminutes = "0" + str(dminutes)
    else:
        strdminutes = str(dminutes)
    deltas = deltam - (dminutes*60)
    dseconds = int(round(deltas))
    if dseconds < 10:
        strdseconds = "0" + str(dseconds)
    else:
        strdseconds = str(dseconds)
    print ""
    print "Process started at " + str(timestart)
    print "      and ended at " + str(timeendSDEC)
    print "   Duration = " + strdhours + ":" + strdminutes + ":" + strdseconds
    print "********************************************************************"

except Exception as e:
    print '*** ERROR with end processing / messaging ***'
    errors = True

sys.stdout = old_output
logFile.close()

#-------------------------------------------------------------------------------
#                                       Email

# Set Subject depending on if errors or not
if errors == True:
    email_subject = 'ERROR running blueSDEcopyTOcosd.py'
if errors == False:
    email_subject = 'SUCCESS running blueSDEcopyTOcosd.py'

import smtplib, ConfigParser
from email.mime.text import MIMEText

# Get username and pwd
config = ConfigParser.ConfigParser()
config.read(email_config_file)
email_usr = config.get("email","usr")
email_pwd = config.get("email","pwd")

# Set from and to addresses
fromaddr = "dplugis@gmail.com"
toaddr = lueg_admin_email

# Get the log file to add to email body
fp = open(logFileName,"rb")
msg = MIMEText(fp.read())
fp.close()

# Set visible info in email
msg['Subject'] = email_subject
msg['From'] = "Python Script"
msg['To'] = "SDE Administrator"

# Email
s = smtplib.SMTP('smtp.gmail.com', 587)
s.ehlo()
s.starttls()
s.ehlo()
s.login(email_usr,email_pwd)
s.sendmail(fromaddr,toaddr,msg.as_string())
s.quit()