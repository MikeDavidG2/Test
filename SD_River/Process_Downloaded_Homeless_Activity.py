#-------------------------------------------------------------------------------
# Purpose:
"""
To process the just recently downloaded Homeless Activity Data
"""
#
# Author:      mgrue
#
# Created:     10/13/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# TODO: Update the script Purpose above to be more accurate.

import arcpy, sys, datetime, os, ConfigParser
arcpy.env.overwriteOutput = True

def main():

    #---------------------------------------------------------------------------
    #                     Set Variables that will change
    #---------------------------------------------------------------------------

    # Name of this script
    name_of_script = 'Process_Downloaded_Homeless_Activity'

    # Set the path prefix depending on if this script is called manually by a
    #  user, or called by a scheduled task on ATLANTIC server.
    called_by = arcpy.GetParameterAsText(0)

    if called_by == 'MANUAL':
        path_prefix = 'U:'
        ask_to_update = True  # This var controls if the script asks the user if we want to update the CURRENT FGDB

    elif called_by == 'SCHEDULED':
        path_prefix = 'D:\users'
        ask_to_update = False  # We don't want to ask the server this question, assume we want to run the update
        run_update = 'y'  # Run the Update_CURRENT_FGDB() function automatically

    else:  # If script run directly w/o a batch file
        path_prefix = 'U:'
        ask_to_update = True

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
    wkg_folder       = r'{}\yakos\hep_A\PROD\Environment_B\Data_B'.format(path_prefix)
    current_FGDB     = 'Homeless_Activity_CURRENT.gdb'  # Name of the "CURRENT" FGDB

    # Get list of Feature Service Names
    FS_names       = config.get('Download_Info', 'FS_names')
    FS_names_ls    = FS_names.split(', ')
    collector_sites_fs_name = FS_names_ls[1]

    # Get list of FS indexes
    FS_indexes     = config.get('Download_Info', 'FS_indexes')
    FS_indexes_ls  = FS_indexes.split(', ')
    collector_sites_fs_index = FS_indexes_ls[1]

    # Get list of names of the existing FGDB's
    FGDB_names     = config.get('Download_Info', 'FGDB_names')
    FGDB_names_ls  = FGDB_names.split(', ')

    # Get list of names of the FC's
    FC_names       = config.get('Download_Info', 'FC_names')
    FC_names_ls    = FC_names.split(', ')

    # List of Site Numbers in the Visits database that we should ignore in the
    # Check_For_Missing_Values().  We would ignore these sites because there
    # could be Visits to sites in the past for sites that were later deleted
    # in the Sites database (and we do not want to get Warning emails for these)
    # Enter these as an integer, NOT as a string
    missing_sites_to_ignore = [10, 20, 40, 42, 91]

    # Set the Email variables
    email_admin_ls = ['michael.grue@sdcounty.ca.gov', 'randy.yakos@sdcounty.ca.gov', 'gary.ross@sdcounty.ca.gov']
    ##email_admin_ls = ['michael.grue@sdcounty.ca.gov']  # For testing purposes

    #---------------------------------------------------------------------------
    #                Set Variables that will probably not change

    # Flag to control if there is an error
    success = True

    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Calling Functions

    # Turn all 'print' statements into a log-writing object
    if success == True:
        try:
            orig_stdout, log_file_date = Write_Print_To_Log(log_file, name_of_script)
        except Exception as e:
            success = False
            print '*** ERROR with Write_Print_To_Log() ***'
            print str(e)

    if ask_to_update == True:
       run_update = (raw_input('Do you want to update the CURRENT FGDB? (y/n)\n  Enter "n" if you want to skip the update portion of this script.')).lower()
       print run_update

    # Update the CURRENT FGDB with data from the FGDBs holding all the recently downloaded AGOL data
    if (success == True) and (run_update == 'y'):
        try:
            success = Update_CURRENT_FGDB(wkg_folder, FGDB_names_ls, FC_names_ls, current_FGDB, email_admin_ls, cfgFile)

        except Exception as e:
            success = False
            print '*** ERROR with Update_CURRENT_FGDB() ***'
            print str(e)

    #---------------------------------------------------------------------------
    #                    Start QA/QC Downloaded Data Section
    #---------------------------------------------------------------------------
    if success == True:
        try:
            sites_CURRENT  = os.path.join(wkg_folder, current_FGDB, 'Sites')
            visits_CURRENT = os.path.join(wkg_folder, current_FGDB, 'Visits')

            # Check for any duplicate Site Numbers in the Sites database
            all_unique_values = Check_For_Unique_Values(sites_CURRENT, 'Site_Number', email_admin_ls, cfgFile)

            # Check for any Site Numbers in the Visit database that are not in the Site database
            Check_For_Missing_Values(visits_CURRENT, sites_CURRENT, 'Site_Number', 'Site_Number', missing_sites_to_ignore, email_admin_ls, cfgFile)

            # Compare [Site_Status] and [Cleanup_Recommended] between Sites and Visits
            token = AGOL_Get_Token(cfgFile)
            success = Compare_Fields(sites_CURRENT, visits_CURRENT, email_admin_ls, cfgFile, collector_sites_fs_name, collector_sites_fs_index, token)

            # Calculate Last_Cleaning_Date
            # Only calculate the fields if all_unique_values = 'True' and success = 'True'
            if all_unique_values and success:
                success = Calc_Fields(sites_CURRENT, visits_CURRENT, email_admin_ls, cfgFile)
            else:
                print 'Fields were not calculated since there were:'
                if all_unique_values == False:
                    print '  1) Duplicate Site Numbers in the Sites database (all_unique_values = "False")'
                if success == False:
                    print '  2) There were errors with the script above (success = "False")'

                print '  Fix the errors, then rerun this script.'

        except Exception as e:
            success = False
            print 'ERROR with QA/QC Downloaded Data section'
            print str(e)
    #---------------------------------------------------------------------------
    #                   End QA/QC Downloaded Data Section
    #---------------------------------------------------------------------------

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
#                       FUNCTION Update_CURRENT_FGDB()
def Update_CURRENT_FGDB(wkg_folder, FGDB_names_ls, FC_names_ls, current_FGDB, email_list, cfgFile):
    """
    RETURNS:
      all_data_updated (boolean): Flag that is 'True' if all attempts to update
        the CURRENT FGDB were successful.  It is 'False' if even one attempt was
        unsuccessful.

    FUNCTION:
      To update the CURRENT FGDB with the most up-to-date FC in each updated FGDB
      from the AGOL database
    """

    print 'Starting Update_CURRENT_FGDB()'

    all_data_updated = True

    date_and_time = Get_DT_To_Append()
    today = date_and_time.split('__')[0]  # Get the YYYY_MM_DD format
    print '  Today is: "{}"'.format(today)
    print '\n  ----------------------------------------------------------------'

    # Check each FGDB that could have had recent data added to it
    for count, FGDB_name in enumerate (FGDB_names_ls):
        updated = False
        FGDB_path = os.path.join(wkg_folder, FGDB_name)

        print '  Checking for new data that has the date "{}" in:\n    "{}"\n'.format(today, FGDB_path)
        arcpy.env.workspace = FGDB_path
        fc_list = arcpy.ListFeatureClasses()

        # Check each FC in the FGDB to see when the data was downloaded
        # If the download date is equal to today, send that FC to the CURRENT database
        for fc in fc_list:
            date_downloaded = (fc.split('__')[0])[-10:]  # Get the YYYY_MM_DD format
            if date_downloaded == today:
                updated = True
                in_fc = os.path.join(FGDB_path, fc)
                out_fc = os.path.join(wkg_folder, current_FGDB, FC_names_ls[count])
                print '  Copying Features from: "{}"'.format(in_fc)
                print '                     To: "{}"\n'.format(out_fc)
                arcpy.CopyFeatures_management(in_fc, out_fc)

                #---------------------------------------------------------------
                #         Create a table with the date and time the
                #       FC added to CURRENT.gdb was downloaded from AGOL

                # Delete existing table
                try:
                    arcpy.env.workspace = os.path.join(wkg_folder, current_FGDB)
                    existing_table = arcpy.ListTables('{}*'.format(FC_names_ls[count]))[0]  # Use the wildcard to limit results to one table that starts with the FC name
                    print '  Deleting existing Table: {}\n'.format(existing_table)
                    arcpy.Delete_management(existing_table)
                except Exception as e:
                    print '  WARNING, existing table was not deleted, may not exist.\n'


                # Get the Date and Time the newest FC was downloaded
                date_time_downloaded = fc[-20:]

                # Set attributes
                out_path = os.path.join(wkg_folder, current_FGDB)
                table_name = FC_names_ls[count] + '_UPDT_' + date_time_downloaded

                print '  Creating table at: "{}"'.format(out_path)
                print '          With name: "{}"\n'.format(table_name)
                arcpy.CreateTable_management(out_path, table_name)

        if updated == True:
            print '  Updated CURRENT database from: {}'.format(FGDB_name)

        else:
            all_data_updated = False
            print '  WARNING! There was no newly downloaded data in "{}" with date "{}" to update the Homeless_Activity_CURRENT.gdb'.format(FGDB_name, today)

            # Send a warning email
            subj = 'WARNING with Process_Downloaded_Homeless_Activity.py'
            body = """ The Homeless_Activity_Current.gdb was not updated from
            <b>{}</b>.<br>
            This is because there was no FC with todays date ({}) in the above mentioned daily download FGDB,
            but there should have been.  Please investigate.""".format(FGDB_name, today)

            Email_W_Body(subj, body, email_list, cfgFile)

        print '  ------------------------------------------------------------\n'

    print '  All data was updated successfully: "{}"'.format(all_data_updated)
    print 'Finished Update_CURRENT_FGDB()'
    print '------------------------------------------------------------------\n'

    return all_data_updated

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         Function Check_For_Unique_Values
def Check_For_Unique_Values(table, field, email_list, cfgFile):
    """
    PARAMETERS:
      table (str): Full path to a FC or Table in a FGDB
      field (str): Name of a field in the above 'table'
      email_list(str): List of email addresses
      cfgFile (str): Path to a config file (.txt or .ini) with format:
        [email]
        usr: <username>
        pwd: <password>

    RETURNS:
      all_unique_values (boolean): 'True' if all the values in the specified field
        are unique.  'False' if there is at least one duplicate.

    FUNCTION:
      To check a field in a table and see if there are any duplicate values in
      that field.
    """

    print 'Starting Check_For_Unique_Values()'
    print '  Checking field: "{}" in table: "{}"'.format(field, table)

    unique_values    = []
    duplicate_values = []
    all_unique_values = True

    with arcpy.da.SearchCursor(table, [field]) as cursor:
        for row in cursor:
            value = row[0]
            if value not in unique_values:
                unique_values.append(value)
            else:
                duplicate_values.append(str(value))
                all_unique_values = False

    # If there were any duplicates, print them out and send a warning email
    if len(duplicate_values) > 0:
        print '  There were duplicate values:'
        for duplicate_value in duplicate_values:
            print '    {}'.format(duplicate_value)

        duplicate_values_str = '<br>'.join(duplicate_values)

        subj = 'WARNING! There were duplicate values in {}'.format(field)
        body = """In field: "{}"<br>
                  In table: "{}"<br>
                  There were duplicate values:<br><br>
                  {}<br><br>
                  Please log onto AGOL and make sure that each site has a correct and unique Site Number.
        """.format(field, table, duplicate_values_str)

        Email_W_Body(subj, body, email_list, cfgFile)

    else:
        print '  There were NO duplicate values.\n  No WARNING email needed.'

    print 'Finished Check_For_Unique_Values()'
    print '------------------------------------------------------------------\n'

    return all_unique_values

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       Function Check_For_Missing_Values()
def Check_For_Missing_Values(target_table, table_to_check, target_field, check_field, missing_sites_to_ignore, email_list, cfgFile):
    """
    PARAMETERS:
      target_table (str): Table to get the values to check.
      table_to_check (str): Table to perform the check on.
      target_field (str): Name of the field in the target_table to check.
      check_field (str): Name of the field in the table_to_check to perform the
        check on.
      missing_sites_to_ignore (str): List of Site Numbers in the Visits database
        that we should ignore in this function.  We would
        ignore these sites because there could be Visits to sites in the past
        for sites that were later deleted in the Sites database (and we do not
        want to get Warning emails for these).
      email_list(str): List of email addresses
      cfgFile (str): Path to a config file (.txt or .ini) with format:
        [email]
        usr: <username>
        pwd: <password>

    RETURNS:
      None

    FUNCTION:
      To check for any missing values from one field in one table when compared
      to a target table/field.  Sends an email if there are missing values
      in the table_to_check.
    """
    print 'Starting Check_For_Missing_Values()'
    print '  Target Table   = {}'.format(target_table)
    print '  Table To Check = {}'.format(table_to_check)
    print '  Target Field   = {}'.format(target_field)
    print '  Check Field    = {}'.format(check_field)
    if len(missing_sites_to_ignore) > 0:
        print '  Site Numbers in the Visit database to ignore:'
        for num in missing_sites_to_ignore:
            print '    {}'.format(str(num))
    print ''

    # Get list of unique values in the Table To Check
    print '  Getting list of unique values in the Table To Check'
    unique_values = []
    with arcpy.da.SearchCursor(table_to_check, [check_field]) as check_cursor:
        for row in check_cursor:
            value = row[0]
            if value not in unique_values:
                unique_values.append(value)

    del row, check_cursor
    unique_values.sort()
    ##print unique_values

    # Get list of values that ARE in Target Table that are NOT in Table To Check
    print '  Getting list of values in Target Table that are not in Table To Check'
    missing_values = []
    with arcpy.da.SearchCursor(target_table, [target_field]) as target_cursor:
        for row in target_cursor:
            value = row[0]
            if (value not in unique_values) and (value not in missing_sites_to_ignore) and (str(value) not in missing_values):
                missing_values.append(str(value))

    del row, target_cursor
    missing_values.sort()
    ##print missing_values

    if len(missing_values) > 0:  # Then there were missing values
        print '  There were values in Target Table that are not in Table To Check'
        for m_val in missing_values:
            print '    {}'.format(m_val)

        print '\n  Sending Warning Email...\n'

        missing_values_str = '<br>'.join(missing_values)

        subj = 'WARNING!  There were missing values in {}.'.format(check_field)
        body = """In field: "{}"<br>
                  In the CURRENT FGDB, Feature Class: "{}"<br>
                  There were missing values:<br><br>
                  <b>{}</b><br><br>
                  <b>This happens if there is a Site Number for a Visit that is not in
                  the Sites database.</b><br>
                  It is possible that an incorrect Site Number was entered for a visit.<br>
                  OR that a Site is missing its Site Number.<br>
                  OR that a Site has not yet been entered into the Sites database.<br>
                  Please log onto AGOL and make the appropriate changes.<br><br>
                  If there is a site that has been deleted in the Sites database,
                  you can add that site number to the "missing_sites_to_ignore"
                  list that is in the script.  Any value in this list will not
                  be considered a "Missing Value".
        """.format(check_field, os.path.basename(table_to_check), missing_values_str)

        Email_W_Body(subj, body, email_list, cfgFile)

    else:
        print '  There were NO missing values in the Table To Check.  No Warning email needed.'

    print 'Finished Check_For_Missing_Values()'
    print '------------------------------------------------------------------\n'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION:    Get AGOL token
