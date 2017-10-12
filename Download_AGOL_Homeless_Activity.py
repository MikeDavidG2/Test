#-------------------------------------------------------------------------------
# Purpose:
"""
To download data from an AGOL Feature Service.  This script will download all
of the data in the FS regardless of the size of the data or the number of
features returned by the server.
Users Set:
  The Feature Service URL that ends in .../FeatureServer
  Index that the layer is at in the FS (Usually 0)
  Folder you want the data downloaded to
  Name of the existing FGDB to download (in the Folder set above)
  Name you want to give to the FC
"""
#
# Author:      mgrue
#
# Created:     10/11/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# TODO: Test this script and debug
# TODO: When I'm done writing/testing this script, this should be used to replace my current Download_AGOL_Data.py.
# TODO: Update the script Purpose above to be more accurate.

import arcpy, sys
arcpy.env.overwriteOutput = True

def main():

    #---------------------------------------------------------------------------
    #                     Set Variables that will change

    # Name of this script
    name_of_script = 'Download_AGOL_Homeless_Activity.py'

    # Full path to a text file that has the username and password of an account
    #  that has access to at least VIEW the FS in AGOL, as well as an email
    #  account that has access to send emails.
    cfgFile     = r"<path to config file>"

    # Set the log file variables
    log_file = r'<path to a log file, include the name of the log file after the last />'

    # FS_name is the name of the Feature Service (FS) you want to download (d/l).
    #   For example: "Homeless_Activity_Sites"
    FS_name        = '<name of FS goes here>'

    # Index of the layer in the FS you want to d/l.  Usually 0.
    index_of_layer = 0

    # Set variables of where you want the data to go, and what the d/l FC name should be.
    wkg_folder     = r'<path to a folder>'
    wkg_FGDB       = '<name of EXISTING FGDB in that folder>'
    FC_name        = '<name you want to give the FC that will be created>'

    # Set the Email variables
    email_admin_ls = ['michael.grue@sdcounty.ca.gov']


    #---------------------------------------------------------------------------
    #                Set Variables that will probably not change

    # We will get all the fields
    AGOL_fields = '*'

    # Set the full FS URL. "1vIhDJwtG5eNmiqX" is the COSD portal server so it shouldn't change much.
    FS_url      = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/{}/FeatureServer'.format(FS_name)

    # Flag to control if there is an error
    success = True

    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Calling Functions

    # Turn all 'print' statements into a log-writing object
    if success == True:
        try:
            orig_stdout = Write_Print_To_Log(log_file)
        except Exception as e:
            success = False
            print '*** ERROR with Write_Print_To_Log() ***'
            print str(e)

    # Get a token with permissions to view the data
    if success == True:
        try:
            token = Get_Token(cfgFile)
        except Exception as e:
            success = False
            print '*** ERROR with Get_Token() ***'
            print str(e)

    # Download the data
    if success == True:
        try:
            Get_AGOL_Data_All(AGOL_fields, token, FS_url, index_of_layer, wkg_folder, wkg_FGDB, FC_name)

        except Exception as e:
            success = False
            print '*** ERROR with Get_AGOL_Data_All() ***'
            print str(e)

    # End of script reporting
    print 'Success = {}'.format(success)
    sys.stdout = orig_stdout

    # Email recipients
    if success == True:
        email_subject = 'SUCCESS running {}'.format(name_of_script)
    else:
        email_subject = 'ERROR running {}'.format(name_of_script)

    Email_W_LogFile(email_subject, email_admin_ls, cfgFile, log_file)

