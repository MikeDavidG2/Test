#########################################################
###                   report_RMAs.py                  ###
###  Python script to report values from user tracks  ###
###    (e.g., RMA, distance and number of parcels)    ###
###  Karen Chadwick                      August 2015  ###
#########################################################

# Import modules
import sys, string, os, time, datetime, math, ConfigParser, json, urllib, urllib2, smtplib, mimetypes
import arcpy as gpRMA
from dateutil.relativedelta import relativedelta

#import requests
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.text import MIMEText

timestart = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
stimes = time.time()

#######################################################################################
#######################################################################################
###  Set any changeable variables between here ---------------------------------->  ###

# MG 6/23/17: Added manually_entered_dates so users can make script auto generate
# the dates.
# or the user can enter their own dates below.
# 'True' when you want to manually enter 'datestart' and 'dateend'
# 'False' when the script should auto calculate 'datestart' and 'dateend':
#    datestart = last month's 1st day of the month
#    dateend   = last month's last day of the month
manually_entered_dates = False

#-------------------------------------------------------------------------------
if (manually_entered_dates == True):
    #######################################################################
    ####### Note: dates are *INCLUSIVE* --> for a report covering Sep, Oct,
    ### Nov of 2015, use: datestart = "2015-09-01" dateend = "2015-11-30"
    datestart   = "2017-06-01"  ## Date should be in format yyyy-mm-dd"
    dateend     = "2017-06-30"  ## Date should be in format yyyy-mm-dd"
    ####### --> the start and end dates will be included in the report
    #######################################################################
#-------------------------------------------------------------------------------

roadbuffer  = 40    ###  <-- Change the road buffer distance (number of FEET) here!
distcutoff  = 5280  ###  <-- Change the cutoff distance (number of FEET) here!
##cfgFile     = r"D:\sde_maintenance\scripts\configFiles\accounts.txt"
##stmwtrPeeps = ["alex.romo@sdcounty.ca.gov","randy.yakos@sdcounty.ca.gov","gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
##scriptAdmin = ["randy.yakos@sdcounty.ca.gov","gary.ross@sdcounty.ca.gov", 'michael.grue@sdcounty.ca.gov']
# TODO: Before going to PROD, delete below 3 variables and and uncomment out 3 above
cfgFile     = r"M:\scripts\configFiles\accounts.txt"
stmwtrPeeps = ["michael.grue@sdcounty.ca.gov"]
scriptAdmin = ['michael.grue@sdcounty.ca.gov']

fromEmail   = "dplugis@gmail.com"
###  <-------------------------------------------------------------------  and here ###
#######################################################################################
#######################################################################################

# Set variables that shouldn't change much
todaystr    = str(time.strftime("%Y%m%d", time.localtime()))
trackURL    = "http://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/Track_line/FeatureServer/0/query"
wkgFolder   = r'D:\Projects\stormwater\scripts\data'
# TODO: Before going to PROD, delete below 1 variable and and uncomment out 1 above
wkgFolder   = r'P:\stormwater\scripts\data'
wkgGDB      = "RMAsummaryWKG.gdb"
wkgPath     = wkgFolder + "\\" + wkgGDB
indataFC    = "Track_line"
outTrackFC  = "outTracksRMA"
rmaZones    = "D:\\Projects\\stormwater\\data_ago\\agol_stormdata.gdb\\RMA_HSA_JUR1"
warehouse   = "D:\\sde_maintenance\\scripts\\Database Connections\\Atlantic Warehouse (sangis user).sde\\"
# TODO: Before going to PROD, delete below 2 variables and and uncomment out 2 above
rmaZones    = "P:\\stormwater\\data_ago\\agol_stormdata.gdb\\RMA_HSA_JUR1"
warehouse   = "M:\\scripts\\Database Connections\\Atlantic Warehouse (sangis user).sde\\"

cities      = warehouse + "SDE.SANGIS.JUR_MUNICIPAL"
parcels     = warehouse + "SDE.SANGIS.PARCELS_ALL"
cmroads     = warehouse + "SDE.SANGIS.ROAD_SEGMENTS"
gtURL       = "https://www.arcgis.com/sharing/rest/generateToken"
dsslvFields = ["NAME","DATE","EDITOR","EDITDATE"]
AGOfields   = "NAME,DATE,GlobalID,EDITOR,EDITDATE"

