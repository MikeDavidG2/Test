################################################################################
### blue2cosd.py
### Copy files maintained on Blue Workspace SDE to County Workspace SDE
### May 2017
################################################################################
import arcpy
import ConfigParser
import datetime
import ftplib
import math
import os
import re
import string
import sys
import time
import zipfile

stopTimeStr  = "05:00:00" # time of day (next day) to stop copying
root          = "D:\\sde_cosd_and_blue"
sdePath       = os.path.join(root,"connection","Connection to Workspace (sangis user).sde")
dataPath      = os.path.join(root,"data")
logPath       = os.path.join(root,"log")
configFile    = os.path.join(root,"connection","ftp.txt")
ftpFolder     = "ftp/LUEG/transfer_to_cosd"
sdePre        = "SDEP2.SANGIS."
manifestTable = "manifest_blue2cosd"
errorFile     = os.path.join(logPath,"ERROR_" + str(time.strftime("%Y%m%d", time.localtime())) + "_blue2cosd.txt")
errorFlag     = False
ignoreFields  = [
    "Shape",
    "SHAPE",
    "Shape_Area",
    "SHAPE_Area",
    "Shape.STArea()",
    "SHAPE.STArea()",
    "Shape_STArea__",
    "Shape_Length",
    "SHAPE_Length",
    "Shape.STLength()",
    "SHAPE.STLength()",
    "Shape_STLength__"]