#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------
#                              Define Functions
#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Write_Print_To_Log()
def Write_Print_To_Log(log_file):
    """
    PARAMETERS:
      log_file (str): Path to log file.  The part after the last "\" will be the
        name of the .log file after the date, time, and ".log" is appended to it.

    RETURNS:
      orig_stdout (os object): The original stdout is saved in this variable so
        that the script can access it and return stdout back to its orig settings.

    FUNCTION:
      To turn all the 'print' statements into a log-writing object.  A new log
        file will be created based on log_file with the date, time, ".log"
        appended to it.  And any print statements after the command
        "sys.stdout = write_to_log" will be written to this log.
      It is a good idea to use the returned orig_stdout variable to return sys.stdout
        back to its original setting.
      NOTE: This function needs the function Get_DT_To_Append() to run

    """
    print 'Starting Write_Print_To_Log()...'

    # Get the original sys.stdout so it can be returned to normal at the
    #    end of the script.
    orig_stdout = sys.stdout

    # Get DateTime to append
    dt_to_append = Get_DT_To_Append()

    # Create the log file with the datetime appended to the file name
    log_file_date = '{}_{}.log'.format(log_file,dt_to_append)
    write_to_log = open(log_file_date, 'w')

    # Make the 'print' statement write to the log file
    print '  Setting "print" command to write to a log file found at:\n  {}'.format(log_file_date)
    sys.stdout = write_to_log

    # Header for log file
    start_time = datetime.datetime.now()
    start_time_str = [start_time.strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                  {}'.format(start_time_str)
    print '             START <name_of_script_here>.py'
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'

    return orig_stdout

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Get_dt_to_append
def Get_DT_To_Append():
    """
    PARAMETERS:
      none

    RETURNS:
      dt_to_append (str): Which is in the format 'YYYY_MM_DD__HH_MM_SS'

    FUNCTION:
      To get a formatted datetime string that can be used to append to files
      to keep them unique.
    """
    print 'Starting Get_DT_To_Append()...'

    start_time = datetime.datetime.now()

    date = start_time.strftime('%Y_%m_%d')
    time = start_time.strftime('%H_%M_%S')

    dt_to_append = '%s__%s' % (date, time)

    print '  DateTime to append: {}'.format(dt_to_append)

    print 'Finished Get_DT_To_Append()\n'
    return dt_to_append

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION:    Get AGOL token
def Get_Token(cfgFile, gtURL="https://www.arcgis.com/sharing/rest/generateToken"):
    """
    PARAMETERS:
      cfgFile (str):
        Path to the .txt file that holds the user name and password of the
        account used to access the data.  This account must be in a group
        that has access to the online database.
        The format of the config file should be as below with
        <username> and <password> completed:

          [AGOL]
          usr: <username>
          pwd: <password>

      gtURL {str}: URL where ArcGIS generates tokens. OPTIONAL.

    VARS:
      token (str):
        a string 'password' from ArcGIS that will allow us to to access the
        online database.

    RETURNS:
      token (str): A long string that acts as an access code to AGOL servers.
        Used in later functions to gain access to our data.

    FUNCTION: Gets a token from AGOL that allows access to the AGOL data.
    """

    print '--------------------------------------------------------------------'
    print "Getting Token..."

    import ConfigParser, urllib, urllib2, json

    # Get the user name and password from the cfgFile
    configRMA = ConfigParser.ConfigParser()
    configRMA.read(cfgFile)
    usr = configRMA.get("AGOL","usr")
    pwd = configRMA.get("AGOL","pwd")

    # Create a dictionary of the user name, password, and 2 other keys
    gtValues = {'username' : usr, 'password' : pwd, 'referer' : 'http://www.arcgis.com', 'f' : 'json' }

    # Encode the dictionary so they are in URL format
    gtData = urllib.urlencode(gtValues)

    # Create a request object with the URL adn the URL formatted dictionary
    gtRequest = urllib2.Request(gtURL,gtData)

    # Store the response to the request
    gtResponse = urllib2.urlopen(gtRequest)

    # Store the response as a json object
    gtJson = json.load(gtResponse)

    # Store the token from the json object
    token = gtJson['token']
    ##print token  # For testing purposes

    print "Successfully retrieved token.\n"

    return token

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                             FUNCTION Get_AGOL_Data_All()
def Get_AGOL_Data_All(AGOL_fields, token, FS_url, index_of_layer, wkg_folder, wkg_FGDB, FC_name):
    """
    PARAMETERS:
      AGOL_fields (str) = The fields we want to have the server return from our query.
        use the string ('*') to return all fields.
      token (str) = The token obtained by the Get_Token() which gives access to
        AGOL databases that we have permission to access.
      FS_url (str) = The URL address for the feature service.
        Should be the service URL on AGOL (up to the '/FeatureServer' part).
      index_of_layer (int)= The index of the specific layer in the FS to download.
        i.e. 0 if it is the first layer in the FS, 1 if it is the second layer, etc.
      wkg_folder (str) = Full path to the folder that contains the FGDB that you
        want to download the data into.  FGDB must already exist.
      wkg_FGDB (str) = Name of the working FGDB in the wkg_folder.
      FC_name (str) = The name of the FC that will be created to hold the data
        downloaded by this function.  This FC gets overwritten every time the
        script is run.

    RETURNS:
      None

    FUNCTION:
      To download ALL data from a layer in a FS on AGOL, using OBJECTIDs.
      This function, establishs a connection to the
      data, finds out the number of features, gets the highest and lowest OBJECTIDs,
      and the maxRecordCount returned by the server, and then loops through the
      AGOL data and downloads it to the FGDB.  The first time the data is d/l by
      the script it will create a FC.  Any subsequent loops will download the
      next set of data and then append the data to the first FC.  This looping
      will happen until all the data has been downloaded and appended to the one
      FC created in the first loop.

    NOTE:
      Need to have obtained a token from the Get_Token() function.
      Need to have an existing FGDB to download data into.
    """
    print '--------------------------------------------------------------------'
    print 'Starting Get_AGOL_Data_All()'

    import urllib2, json, urllib

    # Set URLs
    query_url = FS_url + '/{}/query'.format(index_of_layer)
    print '  Downloading all data found at: {}/{}\n'.format(FS_url, index_of_layer)

    #---------------------------------------------------------------------------
    #        Get the number of records are in the Feature Service layer

    # This query returns ALL the OBJECTIDs that are in a FS regardless of the
    #   'max records returned' setting
    query = "?where=1=1&returnIdsOnly=true&f=json&token={}".format(token)
    obj_count_URL = query_url + query
    ##print obj_count_URL  # For testing purposes
    response = urllib2.urlopen(obj_count_URL)  # Send the query to the web
    obj_count_json = json.load(response)  # Store the response as a json object
    try:
        object_ids = obj_count_json['objectIds']
    except:
        print 'ERROR!'
        print obj_count_json['error']['message']

    num_object_ids = len(object_ids)
    print '  Number of records in FS layer: {}'.format(num_object_ids)

    #---------------------------------------------------------------------------
    #                  Get the lowest and highest OBJECTID
    object_ids.sort()
    lowest_obj_id = object_ids[0]
    highest_obj_id = object_ids[num_object_ids-1]
    print '  The lowest OBJECTID is: {}\n  The highest OBJECTID is: {}'.format(\
                                                  lowest_obj_id, highest_obj_id)

    #---------------------------------------------------------------------------
    #               Get the 'maxRecordCount' of the Feature Service
    # 'maxRecordCount' is the number of records the server will return
    # when we make a query on the data.
    query = '?f=json&token={}'.format(token)
    max_count_url = FS_url + query
    ##print max_count_url  # For testing purposes
    response = urllib2.urlopen(max_count_url)
    max_record_count_json = json.load(response)
    max_record_count = max_record_count_json['maxRecordCount']
    print '  The max record count is: {}\n'.format(str(max_record_count))


    #---------------------------------------------------------------------------

    # Set the variables needed in the loop below
    start_OBJECTID = lowest_obj_id  # i.e. 1
    end_OBJECTID   = lowest_obj_id + max_record_count - 1  # i.e. 1000
    last_dl_OBJECTID = 0  # The last downloaded OBJECTID
    first_iteration = True  # Changes to False at the end of the first loop

    while last_dl_OBJECTID <= highest_obj_id:
        where_clause = 'OBJECTID >= {} AND OBJECTID <= {}'.format(start_OBJECTID, end_OBJECTID)

        # Encode the where_clause so it is readable by URL protocol (ie %27 = ' in URL).
        # visit http://meyerweb.com/eric/tools/dencoder to test URL encoding.
        # If you suspect the where clause is causing the problems, uncomment the
        #   below 'where = "1=1"' clause.
        ##where_clause = "1=1"  # For testing purposes
        print '  Getting data where: {}'.format(where_clause)
        where_encoded = urllib.quote(where_clause)
        query = "?where={}&outFields={}&returnGeometry=true&f=json&token={}".format(where_encoded, AGOL_fields, token)
        fsURL = query_url + query

        # Create empty Feature Set object
        fs = arcpy.FeatureSet()

        #---------------------------------------------------------------------------
        #                 Try to load data into Feature Set object
        # This try/except is because the fs.load(fsURL) will fail whenever no data
        # is returned by the query.
        try:
            ##print 'fsURL %s' % fsURL  # For testing purposes
            fs.load(fsURL)
        except:
            print '*** ERROR, data not downloaded ***'

        #-----------------------------------------------------------------------
        # Process d/l data

        if first_iteration == True:  # Then this is the first run and d/l data to the FC_name
            path = wkg_folder + "\\" + wkg_FGDB + '\\' + FC_name
        else:
            path = wkg_folder + "\\" + wkg_FGDB + '\\temp_to_append'

        #Copy the features to the FGDB.
        print '    Copying AGOL database features to: %s' % path
        arcpy.CopyFeatures_management(fs,path)

        # If this is a subsequent run then append the newly d/l data to the FC_name
        if first_iteration == False:
            orig_path = wkg_folder + "\\" + wkg_FGDB + '\\' + FC_name
            print '    Appending:\n      {}\n      To:\n      {}'.format(path, orig_path)
            arcpy.Append_management(path, orig_path, 'NO_TEST')

            print '    Deleting temp_to_append'
            arcpy.Delete_management(path)

        # Set the last downloaded OBJECTID
        last_dl_OBJECTID = end_OBJECTID

        # Set the starting and ending OBJECTID for the next iteration
        start_OBJECTID = end_OBJECTID + 1
        end_OBJECTID   = start_OBJECTID + max_record_count - 1

        # If we reached this point we have gone through one full iteration
        first_iteration = False
        print ''

    if first_iteration == False:
        print "  Successfully retrieved data.\n"
    else:
        print '  * WARNING, no data was downloaded. *'

    print 'Finished Get_AGOL_Data_All()'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Email_W_LogFile()
def Email_W_LogFile(email_subject, email_recipients, email_login_info, log_file=None):
    """
    PARAMETERS:
      email_subject (str): The subject line for the email

      email_recipients (list): List (of strings) of email addresses

      email_login_info (str): Path to a config file with username and password.
        The format of the config file should be as below with
        <username> and <password> completed:

          [email]
          usr: <username>
          pwd: <password>


      log_file {str}: Path to a log file to be included in the body of the
        email. Optional.

    RETURNS:
      None

    FUNCTION:
      To send an email to the listed recipients.  May provide a log file to
      include in the body of the email.
    """

    import smtplib, ConfigParser
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    print 'Starting Email()'

    # Set log file into body of email if provided
    if log_file != None:
        # Get the log file to add to email body
        fp = open(log_file,"rb")
        msg = MIMEText(fp.read())
        fp.close()
    else:
        msg = MIMEMultipart()

    # Get username and pwd from the config file
    try:
        config = ConfigParser.ConfigParser()
        config.read(email_login_info)
        email_usr = config.get("email","usr")
        email_pwd = config.get("email","pwd")
    except:
        print 'ERROR!  Could not read config file.  May not exist at location, or key may be incorrect.  Email not sent.'
        return

    # Set from and to addresses
    fromaddr = "dplugis@gmail.com"
    toaddr = email_recipients
    email_recipients_str = ', '.join(email_recipients)  # Join each item in list with a ', '

    # Set visible info in email
    msg['Subject'] = email_subject
    msg['From']    = "Python Script"
    msg['To']      = email_recipients_str

    # Email
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(email_usr,email_pwd)
    s.sendmail(fromaddr,toaddr,msg.as_string())
    s.quit()

    print 'Sent email with subject "{}"'.format(email_subject)
    print 'To: {}'.format(email_recipients_str)

    return

#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
