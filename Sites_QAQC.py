#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     24/10/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
def main():

    sites_CURRENT = r'X:\week\Homeless_Activity_CURRENT.gdb\Sites'
    visits_CURRENT = r'X:\week\Homeless_Activity_CURRENT.gdb\Visits'
    email_admin_ls = ['michael.grue@sdcounty.ca.gov']
    cfgFile = r"U:\yakos\hep_A\PROD\Environment_B\Scripts_B\Source_Code\config_file.ini"
    name_of_script = 'Sites_QAQC.py'
    success = True
    # TODO: Get this script into the Processing data script

    try:
        #-----------------------------------------------------------------------
        #                 Start QA/QC Downloaded Data Section
        #-----------------------------------------------------------------------
        # Check for any duplicate Site Numbers in the Sites database
        all_unique_values = Check_For_Unique_Values(sites_CURRENT, 'Site_Number', email_admin_ls, cfgFile)

        # Check for any Site Numbers in the Visit database that are not in the Site database
        Check_For_Missing_Values(visits_CURRENT, sites_CURRENT, 'Site_Number', 'Site_Number', email_admin_ls, cfgFile)

        # Compare Site_Status, Cleanup_Recommended between Sites and Visits
        success = Compare_Fields(sites_CURRENT, visits_CURRENT, email_admin_ls, cfgFile)

        # Get Last_Cleaning_Date
        all_unique_values = True
        if all_unique_values:  # Only calculate the fields if there were all_unique_values
            success = Calc_Fields(sites_CURRENT, visits_CURRENT, email_admin_ls, cfgFile)
        else:
            success = False
            print 'Fields were not calculated since there were duplicate Site Numbers in the Sites database.'
            print 'Fix the duplicate errors, then rerun this script.'

    except Exception as e:
        success = False
        print 'ERROR with QA/QC Downloaded Data section'
        print str(e)

        #-----------------------------------------------------------------------
        #                 End QA/QC Downloaded Data Section
        #-----------------------------------------------------------------------

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
        print '  There were NO duplicate values'

    print 'Finished Check_For_Unique_Values()'
    print '------------------------------------------------------------------\n'

    return all_unique_values

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       Function Check_For_Missing_Values()
def Check_For_Missing_Values(target_table, table_to_check, target_field, check_field, email_list, cfgFile):
    """
    PARAMETERS:
      target_table (str): Table to get the values to check.
      table_to_check (str): Table to perform the check on.
      target_field (str): Name of the field in the target_table to check.
      check_field (str): Name of the field in the table_to_check to perform the
        check on.
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

    print '  Getting list of unique values in the Target Table'
    unique_values = []
    with arcpy.da.SearchCursor(target_table, [target_field]) as target_cursor:
        for row in target_cursor:
            value = row[0]
            if value not in unique_values:
                unique_values.append(value)

    print '  Getting list of values in Target Table that are not in Table To Check'
    missing_values = []
    with arcpy.da.SearchCursor(table_to_check, [check_field]) as check_cursor:
        for row in check_cursor:
            value = row[0]
            if value not in unique_values:
                missing_values.append(str(value))

    if len(missing_values) > 0:
        print '  There were values in Target Table field: "{}" that are not in Table To Check field: "{}"'.format(target_field, check_field)
        for m_val in missing_values:
            print '    {}'.format(m_val)

        missing_values_str = '<br>'.join(missing_values)

        subj = 'WARNING!  There were missing values in {}.'.format(check_field)
        body = """In field: "{}"<br>
                  In table: "{}"<br>
                  There were missing values:<br><br>
                  {}<br><br>
                  <b>This happens if there is a Site Number for a Visit that is not in
                  the Sites database.</b><br>
                  It is possible that an incorrect Site Number
                  was entered for a visit.  OR that a Site is missing its Site Number.
                  Or that a Site has not yet been entered into the Sites database.
                  Please log onto AGOL and make the appropriate changes.
        """.format(check_field, table_to_check, missing_values_str)

        Email_W_Body(subj, body, email_list, cfgFile)

    else:
        print '  There were NO missing values in the Table To Check'

    print 'Finished Check_For_Missing_Values()'
    print '------------------------------------------------------------------\n'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Compare_Fields(sites_CURRENT, visits_CURRENT, email_list, cfgFile):
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
      To compare fields in the Sites database with the Visits database and
      send a warning email letting LUEG-GIS admin know that there are Sites
      and Visits with conflicting information for the Sites database and the
      MOST RECENT VISIT in the Visits database.  These errors probably mean that
      the Sites database in AGOL needs to be updated with info from the most
      recent visit.

      1) Compare [Site_Status] field.
      2) Compare [Cleanup_Recommended] field.
      3) Send warning emails if either 1 or 2 above had mismatched values.
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
            visits_sql_clause = (None, 'ORDER BY Date_Of_Visit DESC')  # We want to order by the user defined date (most recent first)
            with arcpy.da.SearchCursor(visits_CURRENT, ['Site_Number', 'Date_Of_Visit', 'Site_Status_Visit'], where_clause, '', '', visits_sql_clause) as visits_search_cur:
                try:
                    v_row = next(visits_search_cur)  # We only want the first record in the visits_search_cur since this is the most recent visit
                    date_of_visit    = v_row[1]
                    site_stat_visit = v_row[2]
                    del v_row

                    print '    Site Status Collector: {}'.format(site_stat_col)
                    print '    Site Status Survey123: {}'.format(site_stat_visit)
                    print '       Date of Last Visit: {}'.format(date_of_visit)

                    if site_stat_col != site_stat_visit:
                        print '  ***  Site Status not the same! ***'
                        mismatched_site_status.append('Site: "<b>{}</b>" has a Site Status of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, site_stat_col, site_stat_visit))

                except StopIteration:  # StopIteration thrown if the search cursor has no next() because there are 0 visits for that site.  Not actually an error.
                    print '  No visits for that site.  Can\'t compare, but not necessarily an error.'
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
            visits_sql_clause = (None, 'ORDER BY Date_Of_Visit DESC')  # We want to order by the user defined date (most recent first)
            with arcpy.da.SearchCursor(visits_CURRENT, ['Site_Number', 'Date_Of_Visit', 'Cleanup_Recommended_Visit'], where_clause, '', '', visits_sql_clause) as visits_search_cur:
                try:
                    v_row = next(visits_search_cur)  # We only want the first record in the visits_search_cur since this is the most recent visit
                    date_of_visit     = v_row[1]
                    cleanup_rec_visit = v_row[2]
                    del v_row

                    print '    Cleanup Recommended Collector: {}'.format(cleanup_rec_col)
                    print '    Cleanup Recommended Survey123: {}'.format(cleanup_rec_visit)
                    print '               Date of Last Visit: {}'.format(date_of_visit)

                    if cleanup_rec_col != cleanup_rec_visit:
                        print '  ***  Cleanup Recommended not the same! ***'
                        mismatched_cleanup_rec.append('Site: "<b>{}</b>" has a Cleanup Recommended of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, cleanup_rec_col, cleanup_rec_visit))

                except StopIteration:  # StopIteration thrown if the search cursor has no next() because there are 0 visits for that site.  Not actually an error.
                    print '  No visits for that site.  Can\'t compare, but not necessarily an error.'
                except Exception as e:  # This error may be an actual error.
                    success = False
                    print '*** ERROR with Comparing this Sites Cleanup_Recommended ***'
                    print str(e)

            del visits_search_cur
            print '\n  ---------------------'

    del sites_search_cur


    #-----------------------------------------------------------------------
    #                     Send Compare Warning Emails

    # Send an email if there were any mismatched Site Statuses
    if len(mismatched_site_status) > 0:

        mismatched_site_status_str = '<br>'.join(mismatched_site_status)

        subj = 'WARNING.  There were mismatched Site Statuses.'
        body = """Below is a list of sites that have a different <u>Site Status</u>
        in Collector and in the most recent visit for that site in Survey123.<br>
        Please go into the appropriate database to make the corrections:<br><br>
        {}""".format(mismatched_site_status_str)

        Email_W_Body(subj, body, email_list, cfgFile)


    # Send an email if there were any mismatched Cleanup Recommended
    if len(mismatched_cleanup_rec) > 0:

        mismatched_cleanup_rec_str = '<br>'.join(mismatched_cleanup_rec)

        subj = 'WARNING.  There were mismatched Cleanup Recommended.'
        body = """Below is a list of sites that have a different <u>Cleanup Recommended</u>
        in Collector and in the most recent visit for that site in Survey123.<br>
        Please go into the appropriate database to make the corrections:<br><br>
        {}""".format(mismatched_cleanup_rec_str)

        Email_W_Body(subj, body, email_list, cfgFile)

    print '  Success within this function: {}'.format(success)
    print 'Finished Compare_Fields()'
    print '------------------------------------------------------------------\n'

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
        in_table = os.path.join(wkg_folder, current_FGDB, 'Sites')
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
            visits_sql_clause = (None, 'ORDER BY Date_Of_Visit DESC')  # We want to order by the user defined date (most recent first)
            perform_calc = True

            with arcpy.da.SearchCursor(visits_CURRENT, ['Site_Number', 'Date_Of_Visit', 'Reason_For_Visit'], where_clause, '', '', visits_sql_clause) as visits_search_cur:
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
    print '    Subject: {}'.format(subj)

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

    print '  Finished Email_W_Body().\n'


if __name__ == '__main__':
    main()