#-------------------------------------------------------------------------------
#MG 7/03/17: Added below to auto calculate dates
# If manually_entered_dates == False, get the datestart and dateend
if (manually_entered_dates == False):

    # Get datestart
    today = datetime.date.today()                   # Get today as a datetime object
    last_month = today + relativedelta(months=-1)   # Subtract one month from the current month
    last_month_1st = last_month.replace(day=1)      # Change the day to the 1st of the previous month
    datestart = last_month_1st.strftime('%Y-%m-%d') # datestart is last months 1st of the month
    print 'Date Start: ' + datestart

    # Get dateend
    one_day             = datetime.timedelta(days=1) # Create a timedelta of 1 day
    this_month_1st      = today.replace(day=1)       # Set the date to the 1st of the current month
    last_month_last_day = this_month_1st - one_day   # Subtract 1 day from 1st of the current month
    dateend             = last_month_last_day.strftime('%Y-%m-%d') # dateend is last day of last month
    print 'Date End: ' + dateend
#-------------------------------------------------------------------------------

# Make print statements write to a log file
logFileNameRMA = str(wkgFolder) + "\\..\\log\\reportRMAs_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt"
logFileRMA = open(logFileNameRMA,"w")
old_outputRMA = sys.stdout
sys.stdout = logFileRMA

# START processing
gpRMA.env.overwriteOutput = True
gpRMA.env.workspace = wkgFolder
errorSTATUS = 0

print "************************* REPORT_RMAS.PY *************************"

# Preliminary setup
try:
    # Get dates and report name
    print 'Start and end dates manually entered = ' + str(manually_entered_dates)
    if (manually_entered_dates == False):
        print '  The Script auto calculated the below dates.'
        print '  To set dates manually, change manually_entered_dates to "True".'
    print "    Start date = " + str(datestart)
    datestartstr = datestart.replace("-","")
    dsvals = datestart.split("-")
    ds = datetime.datetime(int(dsvals[0]),int(dsvals[1]),int(dsvals[2]))
    print "    End date = " + str(dateend)
    dateendstr = dateend.replace("-","")
    devals = dateend.split("-")
    de = datetime.datetime(int(devals[0]),int(devals[1]),int(devals[2]))
    # Dates are in UTC, converted to view in PST --> adjust for PST (8 hours)
    datestartconv = str(ds + datetime.timedelta(hours=8))
    dateendconv = str(de + datetime.timedelta(days=1,hours=8)) ## Dates are inclusive --> add 1 day to include the end date
    # Create a working GDB
    if gpRMA.Exists(wkgPath):
        print "Deleting existing instance of working GDB..."
        gpRMA.Delete_management(wkgPath)
        print "   Successfully deleted working GDB."
    gpRMA.CreateFileGDB_management(wkgFolder,wkgGDB)
    print "   Successfully created working GDB."
    gpRMA.env.workspace = wkgPath
    # Set report name/path
    rptName = "RMA_report_" + datestartstr + "_" + dateendstr + ".csv"
    rptPath = wkgFolder + "\\" + rptName
    print "Report = " + rptPath
    gpRMA.env.workspace = wkgPath
except Exception as e:
    errorSTATUS = 1
    print "********* ERROR during preliminary setup... *********"
    print '  ' + str(e)

# Get AGOL token
try:
    if errorSTATUS == 0:
        print "Getting token..."
        configRMA = ConfigParser.ConfigParser()
        configRMA.read(cfgFile) #KC 10/14/2015 Edited to use cfgFile
        usr = configRMA.get("AGOL","usr") #KC 10/14/2015 Edited to use cfgFile
        pwd = configRMA.get("AGOL","pwd") #KC 10/14/2015 Edited to use cfgFile
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

