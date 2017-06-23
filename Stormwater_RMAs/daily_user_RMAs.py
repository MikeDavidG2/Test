##############################################
###           daily_user_RMAs.py           ###
###  Python script to report daily values  ###
###     from user tracks (user and RMA)    ###
###  Karen Chadwick           August 2015  ###
###  *** ASSUMES START AFTER MIDNIGHT ***  ###
##############################################

### Import modules
import arcpy
import ConfigParser
import datetime
import json
import math
import mimetypes
import os
#import requests
import smtplib
import string
import sys
import time
import urllib
import urllib2 

from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.text import MIMEText


old_outputRMA = sys.stdout
timestart = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
stimes = time.time()

### Set some variables
trackURL    = "http://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/Track_line/FeatureServer/0/query"
wkgFolder   = "D:\\Projects\\stormwater\\scripts\\data"
wkgGDB      = "RMAuserWKG.gdb"
wkgPath     = wkgFolder + "\\" + wkgGDB
indataFC    = "Track_line"
outTrackFC  = "outUserTracksRMA"
rmaZones    = "D:\\Projects\\stormwater\\data_ago\\agol_stormdata.gdb\\RMA_HSA_JUR1"
gtURL       = "https://www.arcgis.com/sharing/rest/generateToken"
dsslvFields = ["NAME","DATE","EDITOR","EDITDATE"]
AGOfields   = "NAME,DATE,GlobalID,EDITOR,EDITDATE"

logFileNameRMA = str(wkgFolder) + "\\..\\log\\dailyUserRMAs_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt"
logFileRMA = open(logFileNameRMA,"w")
sys.stdout = logFileRMA

distcutoff  = 5280  ###  cutoff distance (FEET)
cfgFile     = "D:\\sde_maintenance\\scripts\\configFiles\\accounts.txt"
stmwtrPeeps = ["alex.romo@sdcounty.ca.gov","randy.yakos@sdcounty.ca.gov","gary.ross@sdcounty.ca.gov"]
scriptAdmin = ["randy.yakos@sdcounty.ca.gov","gary.ross@sdcounty.ca.gov"]
fromEmail   = "dplugis@gmail.com"

### START processing
arcpy.env.overwriteOutput = True
arcpy.env.workspace = wkgFolder
errorSTATUS = 0

print "************************* DAILY_USER_RMAS.PY *************************"

### Preliminary setup
try:
    # Get dates and report name
    # Assumes start time *AFTER* midnight
    today = datetime.date.today()
    todaystr = str(today)
    print "todaystr = " + todaystr
    de = today + datetime.timedelta(days=-1) ## To show the right day for the report name 
    dateend = str(de)
    print "dateend = " + dateend
    ds = today + datetime.timedelta(days=-7)
    datestart = str(ds)
    print "datestart = " + datestart
    # Dates are in UTC, converted to view in PST --> adjust for PST (8 hours)
    dec = datetime.datetime(de.year,de.month,de.day)
    dateendconv = str(dec + datetime.timedelta(days=1,hours=8)) ## To search for the correct date range
    dsc = datetime.datetime(ds.year,ds.month,ds.day)
    datestartconv = str(dsc + datetime.timedelta(hours=8))
    rptName = "RMA_daily_user_report_" + str(dateend) + ".csv"
    rptPath = wkgFolder + "\\" + rptName
    print rptPath
    # Create a working GDB
    if arcpy.Exists(wkgPath):
        print "Deleting existing instance of working GDB..."
        arcpy.Delete_management(wkgPath)
        print "   Successfully deleted working GDB."
    arcpy.CreateFileGDB_management(wkgFolder,wkgGDB)
    print "   Successfully created working GDB."
    arcpy.env.workspace = wkgPath
except:
    errorSTATUS = 1
    print "********* ERROR during preliminary setup... *********"
    
### Get AGOL token
try:
    if errorSTATUS == 0:
        print "Getting token..."
        configRMA = ConfigParser.ConfigParser()
        configRMA.read(cfgFile)
        usr = configRMA.get("AGOL","usr")
        pwd = configRMA.get("AGOL","pwd")
        gtValues = {'username' : usr, 'password' : pwd, 'referer' : 'http://www.arcgis.com', 'f' : 'json' }
        gtData = urllib.urlencode(gtValues)
        gtRequest = urllib2.Request(gtURL,gtData)
        gtResponse = urllib2.urlopen(gtRequest)
        gtJson = json.load(gtResponse)
        token = gtJson['token']
        print "   Successfully retrieved token."
except:
    errorSTATUS = 1
    print "********* ERROR while generating token... *********"

