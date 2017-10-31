#-------------------------------------------------------------------------------
# Purpose:
"""
To download the attachments in a Feature Service
"""
#
# Author:      mgrue
#
# Created:     10/13/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# TODO: Update the script Purpose above to be more accurate.

import arcpy, sys, datetime, os, ConfigParser, urllib, urllib2, json
arcpy.env.overwriteOutput = True

def main():

    #---------------------------------------------------------------------------
    #                     Set Variables that will change
    #---------------------------------------------------------------------------

    # Name of this script
    name_of_script = 'Download_AGOL_Attachments'

    # Set the path prefix depending on if this script is called manually by a
    #  user, or called by a scheduled task on ATLANTIC server.
    called_by = arcpy.GetParameterAsText(0)

    if called_by == 'MANUAL':
        path_prefix = 'U:'

    elif called_by == 'SCHEDULED':
        path_prefix = 'D:\users'

    else:  # If script run directly
        path_prefix = 'U:'

    #---------------------------------------------------------------------------
    # Full path to a text file that has the username and password of an account
    #  that has access to at least VIEW the FS in AGOL, as well as an email
    #  account that has access to send emails.
    cfgFile     = r"{}\yakos\hep_A\PROD\Environment_B\Scripts_B\Source_Code\config_file.ini".format(path_prefix)
    if os.path.isfile(cfgFile):
        config = ConfigParser.ConfigParser()
        config.read(cfgFile)
    else:
        print("INI file not found. \nMake sure a valid '.ini' file exists at {}.".format(cfgFile))
        sys.exit()

    # Set the log file variables
    log_file = r'{}\yakos\hep_A\PROD\Environment_B\Scripts_B\Logs\{}'.format(path_prefix, name_of_script)

    # Set the data paths
    ##attachments_folder       = r'{}\yakos\hep_A\PROD\Environment_B\Attachments_B'.format(path_prefix)
    attachments_folder = r'C:\Users\mgrue\Desktop\Delete_Me'

    # Get list of Feature Service Names and find the FS that has the attachments
    FS_names     = config.get('Download_Info', 'FS_names')
    FS_names_ls  = FS_names.split(', ')
    FS_index_in_ls = 2  # This index is the position of the FS with the attachments in the FS_names_ls list

    # Set the Email variables
    email_admin_ls = ['michael.grue@sdcounty.ca.gov']#, 'randy.yakos@sdcounty.ca.gov', 'gary.ross@sdcounty.ca.gov']

    #---------------------------------------------------------------------------
    #                Set Variables that will probably not change

    # Flag to control if there is an error
    success = True

    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Calling Functions

    # Turn all 'print' statements into a log-writing object