def AGOL_Get_Token(cfgFile, gtURL="https://www.arcgis.com/sharing/rest/generateToken"):
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
def Compare_Fields(sites_CURRENT, visits_CURRENT, email_admin_ls, cfgFile, collector_sites_fs_name, collector_sites_fs_index, token):
    """
    PARAMETERS:
      sites_CURRENT (str): Full path to the Sites database in the CURRENT FGDB.
      visits_CURRENT (str): Full path to the Visits database in the CURRENT FGDB.
      email_list (str): List of emails to send any warning emails to.
      cfgFile (str): Path to a config file (.txt or .ini) with format:
        [email]
        usr: <username>
        pwd: <password>
      collector_sites_fs_name (str): The name of the Feature Service in
        Collector that we want to update if the [Site_Status] and
        [Cleanup_Recommended] conflict with the values in Survey123
        (do not include things like
        "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services",
        just the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      collector_sites_fs_index (str): The index of the layer in the Feature
        Service in Collector we want to update. This will frequently be 0,
        but it could be a higer number if the FS has multiple layers in it.
      token (str): Token from AGOL that gives permission to interact with
        data stored on AGOL servers.  Obtained from the Get_Token().

    RETURNS:
      success (boolean): 'True' if there were no errors.  'False' if there were.

    FUNCTION:
      To compare fields in the Sites database with the Visits database and
      update the data in Collector with the most recent visit from Survey123.
      If this cannot be accomplished, it will send a warning email letting
      LUEG-GIS admin know that there are Sites and Visits with conflicting
      information for the Sites database and the MOST RECENT VISIT in the Visits
      database.  These errors probably mean that the Sites database in AGOL
      needs to be updated with info from the most recent visit.

      PROCESS:
      1)   Compare [Site_Status] field.
      1.1)   Update the field in Collector with the value from Survey123

      2)   Compare [Cleanup_Recommended] field.
      2.1)   Update the field in Collector with the value from Survey123

      3)   Send warning emails if the value in Survey123 was 'None' OR if the
           update was not successful.
    """

    print 'Starting Compare_Fields()'
    success = True

    # Create lists to hold errors
    mismatched_site_status = []
    mismatched_cleanup_rec = []

    # Perform this comparison for each Site_Number in the Sites Database
    sites_sql_clause = (None, 'ORDER BY Site_Number')  # Order by Site_Number in ascending order
    with arcpy.da.SearchCursor(sites_CURRENT, ['Site_Number', 'Site_Status_Collector', 'Cleanup_Recommended_Collector'], '', '', '', sites_sql_clause) as sites_search_cur:
        for s_row in sites_search_cur:
            site_num_col            = s_row[0]
            site_stat_col           = s_row[1]
            cleanup_rec_col         = s_row[2]
            print '  Site Number: {}'.format(site_num_col)

            #---------------------------------------------------------------
            #                        Compare Site_Status

            # For each site get the most recent visit and its Site Status (for that visit)
            # If the Site Statuses do not match between Collector and Survey123,
            #   append the information to a list so that an email can formatted
            #   and sent.
            where_clause = 'Site_Number = {}'.format(site_num_col)  # We only want to look at visits with the same site number we are analyzing
            visits_sql_clause = (None, 'ORDER BY Date_Of_Visit DESC, OBJECTID DESC')  # We want to order by the user defined date (most recent first)
            with arcpy.da.SearchCursor(visits_CURRENT, ['Site_Number', 'Date_Of_Visit', 'Site_Status_Visit', 'OBJECTID'], where_clause, '', '', visits_sql_clause) as visits_search_cur:
                try:
                    v_row = next(visits_search_cur)  # We only want the first record in the visits_search_cur since this is the most recent visit
                    date_of_visit    = v_row[1]
                    site_stat_visit = v_row[2]
                    del v_row

                    # Update the Feature in Collector with the value from Survey123
                    if (site_stat_col != site_stat_visit) and (site_stat_visit != 'None'):  # MG 12/29/17: We only want to change Collector value if there is a non-'None' value in Survey123
                        print '  ***  Site Status not the same! ***'
                        print '    Site Status Collector: {}'.format(site_stat_col)
                        print '    Site Status Survey123: {}'.format(site_stat_visit)
                        print '       Date of Last Visit: {}'.format(date_of_visit)
                        print '    Changing the Site Status in Collector to match Survey123:'

                        # Get the OBJECTID in the AGOL Feature Service of the feature to be updated
                        object_id = AGOL_Get_Object_Ids_Where(collector_sites_fs_name, collector_sites_fs_index, where_clause, token)

                        # Update the Feature in Collector with the new value from Survey123
                        if len(object_id) == 1:
                            field_to_update = 'Site_Status_Collector'
                            new_value       = site_stat_visit
                            feature_updated = AGOL_Update_Features(collector_sites_fs_name, collector_sites_fs_index, object_id, field_to_update, new_value, token)

                            if feature_updated == False:  # Then the feature was not updated in AGOL and we need to add the feature to the warning email
                                print '*** WARNING ***'
                                print '    The Feature was not updated on AGOL, adding this site to the list for human analysis, will be inclucded in the email'
                                mismatched_site_status.append('Site: "<b>{}</b>" has a Site Status of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, site_stat_col, site_stat_visit))

                        else:  # Then there was not one object_id returned by AGOL_Get_Object_Ids_Where(), so add the feature to the warning email
                            print '*** WARNING ***'
                            print '    The number of OBJECTIDs returned by AGOL_Get_Object_Ids_Where() should be: 1, but it was: {}'.format(len(object_id))
                            print '    The feature on AGOL was not updated, adding this site to the list for human analysis, will be included in the email'
                            mismatched_site_status.append('Site: "<b>{}</b>" has a Site Status of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, site_stat_col, site_stat_visit))

                    # Add formatted string to list to be emailed
                    elif (site_stat_col != site_stat_visit) and (site_stat_visit == 'None'):  # MG 12/29/17: We only want an email if there is a 'None' value in Survey123.
                        print '  ***  Site Status not the same! ***'
                        print '    Site Status Collector: {}'.format(site_stat_col)
                        print '    Site Status Survey123: {}'.format(site_stat_visit)
                        print '       Date of Last Visit: {}'.format(date_of_visit)
                        print '    Adding this site to the list for human analysis, will be included in the email.'
                        mismatched_site_status.append('Site: "<b>{}</b>" has a Site Status of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, site_stat_col, site_stat_visit))
                    else:
                        print '    Same Site Status'

                except StopIteration:  # StopIteration thrown if the search cursor has no next() because there are 0 visits for that site.  Not actually an error.
                    print '    No visits for that site.  Can\'t compare, but not necessarily an error.'
                except Exception as e:  # This error may be an actual error.
                    success = False
                    print '*** ERROR with Comparing this Sites Site_Status ***'
                    print str(e)

            del visits_search_cur
            print ''

            #---------------------------------------------------------------
            #                 Compare Cleanup_Recommended

            # For each site get the most recent visit and its Cleanup_Recommended (for that visit)
            # If the Cleanup_Recommended do not match between Collector and Survey123,
            #   append the information to a list so that an email can formatted
            #   and sent.
            where_clause = 'Site_Number = {}'.format(site_num_col)  # We only want to look at visits with the same site number we are analyzing
            visits_sql_clause = (None, 'ORDER BY Date_Of_Visit DESC, OBJECTID DESC')  # We want to order by the user defined date (most recent first)
            with arcpy.da.SearchCursor(visits_CURRENT, ['Site_Number', 'Date_Of_Visit', 'Cleanup_Recommended_Visit', 'OBJECTID'], where_clause, '', '', visits_sql_clause) as visits_search_cur:
                try:
                    v_row = next(visits_search_cur)  # We only want the first record in the visits_search_cur since this is the most recent visit
                    date_of_visit     = v_row[1]
                    cleanup_rec_visit = v_row[2]
                    del v_row

                    # Update the Feature in Collector with the value from Survey123
                    if (cleanup_rec_col != cleanup_rec_visit) and (cleanup_rec_visit != 'None'):  # MG 12/29/17: We only want to change Collector value if there is a non-'None' value in Survey123
                        print '  ***  Cleanup Recommended not the same! ***'
                        print '    Cleanup Recommended Collector: {}'.format(cleanup_rec_col)
                        print '    Cleanup Recommended Survey123: {}'.format(cleanup_rec_visit)
                        print '               Date of Last Visit: {}'.format(date_of_visit)
                        print '    Changing the Cleanup Recommended in Collector to match Survey123:'

                        # Get the OBJECTID in the AGOL Feature Service of the feature to be updated
                        object_id = AGOL_Get_Object_Ids_Where(collector_sites_fs_name, collector_sites_fs_index, where_clause, token)

                        # Update the Feature in Collector with the new value from Survey123
                        if len(object_id) == 1:
                            field_to_update = 'Cleanup_Recommended_Collector'
                            new_value       = cleanup_rec_visit
                            feature_updated = AGOL_Update_Features(collector_sites_fs_name, collector_sites_fs_index, object_id, field_to_update, new_value, token)

                            if feature_updated == False:  # Then the feature was not updated in AGOL and we need to add the feature to the warning email
                                print '*** WARNING ***'
                                print '    The Feature was not updated on AGOL, adding this site to the list for human analysis, will be inclucded in the email'
                                mismatched_cleanup_rec.append('Site: "<b>{}</b>" has a Cleanup Recommended of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, cleanup_rec_col, cleanup_rec_visit))

                        else:
                            print '*** WARNING ***'
                            print '    The number of OBJECTIDs returned by AGOL_Get_Object_Ids_Where() should be: 1, but it was: {}'.format(len(object_id))
                            print '    The feature on AGOL was not updated, adding this site to the list for human analysis, will be included in the email'
                            mismatched_cleanup_rec.append('Site: "<b>{}</b>" has a Cleanup Recommended of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, cleanup_rec_col, cleanup_rec_visit))

                    # Add formatted string to list to be emailed
                    elif (cleanup_rec_col != cleanup_rec_visit) and (cleanup_rec_visit == 'None'):  # MG 12/29/17 : We only want an email if there is a 'None' value in Survey123
                        print '  ***  Cleanup Recommended not the same! ***'
                        print '    Cleanup Recommended Collector: {}'.format(cleanup_rec_col)
                        print '    Cleanup Recommended Survey123: {}'.format(cleanup_rec_visit)
                        print '               Date of Last Visit: {}'.format(date_of_visit)
                        mismatched_cleanup_rec.append('Site: "<b>{}</b>" has a Cleanup Recommended of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, cleanup_rec_col, cleanup_rec_visit))
                    else:
                        print '    Same Cleanup Recommended'

                except StopIteration:  # StopIteration thrown if the search cursor has no next() because there are 0 visits for that site.  Not actually an error.
                    print '    No visits for that site.  Can\'t compare, but not necessarily an error.'
                except Exception as e:  # This error may be an actual error.
                    success = False
                    print '*** ERROR with Comparing this Sites Cleanup_Recommended ***'
                    print str(e)

            del visits_search_cur
            print '\n  ---------------------'

    del sites_search_cur


    #-----------------------------------------------------------------------
    #                     Send Compare Warning Emails

    print '  Analyzing if Warning emails need to be sent...'

    # Send an email if there were any mismatched Site Statuses
    if len(mismatched_site_status) > 0:
        print '    There were mismatched Site Statuses.  Sending Warning email.'

        mismatched_site_status_str = '<br>'.join(mismatched_site_status)

        subj = 'WARNING.  There were mismatched Site Statuses.'
        body = """Below is a list of sites that have a different <u>Site Status</u>
        in Collector and in the most recent visit for that site in Survey123.<br>
        Please go into the appropriate database to make the corrections:<br><br>
        {}""".format(mismatched_site_status_str)

        Email_W_Body(subj, body, email_list, cfgFile)

    else:
        print '    There were no mismatched Site Statuses.  No Warning email needed.'


    # Send an email if there were any mismatched Cleanup Recommended
    if len(mismatched_cleanup_rec) > 0:
        print '    There were mismatched Cleanup Recommended.  Sending Warning email.'

        mismatched_cleanup_rec_str = '<br>'.join(mismatched_cleanup_rec)

        subj = 'WARNING.  There were mismatched Cleanup Recommended.'
        body = """Below is a list of sites that have a different <u>Cleanup Recommended</u>
        in Collector and in the most recent visit for that site in Survey123.<br>
        Please go into the appropriate database to make the corrections:<br><br>
        {}""".format(mismatched_cleanup_rec_str)

        Email_W_Body(subj, body, email_list, cfgFile)

    else:
        print '    There were no mismatched Cleanup Recommended.  No Warning email needed.'

    print '\n  Success within this function: {}'.format(success)
    print 'Finished Compare_Fields()'
    print '------------------------------------------------------------------\n'

    return success

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def AGOL_Get_Object_Ids_Where(name_of_FS, index_of_layer_in_FS, where_clause, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      where_clause (str): Where clause. i.e.:
        where_clause = "FIELD_NAME = 'Value in field'"
      token (str): Obtained from the Get_Token()

    RETURNS:
      object_ids (list of str): List of OBJECTID's that satisfied the
      where_clause.

    FUNCTION:
      To get a list of the OBJECTID's of the features that satisfied the
      where clause.  This list will be the full list of all the records in the
      FS regardless of the number of the returned OBJECTID's or the max record
      count for the FS.

    NOTE: This function assumes that you have already gotten a token from the
    Get_Token() and are passing it to this function via the 'token' variable.
    """

    print '--------------------------------------------------------------------'
    print "      Starting Get_AGOL_Object_Ids_Where()"
    import urllib2, urllib, json

    # Create empty list to hold the OBJECTID's that satisfy the where clause
    object_ids = []

    # Encode the where_clause so it is readable by URL protocol (ie %27 = ' in URL).
    # visit http://meyerweb.com/eric/tools/dencoder to test URL encoding.
    where_encoded = urllib.quote(where_clause)

    # Set URLs
    query_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/query'.format(name_of_FS, index_of_layer_in_FS)
    query = '?where={}&returnIdsOnly=true&f=json&token={}'.format(where_encoded, token)
    get_object_id_url = query_url + query

    # Get the list of OBJECTID's that satisfied the where_clause

    print '        Getting list of OBJECTID\'s that satisfied the where clause for layer:\n    {}'.format(query_url)
    print '        Where clause: "{}"'.format(where_clause)
    response = urllib2.urlopen(get_object_id_url)
    response_json_obj = json.load(response)
    object_ids = response_json_obj['objectIds']

    if len(object_ids) > 0:
        print '        There are "{}" features that satisfied the query.'.format(len(object_ids))
        print '        OBJECTID\'s of those features:'
        for obj in object_ids:
            print '    {}'.format(obj)

    else:
        print '        No features satisfied the query.'

    print "      Finished Get_AGOL_Object_Ids_Where()\n"

    return object_ids

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                FUNCTION:    Update AGOL Features

def AGOL_Update_Features(name_of_FS, index_of_layer_in_FS, object_id, field_to_update, new_value, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      object_id (str or int): OBJECTID that should be updated.
      field_to_update (str): Field in the FS that should be updated.
      new_value (str or int): New value that should go into the field.  Data
        type depends on the data type of the field.
      token (str): Token from AGOL that gives permission to interact with
        data stored on AGOL servers.  Obtained from the Get_Token().

    RETURNS:
      success (boolean): 'True' if there were no errors.  'False' if there were.

    FUNCTION:
      To Update features on an AGOL Feature Service.
    """

    print '--------------------------------------------------------------------'
    print "Starting AGOL_Update_Features()"
    import urllib2, urllib, json

    success = True

    # Set the json upate
    features_json = {"attributes" : {"objectid" : object_id, "{}".format(field_to_update) : "{}".format(new_value)}}
    ##print 'features_json:  {}'.format(features_json)

    # Set URLs
    update_url       = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/updateFeatures?token={}'.format(name_of_FS, index_of_layer_in_FS, token)
    update_params    = urllib.urlencode({'Features': features_json, 'f':'json'})


    # Update the features
    print '  Updating Features in FS: {}'.format(name_of_FS)
    print '                 At index: {}'.format(index_of_layer_in_FS)
    print '   OBJECTID to be updated: {}'.format(object_id)
    print '      Field to be updated: {}'.format(field_to_update)
    print '   New value for updt fld: {}'.format(new_value)

    ##print update_url + update_params
    response  = urllib2.urlopen(update_url, update_params)
    response_json_obj = json.load(response)
    ##print response_json_obj

    for result in response_json_obj['updateResults']:
        ##print result
        print '    OBJECTID: {}'.format(result['objectId'])
        print '      Updated? {}'.format(result['success'])
        if result['success'] != 'True':
            success = False

    print 'Finished AGOL_Update_Features()\n'
    return success

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Calc_Fields(sites_CURRENT, visits_CURRENT, email_list, cfgFile):
    """
    PARAMETERS:
      sites_CURRENT (str): Full path to the Sites database in the CURRENT FGDB.
      visits_CURRENT (str): Full path to the Visits database in the CURRENT FGDB.
      email_list (str): List of emails to send any warning emails to.
      cfgFile (str): Path to a config file (.txt or .ini) with format:
        [email]
        usr: <username>
        pwd: <password>

    RETURNS:
      success (str): 'True' if there were no errors.  'False' if there were.

    FUNCTION:
      To calculate fields in the Sites database based off of information in the
      Visits database.

      1) Get the most recent date each site has been cleaned.
    """

    print 'Starting Calc_Fields()'
    print '  Sites database : {}'.format(sites_CURRENT)
    print '  Visits database: {}\n'.format(visits_CURRENT)
    success = True

    # Add Last_Cleaning_Date field to the Sites database
    try:
        in_table        = sites_CURRENT
        field_name      = 'Last_Cleaning_Date'
        field_type      = 'DATE'
        field_precision = ''
        field_scale     = ''
        field_length    = ''
        field_alias     = 'Last Cleaning Date'

        print '  Adding field: "{}"\n  To: {}'.format(field_name, in_table)
        arcpy.AddField_management(in_table, field_name, field_type, field_precision,
                                     field_scale, field_length, field_alias)

    except Exception as e:
        success = False
        print '*** ERROR with Add field: {} ***'.format(field_name)
        print '  This may happen if there is a permission problem because you are running this script MANUALLY,'
        print '  but the CURRENT FGDB was updated with the SCHEDULED process.  For some reason the server running'
        print '  the script makes it hard for a user to change the schema for FCs in this FGDB.'
        print '  Try to copy the FCs over manually from the Daily Download FGDBs, rename them, and give it another try with the MANUAL process'
        print '\nERROR MESSAGES:'
        print str(e)

    # Perform these calculations for each Site_Number in the Sites Database
    sites_sql_clause = (None, 'ORDER BY Site_Number')  # Order by Site_Number in ascending order
    with arcpy.da.SearchCursor(sites_CURRENT, ['Site_Number', 'Site_Status_Collector', 'Cleanup_Recommended_Collector'], '', '', '', sites_sql_clause) as sites_search_cur:
        for s_row in sites_search_cur:
            site_num_col            = s_row[0]
            site_stat_col           = s_row[1]
            cleanup_rec_col         = s_row[2]
            print '  Site Number: {}'.format(site_num_col)

            #---------------------------------------------------------------
            #         Get most recent date each site has been cleaned

            # For each site get the most recent visit (that had 'Site Cleaning' as the Reason_For_Visit)
            #   and get the Date_Of_Visit (for that visit)
            #   This date will be
            where_clause = "Site_Number = {} and Reason_For_Visit = 'Site Cleaning'".format(site_num_col)  # We only want to look at visits with the same site number we are analyzing
            visits_sql_clause = (None, 'ORDER BY Date_Of_Visit DESC, OBJECTID DESC')  # We want to order by the user defined date (most recent first)
            perform_calc = True

            with arcpy.da.SearchCursor(visits_CURRENT, ['Site_Number', 'Date_Of_Visit', 'Reason_For_Visit', 'OBJECTID'], where_clause, '', '', visits_sql_clause) as visits_search_cur:
                try:
                    v_row = next(visits_search_cur)  # We only want the first record in the visits_search_cur since this is the most recent visit
                    date_of_visit     = v_row[1]
                    del v_row
                    print '    Last Cleaning Date: {}'.format(date_of_visit)

                except StopIteration:
                    print '    No Last Cleaning Date for that site.  Can\'t calculate, but not necessarily an error.'
                    perform_calc = False
                except Exception as e:
                    success = False
                    print '*** ERROR with Getting Last Cleaning Date in Visits database ***'

                # Calc the field 'Last_Cleaning_Date' in the "Sites" data
                if perform_calc == True:
                    where_clause = "Site_Number = {}".format(site_num_col)
                    with arcpy.da.UpdateCursor(sites_CURRENT, ['Site_Number', 'Last_Cleaning_Date'], where_clause) as sites_updt_cur:
                        try:
                            s_edit_row = next(sites_updt_cur)
                            s_edit_row[1] = date_of_visit
                            sites_updt_cur.updateRow(s_edit_row)
                            print '      Input above date into Last_Cleaning_Date in Sites database'
                            del sites_updt_cur

                        except StopIteration:
                            print '    No record returned for sites_updt_cur.'

                        except Exception as e:
                            success = False
                            print '*** ERROR Calculating Last_Cleaning_Date ***'
                            print str(e)

            del visits_search_cur
            print '\n  ---------------------'

    del sites_search_cur

    print '  Success within this function: {}'.format(success)

    print 'Finished Calc_Fields()'
    print '------------------------------------------------------------------\n'

    return success

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