old_output  = sys.stdout
logFileName = os.path.join(logPath,"blue2cosd" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt")
logFile     = open(logFileName,"w")
sys.stdout  = logFile

arcpy.env.workspace = dataPath

# Format stop time for processing
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
stopTime = datetime.datetime.strptime(str(tomorrow) + " " + str(stopTimeStr),"%Y-%m-%d %H:%M:%S")

# Download and delete all files from ftp
try:
    os.chdir(dataPath)
    print str(time.strftime("%H:%M:%S", time.localtime())),"| Connecting to ftp"
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    usr = config.get("sangis","usr")
    pwd = config.get("sangis","pwd")
    adr = config.get("sangis","adr")
    ftp = ftplib.FTP(adr)
    ftp.login(usr,pwd)
    ftp.cwd(ftpFolder)
    filenames = ftp.nlst()
    number_of_files = int(len(filenames))
    if number_of_files < 2:
        print "WARNING: No files on FTP site\n"
        sys.stdout = old_output
        logFile.close()
        sys.exit(0)
    else:
        for filename in filenames:
            fc  = filename.strip(".gdb.zip")
            gdb = filename.strip(".zip")
            print str(time.strftime("%H:%M:%S", time.localtime())),"| Downloading and unzipping",fc
            zipPath = os.path.join(dataPath,filename)
            # download
            with open(zipPath,'wb') as openFile:
                ftp.retrbinary('RETR '+ filename,openFile.write)
            # delete existing gdb
            if arcpy.Exists(gdb):
                arcpy.management.Delete(gdb)
            # unzip
            with zipfile.ZipFile(zipPath,"r") as z:
                z.extractall(dataPath)
            # delete zip file from ftp (except manifest file)
            if not filename == manifestTable + ".gdb.zip":
                ftp.delete(filename)
            # delete zip file from staging area
            if arcpy.Exists(zipPath):
                os.unlink(zipPath)
    ftp.quit()
except:
    errorFlag = True
    print "ERROR: Failed to download or unzip file from ftp site\n"
    print arcpy.GetMessages()
    print ""


# Go through each GDB
arcpy.env.workspace = dataPath
workspaces = arcpy.ListWorkspaces("","FileGDB")
for workspace in workspaces:
    timenow = datetime.datetime.now()
    deltaTime = stopTime - timenow
    deltaDays = int(deltaTime.days)
    if deltaDays >= 0:
        if not workspace == os.path.join(dataPath,manifestTable + ".gdb") and not workspace == os.path.join(dataPath,"cosd2blue.gdb"):
            try:
                arcpy.env.workspace = workspace
                fc = arcpy.ListFeatureClasses()[0] # there should only be 1 fc per gdb
                print "\n" + str(time.strftime("%H:%M:%S", time.localtime())),"| Processing",fc
                gdbFC = os.path.join(workspace,fc)
                
                # Get FDS from manifest table
                inManifest = False
                inSDE      = False
                with arcpy.da.SearchCursor(os.path.join(dataPath,manifestTable + ".gdb",manifestTable),["COUNTY_FDS","LAYER_NAME"],"LAYER_NAME = '" + fc + "'") as cur:
                    for row in cur:
                        inManifest = True
                        fds = row[0]
                    
                if inManifest:    
                    # Verify FC exists in County SDE
                    sdeFC = os.path.join(sdePath,sdePre + fds,sdePre + fc)
                    if arcpy.Exists(sdeFC):
                        inSDE = True
                    else:
                        print "ERROR:",fc,"does not exist in",fds,"in County Workspace\n"
                        errorFlag = True
                        inSDE = False
                else:
                    print "ERROR:",fc,"does not exist in manifest table\n"
                    errorFlag = True

                # Go through each field in SDE FC and make sure it exists in GDB FC
                if inSDE and inManifest:
                    gdbFieldsOrig = arcpy.ListFields(gdbFC)
                    gdbFields = []
                    sdeFieldsOrig = arcpy.ListFields(sdeFC)
                    sdeFields = []
                    for fld in gdbFieldsOrig:
                        if fld.name not in ignoreFields:
                            gdbFields.append(fld)
                    for fld in sdeFieldsOrig:
                        if fld.name not in ignoreFields:
                            sdeFields.append(fld)

                    # Make sure field types match
                    fieldError = False
                    for sdeField in sdeFields:
                        gdbFieldExists = False
                        for gdbField in gdbFields:
                            # Check field name
                            if gdbField.name == sdeField.name:
                                gdbFieldExists = True
                                # Check field type
                                if gdbField.type <> sdeField.type:
                                    fieldError = True
                                    errorFlag = True
                                    print "ERROR:",gdbField.name,"field type does not match sde\n"
                                # Check field length
                                if gdbField.type == "String" and gdbField.length > sdeField.length:
                                    fieldError = True
                                    errorFlag = True
                                    print "ERROR:",gdbField.name,"is too long for sde\n"
                        if not gdbFieldExists:
                            print "WARNING:",sdeField.name,"does not exist in gdb\n"

                    # Only update data if there are no field errors
                    if not fieldError:
                        # Backup existing data from SDE to gdb
                        if arcpy.Exists(os.path.join(sdePath,sdePre + fds,fc + "_BAK")):
                            arcpy.management.Delete(os.path.join(sdePath,sdePre + fds,sdePre + fc + "_BAK"))
                        print str(time.strftime("%H:%M:%S", time.localtime())),"|   Backing up",fc
                        arcpy.management.Copy(os.path.join(sdePath,sdePre + fds,sdePre + fc),os.path.join(sdePath,sdePre + fds,fc + "_BAK"))
                        arcpy.management.RegisterAsVersioned(os.path.join(sdePath,sdePre + fds),"NO_EDITS_TO_BASE")

                        
                        # Delete all records and append
                        sdeFC = os.path.join(sdePath,sdePre + fds,sdePre + fc)
                        arcpy.management.MakeFeatureLayer(sdeFC,"sde_lyr")
                        arcpy.management.DeleteRows("sde_lyr")
                        arcpy.management.Delete("sde_lyr")
                        
                        try:
                            print str(time.strftime("%H:%M:%S", time.localtime())),"|   Updating",fc,"in SDE"
                            arcpy.management.MakeFeatureLayer(gdbFC,"gdb")
                            arcpy.management.MakeFeatureLayer(sdeFC,"sde")
                            arcpy.management.Append("gdb","sde","NO_TEST")
                            arcpy.management.Delete("gdb")
                            arcpy.management.Delete("sde")
                        except:
                            print "ERROR appending",fc,"to SDE\n"
                            errorFlag = True
                # Delete old gdb
                if not errorFlag and not fieldError:
                    print str(time.strftime("%H:%M:%S", time.localtime())),"|   Deleting",fc + ".gdb"
                    arcpy.env.workspace = dataPath
                    arcpy.management.Delete(os.path.join(dataPath,fc + ".gdb"))
                else:
                    errorFlag = True
                    print "ERROR: Problem with",fc + ";",os.path.join(dataPath,fc + ".gdb"),"was not deleted\n"
                
            except:
                errorFlag = True
                print "ERROR with",fc,"\n"
                print arcpy.GetMessages()
    
    
sys.stdout = old_output
logFile.close()

if errorFlag:
    # email message
    eFile = open(errorFile,"w")
    eFile.close()
sys.exit()
