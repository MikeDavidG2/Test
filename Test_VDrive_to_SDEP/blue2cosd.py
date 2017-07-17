
"""
NOTE: For the purposes of this script a 'Dataset' can be any type of data
(Feature Class, Table, etc.).  A Feature Dataset (FDS) is the specific object in
ArcCatalog that can contain Feature Classes of all the same Projection.
"""

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
root          = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_root'  # MG 07/17/17: Set variable to DEV settings.  TODO: Delete after testing
sdePath       = os.path.join(root,"connection","Connection to Workspace (sangis user).sde")
sdePath       = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_root\connection\FALSE_SDEP2.gdb'  # MG 07/17/17: Set variable to DEV settings.  TODO: Delete after testing
dataPath      = os.path.join(root,"data")
logPath       = os.path.join(root,"log")
configFile    = os.path.join(root,"connection","ftp.txt")
ftpFolder     = "ftp/LUEG/transfer_to_cosd"
ftpFolder     = r'U:\grue\Projects\VDrive_to_SDEP_flow\FALSE_FTP_folder'  # MG 07/17/17: Set variable to DEV settings.  TODO: Delete after testing
sdePre        = "SDEP2.SANGIS."
sdePre        = ''  # MG 07/17/17: Set variable to DEV settings.  TODO: Delete after testing
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
##sys.stdout  = logFile   # MG 07/17/17: Set variable to DEV settings.  TODO: Uncomment out after testing and delete this comment.

arcpy.env.workspace = dataPath

# Format stop time for processing
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
stopTime = datetime.datetime.strptime(str(tomorrow) + " " + str(stopTimeStr),"%Y-%m-%d %H:%M:%S")

# MG 7/17/17:  No need to test this section of the script, FC's and Tables are downloaded and unzipped the exact same way.
### Download and delete all files from ftp
##try:
##    os.chdir(dataPath)
##    print str(time.strftime("%H:%M:%S", time.localtime())),"| Connecting to ftp"
##    config = ConfigParser.ConfigParser()
##    config.read(configFile)
##    usr = config.get("sangis","usr")
##    pwd = config.get("sangis","pwd")
##    adr = config.get("sangis","adr")
##    ftp = ftplib.FTP(adr)
##    ftp.login(usr,pwd)
##    ftp.cwd(ftpFolder)
##    filenames = ftp.nlst()
##    number_of_files = int(len(filenames))
##    if number_of_files < 2:
##        print "WARNING: No files on FTP site\n"
##        sys.stdout = old_output
##        logFile.close()
##        sys.exit(0)
##    else:
##        for filename in filenames:
##            fc  = filename.strip(".gdb.zip")
##            gdb = filename.strip(".zip")
##            print str(time.strftime("%H:%M:%S", time.localtime())),"| Downloading and unzipping",fc
##            zipPath = os.path.join(dataPath,filename)
##            # download
##            with open(zipPath,'wb') as openFile:
##                ftp.retrbinary('RETR '+ filename,openFile.write)
##            # delete existing gdb
##            if arcpy.Exists(gdb):
##                arcpy.management.Delete(gdb)
##            # unzip
##            with zipfile.ZipFile(zipPath,"r") as z:
##                z.extractall(dataPath)
##            # delete zip file from ftp (except manifest file)
##            if not filename == manifestTable + ".gdb.zip":
##                ftp.delete(filename)
##            # delete zip file from staging area
##            if arcpy.Exists(zipPath):
##                os.unlink(zipPath)
##    ftp.quit()
##except:
##    errorFlag = True
##    print "ERROR: Failed to download or unzip file from ftp site\n"
##    print arcpy.GetMessages()
##    print ""
##

# Go through each FGDB
arcpy.env.workspace = dataPath
workspaces = arcpy.ListWorkspaces("","FileGDB")