# Copy the track data
try:
#############################################################################################################
### http://blogs.esri.com/esri/arcgis/2013/10/10/quick-tips-consuming-feature-services-with-geoprocessing/
### https://geonet.esri.com/thread/118781
#############################################################################################################
    if errorSTATUS == 0:
        print "Getting data..."
        #-----------------------------------------------------------------------
        # MG 6/26/17: Changed the 'where' clause to have a date component so that
        #  we don't have to worry about bumping up to the 2000 record limit.

        # The format for the where query is "DATE BETWEEN 'First Date' and
        # 'Second Date'".  The data collected on the first date will be retrieved,
        # while the data collected on the second date will NOT be retrieved.
        # In other words: the first date is inclusive, the second date is exclusive
        # For ex: If data is collected on the 28th, and 29th and the where clause is:
        #   BETWEEN the 28th and 29th. You will get the data collected on the 28th only
        #   BETWEEN the 29th and 30th. You will get the data collected on the 29th only
        #   BETWEEN the 28th and 30th. You will get the data collected on the 28th AND 29th

        # The time manipulation below does NOT affect the selection
        # process that happens in the 'Process the data' step.
        # We want to set the 'where' clause to get records where the [DATE]
        # field is BETWEEN the 'datestart' and 'dateend + two days'.
        # By adding 2 days into the future we ensure that we are grabbing all of
        # the data from AGOL that we may need to process, while ENSURING that we
        # do not try to grab more than 2000 records (which is the limit of this
        # feature service)
        two_days = datetime.timedelta(days=2)
        dateend_td_obj = datetime.datetime.strptime(dateend, '%Y-%m-%d')
        dateend_2_days = dateend_td_obj + two_days
        dateend_2_days_str = dateend_2_days.strftime('%Y-%m-%d')

        # Set where to between 'datestart' and 'dateend + 2 days'
        where = "DATE BETWEEN '{}' and '{}'".format(datestart, dateend_2_days_str)
        ##where = "1=1" # Grabs the whole database (up to 2000 records)
        print 'Where clause used to query Feature Service: \n  '+ where

        # Encode the where statement so it is readable by URL protocol (ie %27 = ' in URL
        # visit http://meyerweb.com/eric/tools/dencoder to test URL encoding
        where_encoded = urllib.quote(where)

        query = "?where={}&outFields={}&returnGeometry=true&f=json&token={}".format(where_encoded,AGOfields,token)
        #-----------------------------------------------------------------------
        fsURL = trackURL + query
        print str(fsURL)
        fs = gpRMA.FeatureSet()
        print "10"
        fs.load(fsURL)
        print "20"
        gpRMA.CreateFileGDB_management(wkgFolder,wkgGDB)
        print "30"
        gpRMA.CopyFeatures_management(fs,wkgPath + "\\" + indataFC)
        print "   Successfully retrieved data."
except:
    errorSTATUS = 1
    print "********* ERROR while copying data... *********"

