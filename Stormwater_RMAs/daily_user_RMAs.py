##############################################
###           daily_user_RMAs.py           ###
###  Python script to report daily values  ###
###     from user tracks (user and RMA)    ###
###  Karen Chadwick           August 2015  ###
###  *** ASSUMES START AFTER MIDNIGHT ***  ###
##############################################
# TODO: Document this script
# TODO: Go through all print statements in both main() and Get_List...()

# Import modules
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

def main():
    timestart = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    stimes = time.time()

    #######################################################################################
    #######################################################################################
    ###  Set any changeable variables between here ---------------------------------->  ###

    roadbuffer  = 40
    distcutoff  = 5280  ###  cutoff distance (FEET)
    cfgFile     = "M:\\scripts\\configFiles\\accounts.txt"
    ##stmwtrPeeps = ["alex.romo@sdcounty.ca.gov","randy.yakos@sdcounty.ca.gov","gary.ross@sdcounty.ca.gov"]
    ##scriptAdmin = ["randy.yakos@sdcounty.ca.gov","gary.ross@sdcounty.ca.gov"]
    # TODO before going to prod: remove the below variables and uncomment the above. MG: 6/26/17
    stmwtrPeeps = ['michael.grue@sdcounty.ca.gov']
    scriptAdmin = ['michael.grue@sdcounty.ca.gov']
    fromEmail   = "dplugis@gmail.com"

    ###  <-------------------------------------------------------------------  and here ###
    #######################################################################################
    #######################################################################################


    # Set variables that shouldn't change much
    trackURL    = "http://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/Track_line/FeatureServer/0/query"
    ##wkgFolder   = "P:\\stormwater\\scripts\\data"
    # TODO: before going to prod script: remove below variable and uncomment the above. MG: 6/26/17
    wkgFolder   = r'U:\grue\Scripts\GitHub\Test\Stormwater_RMAs\data' # MG 06/26/17: changed working folder for testing purposes
    wkgGDB      = "RMAuserWKG.gdb"
    wkgPath     = wkgFolder + "\\" + wkgGDB
    indataFC    = "Track_line"
    outTrackFC  = "outUserTracksRMA"
    rmaZones    = r"P:\stormwater\data_ago\agol_stormdata.gdb\RMA_HSA_JUR1"
    gtURL       = "https://www.arcgis.com/sharing/rest/generateToken"
    dsslvFields = ['NAME', 'DATE', 'EDITOR', 'EDITDATE', 'HUNAME', 'HANAME', 'HSANAME', 'HBNUM']
    AGOfields   = "NAME,DATE,GlobalID,EDITOR,EDITDATE"
    warehouse   = "M:\\scripts\\Database Connections\\Atlantic Warehouse (sangis user).sde\\"
    cmroads_fc  = warehouse + "SDE.SANGIS.ROAD_SEGMENTS"
    parcels_fc  = warehouse + "SDE.SANGIS.PARCELS_ALL"


    # Make print statements write to a log file
    logFileNameRMA = str(wkgFolder) + "\\..\\log\\dailyUserRMAs_" + str(time.strftime("%Y%m%d%H%M", time.localtime())) + ".txt"
    logFileRMA = open(logFileNameRMA,"w")
    old_outputRMA = sys.stdout

    # TODO before going to prod: Uncomment out below and remove comment
    # MG 06/26/17: commented out for testing purposes
    ##sys.stdout = logFileRMA

    # START processing
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = wkgFolder
    errorSTATUS = 0

    print "************************* DAILY_USER_RMAS.PY *************************"

    # Preliminary setup
    try:
        # Get dates and report name
        # Assumes start time *AFTER* midnight
        today = datetime.date.today()
        todaystr = str(today)
        print "todaystr = " + todaystr
        de = today + datetime.timedelta(days=-1) # To show the right day for the report name
        dateend = str(de)
        print "dateend = " + dateend
        ds = today + datetime.timedelta(days=-7)
        datestart = str(ds)
        print "datestart = " + datestart
        # Dates are in UTC, converted to view in PST --> adjust for PST (8 hours)
        dec = datetime.datetime(de.year,de.month,de.day)
        dateendconv = str(dec + datetime.timedelta(days=1,hours=8)) # To search for the correct date range
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

    # Get AGOL token
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
            # process that happens in the 'Process the data' step, only the URL query.
            # We want to set the 'where' clause to get records where the [DATE]
            # field is BETWEEN the 'datestart' and 'dateend + two days'.
            # By adding 2 days into the future we ensure that we are grabbing all of
            # the data from AGOL that we may need to process, while ENSURING that we
            # do not try to grab more than 2000 records (which is the limit of this
            # feature service)
            two_days = datetime.timedelta(days=2)
            dateend_td_obj = datetime.datetime.strptime(dateend, '%Y-%m-%d')  # Get a datetime object from dateend
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

    # Process the data
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
                    #---------------------------------------------------------------
                    #---------------------------------------------------------------
                    # MG 6/30/17: Find the values for MILES, CMRMILES, and PARCELS

                    # Intersect the split tracks with rma zones so we can dissolve on the rma zones
                    arcpy.Intersect_analysis(['tempTESTtrackSPLITrefine', rmaZones], 'refine_rma_INT')

                    # Add field [MILES] and calc as a value from [Shape_Length]
                    arcpy.AddField_management("refine_rma_INT","MILES","DOUBLE")
                    arcpy.CalculateField_management("refine_rma_INT","MILES","!Shape.Length@MILES!","PYTHON_9.3")

                    # Add field [CMRMILES] and calc as 0 (As a default.  Mileage of CMR calculated below)
                    arcpy.AddField_management("refine_rma_INT","CMRMILES","DOUBLE")
                    arcpy.CalculateField_management("refine_rma_INT","CMRMILES",0,"PYTHON_9.3")

                    #---------------------------------------------------------------
                    # Find which split tracks are on CMR's and calculate their mileage

                    # Buffer the track data
                    roadbufferVal = str(roadbuffer) + " Feet"
                    print "road buffer = " + roadbufferVal
                    print "Buffering tracks..."
                    arcpy.Buffer_analysis("refine_rma_INT","bufferTrack",roadbufferVal)

                    # Make feature layers of the buffered track data, and active/County Maintained Roads
                    arcpy.MakeFeatureLayer_management("bufferTrack","bufferTrackLyr")
                    arcpy.management.MakeFeatureLayer(cmroads_fc,"cmrLyr","\"ASSET_STATUS\" = 'ACTIVE' AND \"JURISDICTION\" = 'CMR - COUNTY-MAINTAINED ROAD'")

                    # Select buffered tracks that Intersect the County Maintained Roads
                    # Export those selected buffers as CMR buffers
                    arcpy.SelectLayerByLocation_management("bufferTrackLyr","INTERSECT","cmrLyr")
                    arcpy.CopyFeatures_management("bufferTrackLyr","cmrbuffer")

                    # Make feature layer of the split tracks and select the split tracks
                    # that are COMPLETELY_WITHIN
                    #    (to reduce errors occuring from interstate driving on underpasses under CMR's)
                    # the CMR buffers.
                    # The selected tracks represent tracks on County Maintained Roads,
                    # Calculate their length
                    arcpy.MakeFeatureLayer_management("refine_rma_INT","refine_rma_INTLyr")
                    arcpy.SelectLayerByLocation_management("refine_rma_INTLyr","COMPLETELY_WITHIN","cmrbuffer")
                    numfeats = arcpy.GetCount_management("refine_rma_INTLyr")
                    count = int(numfeats.getOutput(0))
                    if count == 0:
                        errorSTATUS = 99
                    else:
                        arcpy.CalculateField_management('refine_rma_INTLyr', 'CMRMILES', '!Shape.Length@MILES!', 'PYTHON_9.3')

                    #---------------------------------------------------------------
                    # Dissolve data on all fields we need (and sum [MILES], [CMRMILES])
                    arcpy.Dissolve_management("refine_rma_INT","rmaTrack",dsslvFields,[['MILES','SUM'],['CMRMILES','SUM']],"MULTI_PART","DISSOLVE_LINES")

                    #---------------------------------------------------------------
                    # Find number of parcels per RMA Track
                    arcpy.AddField_management("rmaTrack","PARCELS","DOUBLE")
                    ##arcpy.CalculateField_management('rmaTrack', 'PARCELS', 0)
                    Get_List_Of_Parcels('rmaTrack', parcels_fc, roadbufferVal)

                    #---------------------------------------------------------------
                    #---------------------------------------------------------------
                    # Compare to RMAs
                    print "Adding/calculating COLLECTDATE and INFOSTR fields..."
                    numfeats = arcpy.GetCount_management("rmaTrack")
                    count = int(numfeats.getOutput(0))
                    if count == 0:
                        errorSTATUS = 99
                    else:
                        # Add field [COLLECTDATE]
                        arcpy.AddField_management("rmaTrack","COLLECTDATE","TEXT","","",12)
                        arcpy.MakeTableView_management("rmaTrack","rmaTrackView")

                        # Update [COLLECTDATE] with [DATE] values as a string and without the time component
                        with arcpy.da.UpdateCursor("rmaTrackView",["DATE","COLLECTDATE"]) as rowcursor:
                            for row in rowcursor:
                                datetimeVal = row[0]
                                dateVal = datetime.datetime.strftime(datetimeVal,"%m/%d/%Y")
                                row[1] = dateVal
                                rowcursor.updateRow(row)
                            del rowcursor, row

                        # Add field [INFOSTR] and calc as a string aggregate of all info we want to report
                        arcpy.AddField_management("rmaTrack","INFOSTR","TEXT","","",300)
                        arcpy.CalculateField_management("rmaTrack","INFOSTR",'[NAME] & "__" & [COLLECTDATE] & "__" & [HUNAME] & "/" & [HANAME] & "/" & [HSANAME] & "/" & [HBNUM] & "/" & [SUM_MILES] & "/" & [SUM_CMRMILES] & "/" & [PARCELS]')

                        # Get data summaries
                        print "Running frequencies..."
                        arcpy.MakeFeatureLayer_management("rmaTrack","rmaTrackLyr","\"HBNUM\" <> 0")
                        arcpy.Frequency_analysis("rmaTrackLyr","sumTracks",["INFOSTR"])

                        # Write report file
                        with arcpy.da.SearchCursor("sumTracks",["INFOSTR"]) as rowcursor:
                            tracklist = list(rowcursor)
                        del rowcursor

                        print "Writing report..."
                        # MG: 6/26/17: Create vars to hold sums
                        sum_miles    = 0
                        sum_cmrmiles = 0
                        sum_parcels  = 0

                        with open(rptPath,"w") as csvf:
                            csvf.write("NAME,DATE,RMA,HUNAME,HANAME,HBNUM, MILES, CMRMILES, PARCELS\n")
                            for track in tracklist:
                                usrinfo = track[0].split("__")
                                    # Above turns: "paola_dpw__06/26/2017__CARLSBAD/Escondido Creek/Escondido/904.62"
                                    #          to: "paola_dpw  06/26/2017  CARLSBAD/Escondido Creek/Escondido/904.62"
                                    #              usrinfo[0]  usrinfo[1]  usrinfo[2]
                                rmainfo = usrinfo[2].split("/")
                                if "SAME AS HANAME" in rmainfo[2]:
                                    rmastr = rmainfo[1]
                                else:
                                    rmastr = rmainfo[2]

                                # Round MILES and CMRMILES to 2 decimal pts.
                                miles = round(float(rmainfo[4]), 2)
                                cmr_miles = round(float(rmainfo[5]), 2)

                                #          NAME          ,    DATE          ,    RMA       ,    HUNAME        ,    HANAME        ,    HBNUM         ,    MILES         ,    CMRMILES          ,    PARCELS
                                csvf.write(usrinfo[0] + "," + usrinfo[1] + "," + rmastr + "," + rmainfo[0] + "," + rmainfo[1] + "," + rmainfo[3] + "," + str(miles) + "," + str(cmr_miles) + ',' + rmainfo[6] + "\n")

                                # MG: 6/26/17: Get sums
                                sum_miles     = sum_miles + miles
                                sum_cmrmiles  = sum_cmrmiles + cmr_miles
                                sum_parcels   = sum_parcels + int(rmainfo[6])

                            # # MG: 6/26/17: Write the sums to the CSV
                            csvf.write('------, -----, -----, -----, -----, ----- , ----- , ----- , -----\n')
                            csvf.write('      ,      ,      ,      ,      ,TOTALS:,' + str(sum_miles) + "," + str(sum_cmrmiles) + ',' + str(sum_parcels))
    except Exception as e:
        errorSTATUS = 1
        print "********* ERROR while processing... *********"
        print str(e)

    # Email the results
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

    except Exception as e:
        errorSTATUS = 1
        print "********* ERROR while emailing... *********"
        print str(e)

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


