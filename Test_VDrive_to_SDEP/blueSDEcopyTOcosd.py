################################################
###  blueSDEcopyTOcosd.py                    ###
###  Copy, zip and ftp FCs that have been    ###
###    edited and need to be copied to the   ###
###    County.  Ignores LEAMS FCs (ROAD_*).  ###
################################################
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

old_output = sys.stdout
timestart = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
times = time.time()

arcpy.env.overwriteOutput = True

path            = r"D:\sde_maintenance\blue_copyTOcosd"
sdeWorkspace    = r"Database Connections\Atlantic Workspace (pds user).sde"
sdeWarehouse    = r"Database Connections\Atlantic Warehouse (sangis user).sde"
tablePath       = os.path.join(sdeWorkspace,"SDW.PDS.LUEG_UPDATES")
tableWarehouse  = os.path.join(sdeWarehouse,"SDE.SANGIS.LUEG_UPDATES")
table_workspace = "manifest_blue2cosd"
#table_warehouse = "blueWarehouse2cosd"
ftpfolder       = "ftp/LUEG/transfer_to_cosd"
ftpfldrwhse     = "ftp/LUEG/transfer_to_blue"
cfgfile         = r"D:\sde_maintenance\scripts\configFiles\ftp.txt"
fc2ignore       = [
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
eMailSDEC       = 0
fcstosend       = 0
delerror        = 0
dcutoff         = 14    ###  <-- Change the number of days cutoff here! 

logFileName = os.path.join("D:\sde_maintenance","log","blueSDEcopyTOcounty" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")
logFile     = open(logFileName,"w")
sys.stdout  = logFile

### Define zipping processes
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
    return None


arcpy.env.workspace = path

print "****************** BLUESDECOPYTOCOUNTY.PY *************************"

### Check for FCs to be copied across
try:
    # Get the FC info
    print str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + " | Checking for FCs to copy..."
    blueFDlist = list([])
    blueFClist = list([])
    blueDATElist = list([])
    cntyFDlist = list([])
    ftplist = []
    whereClause = '"EDIT_LOCATION" = ' + "'BLUE'" + ' AND "COUNTY_FDS" IS NOT NULL'
    with arcpy.da.SearchCursor(tablePath,["FEATURE_DATASET","LAYER_NAME","UPDATE_DATE","COUNTY_FDS"],whereClause) as rowcursor:
        for row in rowcursor:
            blueFDlist.extend([str(row[0])])
            blueFClist.extend([str(row[1])])
            blueDATElist.extend([str(row[2])])
            cntyFDlist.extend([str(row[3])])
    del rowcursor
    # Check for relevant dates
    datenow = datetime.date.today()
    # Create a GDB for the copy table, if it doesn't exist already
    table_workspace_gdb = table_workspace + ".gdb"
    table_workspace_gdb_path = os.path.join(path,table_workspace_gdb)
    if arcpy.Exists(table_workspace_gdb_path):
        arcpy.management.Delete(table_workspace_gdb_path)
    else:
        arcpy.management.CreateFileGDB(path,table_workspace_gdb)
        print "\nInitializing copy table: " + str(table_workspace)
        # Then create a table, add fields, and initialize InsertCursor
        arcpy.management.CreateTable(table_workspace_gdb_path,table_workspace)
        arcpy.env.workspace = table_workspace_gdb_path
        arcpy.management.AddField(table_workspace,"COUNTY_FDS","TEXT","","",50)
        arcpy.management.AddField(table_workspace,"FEATURE_CLASS","TEXT","","",50)

        for key, fc in enumerate(blueFClist):
            temp = blueDATElist[key].split(" ")
            datepart = temp[0]
            temp = datepart.split("-")
            dateblue = datetime.date(int(temp[0]),int(temp[1]),int(temp[2]))
            deltadate = datenow - dateblue
            deltadays = int(deltadate.days)
            # If the date difference is less than the cutoff, copy the FC then zip and FTP
            if deltadays <= dcutoff:
                # Copy the FC
                print "\n" + str(blueFClist[key]) + " - date = " + str(dateblue) + " (" + str(deltadays) + " day/s)"
                fcname = str(fc)
                gdbname = fcname + ".gdb"
                gdbpath = os.path.join(path,gdbname)
                print gdbpath
                infcpath = os.path.join(sdeWorkspace,"SDW.PDS." + blueFDlist[key],"SDW.PDS." + fcname)
                print infcpath
                # Make sure the FC exists in the listed location
                if not arcpy.Exists(infcpath):
                    print "***!!!ERROR!!!***: FC " + str(fcname) + " not found in FD " + str(blueFDlist[key])
                    eMailSDEC = 1
                else:
                    print "got here"
                    if fcname not in fc2ignore:
                        print "in here"
                        fcstosend += 1
                        outfcpath = os.path.join(gdbpath,fcname)
                        print outfcpath
                        arcpy.management.CreateFileGDB(path,gdbname)
                        print "Copying " + fcname + " ..."
                        arcpy.management.CopyFeatures(infcpath,outfcpath)
                        # Zip the FC then delete FC
                        zipname = str(gdbname) + ".zip"
                        zippath = str(gdbpath) + ".zip"
                        if arcpy.Exists(zippath):
                            print "   zipfile needs deleting"
                            os.unlink(zippath) # Delete_management fails (zipfile) --> use unlink
                            print "   delete sucessful"
                        print "Zipping GDB ..."
                        zipFGDB(gdbpath)
                        if arcpy.Exists(zippath):
                            if arcpy.Exists(gdbpath):
                                arcpy.management.Delete(gdbpath)
                        # FTP the FC
                        config = ConfigParser.ConfigParser()
                        config.read(cfgfile)
                        usr = config.get("sangis","usr")
                        pwd = config.get("sangis","pwd")
                        adr = config.get("sangis","adr")
                        os.chdir(path)
                        ftp = ftplib.FTP(adr)
                        ftp.login(usr,pwd)
                        ftp.cwd(ftpfolder)
                        print "FTPing feature class ..."
                        try: ftp.delete(zipname)
                        except: d = 0 ### no action if file not on ftp site
                        with open(zippath,"rb") as openFile:
                            ftp.storbinary("STOR " + str(zipname),openFile)
                        ftp.quit()
                        ftplist.append(str(fcname))
except:
    eMailSDEC = 1
    print "********* FAILED TO CHECK ALL FCs *********"
    print arcpy.GetMessages()

### Copy/ftp the LUEG_UPDATES (workspace) table
try:    
    # Copy the workspace LUEG_UPDATES table
    # Send it even if there are no FCs to ftp (the table may be used by multiple scripts on CoSD)
    arcpy.MakeTableView_management(tablePath,"UPDATEview")
    copytblpath = os.path.join(table_workspace_gdb_path,table_workspace)
    arcpy.management.CopyRows("UPDATEview",copytblpath)
    print "\nCopied LUEG_UPDATE (workspace) table..."
    # Determine whether any FCs were prepared for ftp
    if fcstosend == 0:
        print "\nWARNING: No FCs prepared for ftp; date search window = " + str(dcutoff) + " days"
        print "FTPing data table anyway..."
    # Zip/ftp the copy table
    zipname = table_workspace_gdb + ".zip"
    zippath = table_workspace_gdb_path + ".zip"
    if arcpy.Exists(zippath):
        delerror = 1
        print "   table zipfile (workspace) needs deleting"
        try:
            os.unlink(zippath) # Delete_management fails --> use unlink
            print "   delete sucessful"
            delerror = 0
        except:
            print "   WARNING: delete not sucessful!"
    if delerror == 0:
        print "\nZipping workspace table gdb ..."
        zipFGDB(table_workspace_gdb_path)
    else:
        print "\nWARNING: skipping workspace table gdb zip --> sending old table ...!!!..."
    if arcpy.Exists(zippath):
        if arcpy.Exists(table_workspace_gdb_path):
            arcpy.management.Delete(table_workspace_gdb_path)
        config = ConfigParser.ConfigParser()
        config.read(cfgfile)
        usr = config.get("sangis","usr")
        pwd = config.get("sangis","pwd")
        adr = config.get("sangis","adr")
        os.chdir(path)
        ftp = ftplib.FTP(adr)
        ftp.login(usr,pwd)
        ftp.cwd(ftpfolder)
        print "FTPing copy (workspace) table ...\n"
        try: ftp.delete(zipname)
        except: d = 0 ### no action if file not on ftp site
        openFile = open(zippath,"rb")
        ftp.storbinary("STOR " + str(zipname),openFile)
        ftp.quit()
    else:
        print "\nERROR: when sending workspace table ..."
except:
    eMailSDEC = 1
    print "********* FAILED TO COPY/FTP THE WORKSPACE TABLE *********\n"

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
##    eMailSDEC = 1
##    print "********* FAILED TO COPY/FTP THE WAREHOUSE TABLE *********\n"

### Clean up zipfiles
try:
    # Delete FC zipfiles
    for fc in ftplist:
        zipname = fc + ".gdb.zip"
        zippath = path + zipname
        if arcpy.Exists(zippath):
            print "  cleaning up: deleting zipfile " + str(zipname)
            os.unlink(zippath) # Delete_management fails (zipfile) --> use unlink
            print "    zipfile deleted..."
    # Delete the workspace table zipfile
    tblzipname = str(table_workspace_gdb) + ".zip"
    tblzippath = str(table_workspace_gdb_path) + ".zip"
    # Table zipfile won't delete --> leave in folder
    print "  IGNORING workspace table zipfile: " + str(tblzipname)
##    # Delete the warehouse table zipfile #KC added section 7/24/2015
##    tblzipwhsn = table_warehouse_gdb + ".zip"
##    tblzwhspth = table_warehouse_gdb_path + ".zip"
##    # Table zipfile won't delete --> leave in folder
##    print "  IGNORING warehouse table zipfile: " + str(tblzipwhsn)
    # Clean up any ancillary files (.cpg, .dbf, .dbf.xml)
    dirFiles = os.listdir(path)
    for dirFile in dirFiles:
        if os.path.isfile(dirFile) and str(table_workspace) in str(dirFile) and str(dirFile) != str(tblzipname):
            dirFilePath = path + str(dirFile)
            print "  cleaning up: deleting file " + str(dirFile)
            os.unlink(dirFilePath)
except:
    eMailSDEC = 1
    print "********* FAILED TO DELETE ZIPFILES *********"

### END processing - do clerical messaging
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
print "   Duration = " + strdhours + ":" + strdminutes + ":" + strdseconds + " hours"
print "***************************************************************************"
##del resultgdbI

if eMailSDEC == 0:
    sys.stdout = old_output
    logFile.close()

    # email
    import smtplib, ConfigParser
    from email.mime.text import MIMEText

    configSDEC = ConfigParser.ConfigParser()
    configSDEC.read(r"D:\sde_maintenance\scripts\configFiles\accounts.txt")
    email_usrSDEC = configSDEC.get("email","usr")
    email_pwdSDEC = configSDEC.get("email","pwd")

    msgSDEC = MIMEText("")

    fromaddrSDEC       = "dplugis@gmail.com"
    toaddrSDEC         = ["gary.ross@sdcounty.ca.gov",]
    msgSDEC['Subject'] = "BLUE SDE COPY UPDATE - complete"
    msgSDEC['From']    = "Python Script"
    msgSDEC['To']      = "IRP Administrator"

    sSDEC = smtplib.SMTP('smtp.gmail.com', 587)
    sSDEC.ehlo()
    sSDEC.starttls()
    sSDEC.ehlo()
    sSDEC.login(email_usrSDEC,email_pwdSDEC)
    sSDEC.sendmail(fromaddrSDEC,toaddrSDEC,msgSDEC.as_string())
    sSDEC.quit()
    
if eMailSDEC == 1:
    print ""
    print "AN ERROR HAS OCCURRED IN BLUESDECOPYTOCOUNTY.PY (" + str(time.strftime("%Y%m%d %H:%M:%S", time.localtime())) + ")..."
    print ""
    print arcpy.GetMessages()
    
    sys.stdout = old_output
    logFile.close()
    
    # email
    import smtplib, ConfigParser
    from email.mime.text import MIMEText
    
    configSDEC = ConfigParser.ConfigParser()
    configSDEC.read(r"D:\sde_maintenance\scripts\configFiles\accounts.txt")
    email_usrSDEC = configSDEC.get("email","usr")
    email_pwdSDEC = configSDEC.get("email","pwd")
    
    fpSDEC = open(logFileName,"rb")
    msgSDEC = MIMEText(fpSDEC.read())
    fpSDEC.close()
    
    fromaddrSDEC       = "dplugis@gmail.com"
    toaddrSDEC         = ["gary.ross@sdcounty.ca.gov",]
    msgSDEC['Subject'] = "ERROR with BLUE SDE COPY"
    msgSDEC['From']    = "Python Script"
    msgSDEC['To']      = "IRP Administrator"
    
    sSDEC = smtplib.SMTP('smtp.gmail.com', 587)
    sSDEC.ehlo()
    sSDEC.starttls()
    sSDEC.ehlo()
    sSDEC.login(email_usrSDEC,email_pwdSDEC)
    sSDEC.sendmail(fromaddrSDEC,toaddrSDEC,msgSDEC.as_string())
    sSDEC.quit()