# Process the data
try:
    if errorSTATUS == 0:
        # Select the tracks within the date range
        print "Selecting tracks..."
        selectClause = '"DATE" >= date ' + "'" + str(datestartconv) + "' AND " + '"DATE" <= date ' + "'" + str(dateendconv) + "'"
        print "   " + selectClause
        gpRMA.MakeFeatureLayer_management(indataFC,"trackLyr",selectClause)
        numfeats = gpRMA.GetCount_management("trackLyr")
        count = int(numfeats.getOutput(0))
        if count == 0:
            errorSTATUS = 99
        else:
            # Split the lines and discard segments that are too long
            gpRMA.SplitLine_management("trackLyr","tempTESTtrackSPLIT")
            selectClause = '"Shape_Length" < ' + str(distcutoff)
            gpRMA.MakeFeatureLayer_management("tempTESTtrackSPLIT","tempTESTtrackSPLIT_lyr",selectClause)
            numfeats = gpRMA.GetCount_management("tempTESTtrackSPLIT_lyr")
            count = int(numfeats.getOutput(0))
            if count == 0:
                errorSTATUS = 99
            else:
                gpRMA.CopyFeatures_management("tempTESTtrackSPLIT_lyr","tempTESTtrackSPLITrefine")
                gpRMA.Dissolve_management("tempTESTtrackSPLITrefine","trackTEMP",dsslvFields,"","MULTI_PART","UNSPLIT_LINES")
                # Buffer the track data
                roadbufferVal = str(roadbuffer) + " Feet"
                print "road buffer = " + roadbufferVal
                print "Buffering tracks..."
                gpRMA.Buffer_analysis("tempTESTtrackSPLITrefine","bufferTrack",roadbufferVal) #Preserve users and dates
                # Select county-maintained roads
                gpRMA.MakeFeatureLayer_management("bufferTrack","bufferTrackLyr")
                gpRMA.management.MakeFeatureLayer(cmroads,"cmrLyr","\"ASSET_STATUS\" = 'ACTIVE' AND \"JURISDICTION\" = 'CMR - COUNTY-MAINTAINED ROAD'")
                gpRMA.SelectLayerByLocation_management("bufferTrackLyr","INTERSECT","cmrLyr")
                gpRMA.CopyFeatures_management("bufferTrackLyr","cmrbuffer")
                gpRMA.MakeFeatureLayer_management("tempTESTtrackSPLITrefine","trackTEMPLyr")
                gpRMA.SelectLayerByLocation_management("trackTEMPLyr","INTERSECT","cmrbuffer")
                gpRMA.CopyFeatures_management("trackTEMPLyr","cmrTrackTEMP")
                gpRMA.Dissolve_management("cmrTrackTEMP","cmrTrack","","","MULTI_PART","UNSPLIT_LINES")
                # Compare to parcels
                print "Identifying parcels..."
                gpRMA.MakeFeatureLayer_management(parcels,"parcelsLyr")
                gpRMA.SelectLayerByLocation_management("parcelsLyr","INTERSECT","bufferTrack")
                gpRMA.CopyFeatures_management("parcelsLyr","parcelsTEMP")
                # Dissolve parcels by parcel ID (to only count "stacked" (e.g., condo) parcels once)
                print "Dissolving parcels..."
                gpRMA.Dissolve_management("parcelsTEMP","parcelTrack",["PARCELID"],"","MULTI_PART")
                gpRMA.AddField_management("parcelTrack","PARCELS","LONG")
                gpRMA.CalculateField_management("parcelTrack","PARCELS",1)
                # Compare to RMAs
                print "Intersecting data..."
                gpRMA.Intersect_analysis(["trackTEMP",rmaZones,cities],"rmaTrack")
                gpRMA.Intersect_analysis(["parcelTrack",rmaZones,cities],"rmaParcel")
                gpRMA.Intersect_analysis(["cmrTrack",rmaZones,cities],"rmaCMR")
                # Add fields for distance and information
                gpRMA.AddField_management("rmaTrack","MILES","DOUBLE")
                gpRMA.CalculateField_management("rmaTrack","MILES","!Shape.Length@MILES!","PYTHON_9.3")
                gpRMA.AddField_management("rmaTrack","RMAINFO","TEXT","","",250)
                gpRMA.CalculateField_management("rmaTrack","RMAINFO",'[HUNAME] & "/" & [HANAME] & "/" & [HSANAME] & "/" & [HBNUM] & "/" & [NAME_12]')
                gpRMA.AddField_management("rmaParcel","RMAINFO","TEXT","","",250)
                gpRMA.CalculateField_management("rmaParcel","RMAINFO",'[HUNAME] & "/" & [HANAME] & "/" & [HSANAME] & "/" & [HBNUM] & "/" & [NAME_1]')
                gpRMA.AddField_management("rmaCMR","MILES","DOUBLE")
                gpRMA.CalculateField_management("rmaCMR","MILES","!Shape.Length@MILES!","PYTHON_9.3")
                gpRMA.AddField_management("rmaCMR","RMAINFO","TEXT","","",250)
                gpRMA.CalculateField_management("rmaCMR","RMAINFO",'[HUNAME] & "/" & [HANAME] & "/" & [HSANAME] & "/" & [HBNUM] & "/" & [NAME]')
                # Get data summaries
                print "Running frequencies..."
                gpRMA.Frequency_analysis("rmaTrack","sumTracks",["RMAINFO"],["MILES"])
                gpRMA.Frequency_analysis("rmaParcel","sumParcels",["RMAINFO"],["PARCELS"])
                gpRMA.Frequency_analysis("rmaCMR","sumCMR",["RMAINFO"],["MILES"])
                # Write report file
                with gpRMA.da.SearchCursor("sumParcels",["RMAINFO","PARCELS"]) as rowcursor:
                    parcelslist = list(rowcursor)
                del rowcursor
                with gpRMA.da.SearchCursor("sumTracks",["RMAINFO","MILES"]) as rowcursor:
                    tracklist = list(rowcursor)
                del rowcursor
                with gpRMA.da.SearchCursor("sumCMR",["RMAINFO","MILES"]) as rowcursor:
                    cmrlist = list(rowcursor)
                del rowcursor

                print "Writing report..."
                # MG: 6/26/17: Create vars to hold sums
                sum_miles     = 0
                sum_cmr_miles = 0
                sum_parcels   = 0

                with open(rptPath,"w") as csvf:
                    csvf.write("RMA,HUNAME,HANAME,HBNUM,JURISDICTION,MILES,CMRMILES,PARCELS\n")
                    for track in tracklist:
                        rmainfo = str(track[0]).split("/")
                        numparcels = 0
                        for parcels in parcelslist:
                            if str(track[0]) == str(parcels[0]):
                                numparcels = parcels[1]
                        cmrmiles = 0
                        for cmr in cmrlist:
                            if str(track[0]) == str(cmr[0]):
                                cmrmiles = cmr[1]
                        if "SAME AS HANAME" in str(rmainfo[2]):
                            rmastr = str(rmainfo[1])
                        else:
                            rmastr = str(rmainfo[2])

                                   # RMA     ,          HUNAME       ,          HANAME       ,          HBNUM
                        csvf.write(rmastr + "," + str(rmainfo[0]) + "," + str(rmainfo[1]) + "," + str(rmainfo[3]) + "," + \
                                   str(rmainfo[4]) + "," + str(track[1]) + "," + str(cmrmiles) + "," + str(int(numparcels)) + "\n")
                                   #   JURISDICTION   ,         MILES       ,        CMRMILES     ,             PARCELS

                        # MG: 6/26/17: Get sums
                        sum_miles     = sum_miles + track[1]
                        sum_cmr_miles = sum_cmr_miles + cmrmiles
                        sum_parcels   = sum_parcels + numparcels

                    # # MG: 6/26/17: Write the sums to the CSV
                    csvf.write('------, -----, -----, -----, -----, ----- , ----- , -----\n')
                    csvf.write('      ,      ,      ,      ,TOTALS:,' + str(sum_miles) + ',' + str(sum_cmr_miles) + ',' + str(sum_parcels))