### Copy the track data
try:
#############################################################################################################
### http://blogs.esri.com/esri/arcgis/2013/10/10/quick-tips-consuming-feature-services-with-geoprocessing/
### https://geonet.esri.com/thread/118781
### WARNING: Script currently only pulls up to the first 10,000 (1,000?) records - more records will require
###     a loop for iteration - see, e.g., "Max Records" section at the first (blogs) URL listed above or for
###     example code see the second (geonet) URL listed above
#############################################################################################################
    if errorSTATUS == 0:
        print "Getting data..."
        where = "1=1"
        query = "?where={}&outFields={}&returnGeometry=true&f=json&token={}".format(where,AGOfields,token)
        print "10"
        fsURL = trackURL + query
        print "20"
        fs = arcpy.FeatureSet()
        print "30"
        print str(fsURL)
        print "32"
        fs.load(fsURL)
        print "40"
        arcpy.CreateFileGDB_management(wkgFolder,wkgGDB) #E:\\Projects\\stormwater\\scripts\\data\\RMAuserWKG.gdb
        print "50"
        arcpy.CopyFeatures_management(fs,wkgPath + "\\" + indataFC)
        print "   Successfully retrieved data."
except:
    errorSTATUS = 1
    print "********* ERROR while copying data... *********"

### Process the data
try:
    if errorSTATUS == 0:
        # Select the tracks within the date range
        print "Selecting tracks..."
        selectClause = '"DATE" >= date ' + "'" + str(datestartconv) + "' AND " + '"DATE" <= date ' + "'" + str(dateendconv) + "'"
        print "   " + selectClause
        arcpy.MakeFeatureLayer_management(indataFC,"trackLyr",selectClause)
        numfeats = arcpy.GetCount_management("trackLyr")
        count = int(numfeats.getOutput(0))
        if count == 0:
            errorSTATUS = 99
        else:
            # Split the lines and discard segments that are too long
            arcpy.SplitLine_management("trackLyr","tempTESTtrackSPLIT")
            selectClause = '"Shape_Length" < ' + str(distcutoff)
            arcpy.MakeFeatureLayer_management("tempTESTtrackSPLIT","tempTESTtrackSPLIT_lyr",selectClause)
            numfeats = arcpy.GetCount_management("tempTESTtrackSPLIT_lyr")
            count = int(numfeats.getOutput(0))
            if count == 0:
                errorSTATUS = 99
            else:
                arcpy.CopyFeatures_management("tempTESTtrackSPLIT_lyr","tempTESTtrackSPLITrefine")
                arcpy.Dissolve_management("tempTESTtrackSPLITrefine","trackTEMP",dsslvFields,"","MULTI_PART","UNSPLIT_LINES")
                # Compare to RMAs
                print "Intersecting data..."
                arcpy.Intersect_analysis(["trackTEMP",rmaZones],"rmaTrack")
                numfeats = arcpy.GetCount_management("rmaTrack")
                count = int(numfeats.getOutput(0))
                if count == 0:
                    errorSTATUS = 99
                else:
                    # Add fields for information
                    arcpy.AddField_management("rmaTrack","COLLECTDATE","TEXT","","",12)
                    arcpy.MakeTableView_management("rmaTrack","rmaTrackView")
                    with arcpy.da.UpdateCursor("rmaTrackView",["DATE","COLLECTDATE"]) as rowcursor:
                        for row in rowcursor:
                            datetimeVal = row[0]
                            dateVal = datetime.datetime.strftime(datetimeVal,"%m/%d/%Y")
                            row[1] = dateVal
                            rowcursor.updateRow(row)
                        del rowcursor, row
                    arcpy.AddField_management("rmaTrack","INFOSTR","TEXT","","",300)
                    arcpy.CalculateField_management("rmaTrack","INFOSTR",'[NAME] & "__" & [COLLECTDATE] & "__" & [HUNAME] & "/" & [HANAME] & "/" & [HSANAME] & "/" & [HBNUM]')
                    # Get data summaries
                    print "Running frequencies..."
                    arcpy.MakeFeatureLayer_management("rmaTrack","rmaTrackLyr","\"HBNUM\" <> 0")
                    arcpy.Frequency_analysis("rmaTrackLyr","sumTracks",["INFOSTR"])
                    # Write report file
                    with arcpy.da.SearchCursor("sumTracks",["INFOSTR"]) as rowcursor:
                        tracklist = list(rowcursor)
                    del rowcursor
                    print "Writing report..."
                    with open(rptPath,"w") as csvf:
                        csvf.write("NAME,DATE,RMA,HUNAME,HANAME,HBNUM\n")
                        for track in tracklist:
                            usrinfo = str(track[0]).split("__")
                            rmainfo = str(usrinfo[2]).split("/")
                            if "SAME AS HANAME" in str(rmainfo[2]):
                                rmastr = str(rmainfo[1])
                            else:
                                rmastr = str(rmainfo[2])
                            csvf.write(str(usrinfo[0]) + "," + str(usrinfo[1]) + "," + rmastr + "," + str(rmainfo[0]) + "," + \
                                       str(rmainfo[1]) + "," + str(rmainfo[3]) + "\n")