#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------
#                              DEFINE NON-MAIN FUNCTIONS
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         Function: Get_List_Of_Parcels

def Get_List_Of_Parcels(rmaTrack, parcel_fc, roadBufferVal):
    #TODO: Document this function
    """
    """

    # Make feature layers needed below
    arcpy.MakeFeatureLayer_management(rmaTrack, 'rmaTrackLyr')
    arcpy.MakeFeatureLayer_management(parcel_fc,  'parcel_fcLyr')


    # Create a cursor to loop through all features in rmaTrack
    with arcpy.da.SearchCursor(rmaTrack, ['OBJECTID']) as trackCursor:
        for row in trackCursor:
            where_clause = "OBJECTID = {}".format(str(row[0])) # Select track by OBJECTID
            print 'Selecting where: ' + where_clause
            arcpy.SelectLayerByAttribute_management('rmaTrackLyr', 'NEW_SELECTION', where_clause)

            # Confirm one track was selected
            numfeats = arcpy.GetCount_management("rmaTrackLyr")
            count = int(numfeats.getOutput(0))
            ##print 'Count: ' + str(count)
            if count == 1:

                # Select parcels by location based on the selected track
                arcpy.SelectLayerByLocation_management('parcel_fcLyr', 'WITHIN_A_DISTANCE', 'rmaTrackLyr', roadBufferVal, 'NEW_SELECTION')

                # Find out how many parcels selected
                numfeats = arcpy.GetCount_management("parcel_fcLyr")
                count = int(numfeats.getOutput(0))
                print 'Number of selected parcels: ' + str(count)

                # Get a list of ALL the PARCELID's of the selected parcels
                # Use PARCELID so we don't count 'stacked' parcels,
                # but only parcel footprints.
                parcel_ids = []
                with arcpy.da.SearchCursor('parcel_fcLyr', ['PARCELID']) as parcelCursor:
                    for row in parcelCursor:
                        parcel_ids.append(row[0])

                # Get a list of all the UNIQUE PARCELID's.
                # set() returns a list of only unique values
                unique_parcel_ids = sorted(set(parcel_ids))
                num_unique_parcel_ids = len(unique_parcel_ids)
                print 'Number of PARCELID\'s: {}'.format(str(num_unique_parcel_ids))

                # Calculate the PARCEL field in rmaTrack as the number of unique parcel ids
                # Only the selected feature in rmaTrack will have it's field calculated.
                arcpy.CalculateField_management('rmaTrackLyr', 'PARCELS', num_unique_parcel_ids, 'PYTHON_9.3')

            print ''

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

# Call main() function
if __name__ == '__main__':
    main()