except:
    errorSTATUS = 1
    print "********* ERROR while processing... *********"

# Email the results
try:
    if errorSTATUS == 0:  ## No errors
        print "Emailing report..."
        # Set email parameters
        configRMA = ConfigParser.ConfigParser()
        configRMA.read(cfgFile)
        emailusrRMA = configRMA.get("email","usr")
        emailpwdRMA = configRMA.get("email","pwd")
        msgString = "Stormwater RMA report " + datestart + " through " + dateend
        msgRMA = MIMEMultipart()
        fromaddrRMA        = fromEmail
        toaddrRMA          = stmwtrPeeps
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
        msgString = "Daily stormwater user/RMA report--no data found for period " + datestart + " through " + dateend
        msgRMA = MIMEText(msgString)
        fromaddrRMA         = fromEmail
        toaddrRMA           = scriptAdmin  ## <-- LUEG-GIS script administrator
        msgRMA['Subject']   = msgString
        msgRMA['From']        = "Python Script"
        msgRMA['To']          = "LUEG-GIS script administrator"
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
        print gpRMA.GetMessages()
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
        msgRMA['Subject']   = "ERROR with STORMWATER RMA REPORT"
        msgRMA['From']        = "Python Script"
        msgRMA['To']          = "LUEG-GIS script administrator"
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


# END processing - do clerical messaging
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
print "   Duration = " + strdhours + ":" + strdminutes + ":" + strdseconds
print "***************************************************************************"