except:
    errorSTATUS = 1
    print "********* ERROR while processing... *********"

### Email the results
try:
    if errorSTATUS == 0:  ## No errors
        print "Emailing report..."
        # Set email parameters
        configRMA = ConfigParser.ConfigParser()
        configRMA.read(cfgFile)
        emailusrRMA = configRMA.get("email","usr")
        emailpwdRMA = configRMA.get("email","pwd")
        msgString = "Daily stormwater user/RMA report " + todaystr
        msgRMA = MIMEMultipart()
        fromaddrRMA        = fromEmail
        toaddrRMA          = stmwtrPeeps  ## <-- Stormwater personnel
        msgRMA['Subject']  = msgString
        msgRMA['From']     = "Python Script"
        msgRMA['To']       = "Stormwater personnel"
        msgRMA.preamble    = msgString
        # Format email content
        ctype, encoding = mimetypes.guess_type(rptPath)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open (rptPath) as fpRMA:
            attachmentRMA = MIMEText(fpRMA.read(), _subtype=subtype)        
        attachmentRMA.add_header("Content-Disposition","attachment",filename=rptPath)
        msgRMA.attach(attachmentRMA)
        # Send the email
        sRMA = smtplib.SMTP('smtp.gmail.com',587)
        sRMA.starttls()
        sRMA.login(emailusrRMA,emailpwdRMA)
        sRMA.sendmail(fromaddrRMA,toaddrRMA,msgRMA.as_string())
        sRMA.quit()
        print "   Successfully emailed report."
        sys.stdout = old_outputRMA
        logFileRMA.close()
    elif errorSTATUS == 99:  ## No data for time period
        print "Emailing no data message..."
        # Set email parameters
        configRMA = ConfigParser.ConfigParser()
        configRMA.read(cfgFile)
        emailusrRMA = configRMA.get("email","usr")
        emailpwdRMA = configRMA.get("email","pwd")
        msgString = "Daily stormwater user/RMA report--no data found for period " + datestart + " to " + dateend
        msgRMA = MIMEText(msgString)
        fromaddrRMA         = fromEmail
        toaddrRMA           = stmwtrPeeps  
        msgRMA['Subject']   = msgString
        msgRMA['From']      = "Python Script"
        msgRMA['To']        = "Stormwater personnel"
        # Send the email
        sRMA = smtplib.SMTP('smtp.gmail.com',587)
        sRMA.starttls()
        sRMA.login(emailusrRMA,emailpwdRMA)
        sRMA.sendmail(fromaddrRMA,toaddrRMA,msgRMA.as_string())
        sRMA.quit()
        print "   Successfully emailed no data message."
        sys.stdout = old_outputRMA
        logFileRMA.close()
    else:  ## Errors were generated
        print "\nAN ERROR HAS OCCURRED!\n"
        print arcpy.GetMessages()
        sys.stdout = old_outputRMA
        logFileRMA.close()
        # Set email parameters
        configRMA = ConfigParser.ConfigParser()
        configRMA.read(cfgFile)
        emailusrRMA = configRMA.get("email","usr")
        emailpwdRMA = configRMA.get("email","pwd")
        with open(logFileNameRMA,"rb") as fpRMA:
            msgRMA = MIMEText(fpRMA.read())
        fromaddrRMA         = fromEmail
        toaddrRMA           = scriptAdmin  ## <-- LUEG-GIS script administrator
        msgRMA['Subject']   = "ERROR with DAILY STORMWATER USER/RMA REPORT"
        msgRMA['From']      = "Python Script"
        msgRMA['To']        = "LUEG-GIS script administrator"
        # Send the email
        sRMA = smtplib.SMTP('smtp.gmail.com',587)
        sRMA.starttls()
        sRMA.login(emailusrRMA,emailpwdRMA)
        sRMA.sendmail(fromaddrRMA,toaddrRMA,msgRMA.as_string())
        sRMA.quit()
        print "   Emailed log file."
except:
    errorSTATUS = 1
    print "********* ERROR while emailing... *********"
    
        
##### END processing - do clerical messaging
timeend = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
etimee = time.time()
# Calculate time duration
timeElapsed = etimee - stimes
dhours = int(math.floor(timeElapsed/3600))
if dhours < 10: strdhours = "0" + str(dhours)
else: strdhours = str(dhours)
deltam = timeElapsed - (dhours*3600)
dminutes = int(math.floor(deltam/60))
if dminutes < 10: strdminutes = "0" + str(dminutes)
else: strdminutes = str(dminutes)
deltas = deltam - (dminutes*60)
dseconds = int(round(deltas))
if dseconds < 10: strdseconds = "0" + str(dseconds)
else: strdseconds = str(dseconds)
print "\n***************************************************************************"
print "Process started at " + str(timestart)
print "      and ended at " + str(timeend)
print "   Duration = " + strdhours + ":" + strdminutes + ":" + strdseconds + " hours"
print "***************************************************************************"