##    if success == True:
##        try:
##            orig_stdout, log_file_date = Write_Print_To_Log(log_file, name_of_script)
##        except Exception as e:
##            success = False
##            print '*** ERROR with Write_Print_To_Log() ***'
##            print str(e)

    # Get a token with permissions to view the data
    if success == True:
        try:
            token = Get_Token(cfgFile)
        except Exception as e:
            success = False
            print '*** ERROR with Get_Token() ***'
            print str(e)

    # Get Attachments
    if success == True:
        # Set the full FS URL. "1vIhDJwtG5eNmiqX" is the CoSD portal server so it shouldn't change much.
        FS_url  = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/{}/FeatureServer'.format(FS_names_ls[FS_index_in_ls])

        FS_index_in_AGOL = config.get('Download_Info', 'FS_indexes')
        FS_index_in_AGOL_ls = FS_index_in_AGOL.split(', ')
        my_index = FS_index_in_AGOL_ls[FS_index_in_ls]

        ##gaURL = FS_url + '/' + my_index + '/?CreateReplica'  # Get Attachments URL # TODO: May not need the my_index variable afterall
        gaURL = FS_url + '/CreateReplica?'  # Get Attachments URL
        print gaURL

        Get_Attachments(token, gaURL, attachments_folder)

    # Footer for log file
    finish_time_str = [datetime.datetime.now().strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                    {}'.format(finish_time_str)
    print '              Finished {}'.format(name_of_script)
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

    # End of script reporting
    print 'Success = {}'.format(success)
    sys.stdout = orig_stdout

    # Email recipients
    if success == True:
        subj = 'SUCCESS running {}'.format(name_of_script)
        body = """Success<br>
        The Log file name is: {}""".format(os.path.basename(log_file_date))

    else:
        subj = 'ERROR running {}'.format(name_of_script)
        body = """There was an error with this script.<br>
        Please see the log file for more info.<br>
        The Log file name is: {}""".format(os.path.basename(log_file_date))

    Email_W_Body(subj, body, email_admin_ls, cfgFile)

    # End of script reporting
    if success == True:
        print 'SUCCESSFULLY ran {}'.format(name_of_script)
    else:
        print '*** ERROR with {} ***'.format(name_of_script)
        print 'Please see log file (noted above) for troubleshooting\n'

    if called_by == 'MANUAL':
        raw_input('Press ENTER to continue')

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
def Write_Print_To_Log(log_file, name_of_script):
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
    ##print 'Starting Write_Print_To_Log()...'

    # Get the original sys.stdout so it can be returned to normal at the
    #    end of the script.
    orig_stdout = sys.stdout

    # Get DateTime to append
    dt_to_append = Get_DT_To_Append()

    # Create the log file with the datetime appended to the file name
    log_file_date = '{}_{}.log'.format(log_file,dt_to_append)
    write_to_log = open(log_file_date, 'w')

    # Make the 'print' statement write to the log file
    print 'Find log file found at:\n  {}'.format(log_file_date)
    print '\nProcessing...\n'
    sys.stdout = write_to_log

    # Header for log file
    start_time = datetime.datetime.now()
    start_time_str = [start_time.strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                  {}'.format(start_time_str)
    print '             START {}'.format(name_of_script)
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'

    return orig_stdout, log_file_date

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
    ##print 'Starting Get_DT_To_Append()...'

    start_time = datetime.datetime.now()

    date = start_time.strftime('%Y_%m_%d')
    time = start_time.strftime('%H_%M_%S')

    dt_to_append = '%s__%s' % (date, time)

    ##print '  DateTime to append: {}'.format(dt_to_append)

    ##print 'Finished Get_DT_To_Append()\n'
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
#                         FUNCTION:   Get Attachments
# Attachments (images) are obtained by hitting the REST endpoint of the feature
# service (gaURL) and returning a URL that downloads a JSON file (which is a
# replica of the database).  The script then uses that downloaded JSON file to
# get the URL of the actual images.  The JSON file is then used to get the
# StationID and SampleEventID of the related feature so they can be used to name
# the downloaded attachment.

#TODO: find a way to rotate the images clockwise 90-degrees
def Get_Attachments(token, gaURL, gaFolder):
    """
    PARAMETERS:
        token (str):
            The string token obtained in FUNCTION Get_Token().
        gaURL (str):
            The variable set in FUNCTION main() where we can request to create a
            replica FGDB in json format.
        wkgFolder (str):
            The variable set in FUNCTION main() which is a path to our working
            folder.
        dt_to_append (str):
            The date and time string returned by FUNCTION Get_DateAndTime().

    VARS:
        replicaUrl (str):
            URL of the replica FGDB in json format.
        JsonFileName (str):
            Name of the temporary json file.
        gaFolder (str):
            A folder in the wkgFolder that holds the attachments.
        gaRelId (str):
            The parentGlobalId of the attachment.  This = the origId for the
            related feature.
        origId (str):
            The GlobalId of the feature.  This = the parentGlobalId of the
            related attachment.
        origName1 (str):
            The StationID of the related feature to the attachment.
        origName2 (str):
            The SampleEventID of the related feature to the attachment.
        attachName (str):
            The string concatenation of origName1 and origName2 to be used to
            name the attachment.
        dupList (list of str):
            List of letters ('A', 'B', etc.) used to append to the end of an
            image to prevent multiple images with the same StationID and
            SampleEventID overwriting each other.
        attachmentUrl:
            The URL of each specific attachment.  Need a token to actually
            access and download the image at this URL.

    RETURNS:
        gaFolder (str):
            So that the email can send that information.

    FUNCTION:
      Gets the attachments (images) that are related to the database features and
      stores them as .jpg in a local file inside the wkgFolder.
    """

    print '--------------------------------------------------------------------'
    print 'Getting Attachments...'

    # Flag to set if Attachments were downloaded.  Set to 'True' if downloaded
    attachment_dl = False

    test = gaURL + '&' + 'token=' + token
    print test
    #---------------------------------------------------------------------------
    #                       Get the attachments url (ga)
    # Set the values in a dictionary
    gaValues = {
    'f' : 'pjson',
    'replicaName' : 'Homeless_Activity_Replica',
    'layers' : '0',
    'geometryType' : 'esriGeometryPoint',
    'transportType' : 'esriTransportTypeUrl',
    'returnAttachments' : 'true',
    'returnAttachmentDatabyURL' : 'false',
    'token' : token
    }

    # Get the Replica URL
    gaData = urllib.urlencode(gaValues)
    print gaData
    gaRequest = urllib2.Request(gaURL, gaData)
    print gaRequest
    gaResponse = urllib2.urlopen(gaRequest)
    print gaResponse
    gaJson = json.load(gaResponse)
    print gaJson
    replicaUrl = gaJson['URL']
    ##print '  Replica URL: %s' % str(replicaUrl)  # For testing purposes

    # Set the token into the URL so it can be accessed
    replicaUrl_token = replicaUrl + '?&token=' + token + '&f=json'
    print '  Replica URL Token: %s' % str(replicaUrl_token)  # For testing purposes

    #---------------------------------------------------------------------------
    #                         Save the JSON file
    # Access the URL and save the file to the current working directory named
    # 'myLayer.json'.  This will be a temporary file and will be deleted

    JsonFileName = 'Temp_JSON.json'

    # Save the file
    # NOTE: the file is saved to the 'current working directory' + 'JsonFileName'
    urllib.urlretrieve(replicaUrl_token, JsonFileName)

    # Allow the script to access the saved JSON file
    cwd = os.getcwd()  # Get the current working directory
    jsonFilePath = cwd + '\\' + JsonFileName # Path to the downloaded json file
    print '  Temp JSON file saved to: ' + jsonFilePath

    #---------------------------------------------------------------------------
    #                       Save the attachments

    # Make the gaFolder (to hold attachments) if it doesn't exist.
    if not os.path.exists(gaFolder):
        os.makedirs(gaFolder)

    # Open the JSON file
    with open (jsonFilePath) as data_file:
        data = json.load(data_file)

    # Save the attachments
    # Loop through each 'attachment' and get its parentGlobalId so we can name
    #  it based on its corresponding feature
    print '  Attempting to save attachments:'

    breakpoint

    for attachment in data['layers'][0]['attachments']:
        gaRelId = attachment['parentGlobalId']

        # Now loop through all of the 'features' and break once the corresponding
        #  GlobalId's match so we can save based on the 'StationID'
        #  and 'SampleEventID'
        for feature in data['layers'][0]['features']:
            origId = feature['attributes']['globalid']
            StationID = feature['attributes']['StationID']
            SampleEventID = str(feature['attributes']['SampleEventID'])
            if origId == gaRelId:
                break

        # Test to see if the StationID is one of the features downloaded in
        # FUNCTION Get_Data. Download if so, ignore if not
        if SampleEventID in SmpEvntIDs_dl:
            attachName = '%s__%s' % (StationID, SampleEventID)
            # 'i' and 'dupList' are used in the event that there are
            #  multiple photos with the same StationID and SampleEventID.  If they
            #  do have the same attributes as an already saved attachment, the letter
            #  suffix at the end of the attachment name will increment to the next
            #  letter.  Ex: if there are two SDR-100__9876, the first will always be
            #  named 'SDR-1007__9876_A.jpg', the second will be 'SDR-1007__9876_B'
            i = 0
            dupList = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            attachPath = gaFolder + '\\' + attachName + '_' + dupList[i] + '.jpg'

            # Test to see if the attachPath currently exists
            while os.path.exists(attachPath):
                # The path does exist, so go through the dupList until a 'new' path is found
                i += 1
                attachPath = gaFolder + '\\' + attachName + '_' + dupList[i] + '.jpg'

                # Test the new path to see if it exists.  If it doesn't exist, break out
                # of the while loop to save the image to that new path
                if not os.path.exists(attachPath):
                    break

            # Only download the attachment if the picture is from A - G
            # 'H' is a catch if there are more than 7 photos with the same Station ID
            # and Sample Event ID, shouldn't be more than 7 so an 'H' pic is passed.
            if (dupList[i] != 'H'):
                # Get the token to download the attachment
                gaValues = {'token' : token }
                gaData = urllib.urlencode(gaValues)

                # Get the attachment and save as attachPath
                print '    Saving %s' % attachName
                attachment_dl = True

                attachmentUrl = attachment['url']
                urllib.urlretrieve(url=attachmentUrl, filename=attachPath,data=gaData)

            else:
                print '  WARNING.  There were more than 7 pictures with the same Station ID and Sample Event ID. Picture not saved.'

    if (attachment_dl == False):
        print '    No attachments saved this run.  OK if no attachments submitted since last run.'

    print '  All attachments can be found at: %s' % gaFolder

    # Delete the JSON file since it is no longer needed.
    print '  Deleting JSON file'
    os.remove(jsonFilePath)

    print 'Successfully got attachments.\n'

    return gaFolder

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                               Function Email_W_Body()
def Email_W_Body(subj, body, email_list, cfgFile=
    r"P:\DPW_ScienceAndMonitoring\Scripts\DEV\DEV_branch\Control_Files\accounts.txt"):

    """
    PARAMETERS:
      subj (str): Subject of the email
      body (str): Body of the email in HTML.  Can be a simple string, but you
        can use HTML markup like <b>bold</b>, <i>italic</i>, <br>carriage return
        <h1>Header 1</h1>, etc.
      email_list (str): List of strings that contains the email addresses to
        send the email to.
      cfgFile {str}: Path to a config file with username and password.
        The format of the config file should be as below with
        <username> and <password> completed:

          [email]
          usr: <username>
          pwd: <password>

        OPTIONAL. A default will be used if one isn't given.

    RETURNS:
      None

    FUNCTION: To send an email to the listed recipients.
      If you want to provide a log file to include in the body of the email,
      please use function Email_w_LogFile()
    """
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import ConfigParser, smtplib

    print '\n  Starting Email_W_Body()'
    print '    With Subject: {}'.format(subj)

    # Set the subj, From, To, and body
    msg = MIMEMultipart()
    msg['Subject']   = subj
    msg['From']      = "Python Script"
    msg['To']        = ', '.join(email_list)  # Join each item in list with a ', '
    msg.attach(MIMEText(body, 'html'))

    # Get username and password from cfgFile
    config = ConfigParser.ConfigParser()
    config.read(cfgFile)
    email_usr = config.get('email', 'usr')
    email_pwd = config.get('email', 'pwd')

    # Send the email
    ##print '  Sending the email to:  {}'.format(', '.join(email_list))
    SMTP_obj = smtplib.SMTP('smtp.gmail.com',587)
    SMTP_obj.starttls()
    SMTP_obj.login(email_usr, email_pwd)
    SMTP_obj.sendmail(email_usr, email_list, msg.as_string())
    SMTP_obj.quit()
    time.sleep(2)

    print '  Successfully emailed results.\n'

#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