for workspace in workspaces:
    print '\n------------------------------------------------------------------'
    print '{}  |  Processing workspace: "{}"'.format(str(time.strftime("%H:%M:%S", time.localtime())), workspace)

    timenow = datetime.datetime.now()
    deltaTime = stopTime - timenow
    deltaDays = int(deltaTime.days)
    if deltaDays >= 0:
        manifest_FDGB = os.path.join(dataPath,manifestTable + ".gdb")

        if workspace == manifest_FDGB:
            print '  Not processing the manifest table'

        if not workspace == manifest_FDGB and not workspace == os.path.join(dataPath,"cosd2blue.gdb"):
            # Load the Dataset in the FGDB to the SDE
            try:
                arcpy.env.workspace = workspace

                # The FC's name should be the same as the FGDB's name
                #   and there should only be one
                fc = (os.path.basename(workspace)).split('.')[0]

                gdbFC = os.path.join(workspace, fc)

                # Get the dataset type to decide how to handle the dataset
                #   (i.e. as a Feature Class or as a Table)
                desc = arcpy.Describe(gdbFC)
                dataset_type = desc.datasetType

                print "Processing '{}' as a '{}':".format(fc, dataset_type)

                # Get FDS from manifest table
                inManifest = False
                inSDE      = False
                manifest_path = os.path.join(manifest_FDGB, manifestTable)
                where_clause = "LAYER_NAME = '" + fc + "'"
                with arcpy.da.SearchCursor(manifest_path, ["COUNTY_FDS","LAYER_NAME"], where_clause) as cursor:
                    for row in cursor:
                        inManifest = True
                        fds = row[0]
                        print '  "{}" is in Manifest = "{}".  County FDS = "{}"'.format(fc, inManifest, fds)

                if inManifest:
                    # Set path to 'sdeFDS' and 'sdeFC' depending on 'dataset_type'
                    if dataset_type == 'FeatureClass':
                        sdeFDS = os.path.join(sdePath,sdePre + fds)
                        sdeFC = os.path.join(sdeFDS,sdePre + fc)
                    if dataset_type == 'Table':
                        sdeFDS = os.path.join(sdePath,sdePre)  # No fds for a Table
                        sdeFC = os.path.join(sdeFDS,sdePre + fc)

                    # Verify FC exists in County SDE
                    print '  Verifying "{}" exists in County SDE at "{}":'.format(fc, sdeFC)
                    if arcpy.Exists(sdeFC):
                        inSDE = True
                        print '    "Dataset Exists"'
                    else:
                        print "*** ERROR: '{}' does not exist in '{}' in County Workspace ***".format(fc, fds)
                        errorFlag = True
                        inSDE = False

                else:
                    print "*** ERROR: '{}' does not exist in manifest table".format(fc)
                    errorFlag = True

                # Go through each field in SDE Dataset and make sure it exists in GDB Dataset
                if inSDE and inManifest:
                    print '  Analyzing Fields for schema mismatch between SDE Dataset and FGDB Dataset:'

                    # Get list of FGDB fields for this Dataset
                    gdbFieldsOrig = arcpy.ListFields(gdbFC)
                    gdbFields = []
                    for fld in gdbFieldsOrig:
                        if fld.name not in ignoreFields:
                            gdbFields.append(fld)
                    # Get list of SDE fields for this Dataset
                    sdeFieldsOrig = arcpy.ListFields(sdeFC)
                    sdeFields = []
                    for fld in sdeFieldsOrig:
                        if fld.name not in ignoreFields:
                            sdeFields.append(fld)

                    # Using lists from above, make sure field types match
                    fieldError = False
                    for sdeField in sdeFields:
                        gdbFieldExists = False
                        for gdbField in gdbFields:
                            # Check field name exists
                            if gdbField.name == sdeField.name:
                                gdbFieldExists = True
                                # Check field type
                                if gdbField.type <> sdeField.type:
                                    fieldError = True
                                    errorFlag  = True
                                    print '*** ERROR: Field "{}" does not have the same field type in FGDB and SDE  ***'.format(gdbField.name)
                                # Check field length
                                if gdbField.type == "String" and gdbField.length > sdeField.length:
                                    fieldError = True
                                    errorFlag  = True
                                    print '*** ERROR: Field "{}" is too long in FGDB for SDE ***'.format(gdbField.name)
                        if not gdbFieldExists:
                            fieldError = True  # MG 07/17/17:  I added this to prevent SDE from being updated by FGDB dataset with missing field(s)  TODO: Confirm with Gary this is OK and delete this comment if OK.
                            errorFlag  = True  # MG 07/17/17:  I added this to prevent SDE from being updated by FGDB dataset with missing field(s)  TODO: Confirm with Gary this is OK and delete this comment if OK.
                            print '*** ERROR: Field "{}" does not exist in FGDB ***'.format(sdeField.name)

                    if fieldError:
                        print '  New Dataset from FGDB not copied over to SDE, please fix above errors.'

                    # Only update data if there are no field errors
                    if not fieldError:
                        print '    "No field errors detected"'

                        # Set 'backup_path' depending on 'dataset_type'
                        if dataset_type == 'FeatureClass':
                            backup_path = os.path.join(sdePath,sdePre + fds,sdePre + fc + "_BAK")

                        if dataset_type == 'Table':
                            backup_path = os.path.join(sdePath,sdePre + fc + "_BAK")

                        # Delete existing backup if it exists
                        if arcpy.Exists(backup_path):
                            print '  Deleting old backup at "{}"'.format(backup_path)
                            arcpy.management.Delete(backup_path)

                        # Backup existing data in SDE
                        print '  Backing up "{}"\n    From: "{}"\n      To: "{}"'.format(fc, sdeFC, backup_path)
                        arcpy.management.Copy(sdeFC, backup_path)

                        # Register Feature Dataset As Versioned
                        print '  Registering as versioned FDS "{}"'.format(sdeFDS)
##                        arcpy.management.RegisterAsVersioned(sdeFDS,"NO_EDITS_TO_BASE")  # MG 07/17/17: Set variable to DEV settings.  TODO: Uncomment out after testing

                        # MG 07/17/17 TODO: Why is there no setting permissions step on this script?

                        # Delete all records in Dataset
                        print '  Deleting rows in SDE at "{}"'.format(sdeFC)
                        arcpy.DeleteRows_management(sdeFC)

                        # Append data from FGDB to SDE
                        try:
                            print '  Appending data:\n    From: "{}"\n      To: "{}"'.format(gdbFC, sdeFC)
                            arcpy.Append_management(gdbFC, sdeFC, 'TEST')

                        except:
                            errorFlag = True
                            print '*** ERROR Appending data to "{}"'.format(fc)

                # Delete FGDB's used to update SDE
                if not errorFlag and not fieldError:  # If no errors, delete FGDB
                    try:
                        print '  Deleting FGDB used to update SDE "{}"'.format(workspace)
##                        arcpy.management.Delete(workspace)  # MG 07/17/17: Set variable to DEV settings.  TODO: Uncomment out after testing
                    except:
                        errorFlag = True
                        print '*** ERROR: Problem with deleting FGDB used to update SDE ***'

            except Exception as e:
                errorFlag = True
                print '*** ERROR with processing FC ***'
                print str(e)
                print arcpy.GetMessages()

if errorFlag == True:
    print '\n\n*** ERRORS in script, please see above for specifics.  ***'
else:
    print '\n\nSUCCESSFUL run of script.'

sys.stdout = old_output
logFile.close()

if errorFlag:
    # email message
    eFile = open(errorFile,"w")
    eFile.close()
sys.exit()
