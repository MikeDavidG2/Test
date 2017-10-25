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
    try:
        sites_CURRENT = r'U:\yakos\hep_A\PROD\Environment_B\Data\Homeless_Activity_CURRENT.gdb\Sites'
        visits_CURRENT = r'U:\yakos\hep_A\PROD\Environment_B\Data\Homeless_Activity_CURRENT.gdb\Visits'
        email_admin_ls = ['michael.grue@sdcounty.ca.gov']
        cfgFile = r"U:\yakos\hep_A\PROD\Scripts\Source_Code\config_file.ini"
        name_of_script = 'Sites_QAQC.py'

        # TODO Add a field to hold the most recent date a site has been cleaned


        mismatched_site_status = []
        mismatched_cleanup_rec = []

        sites_sql_clause = (None, 'ORDER BY Site_Number')  # Order by Site_Number in ascending order
        with arcpy.da.SearchCursor(sites_CURRENT, ['Site_Number', 'Site_Status_Collector', 'Cleanup_Recommended_Collector'], '', '', '', sites_sql_clause) as sites_search_cur:
            for s_row in sites_search_cur:
                site_num_col            = s_row[0]
                site_stat_col           = s_row[1]
                cleanup_rec_col         = s_row[2]
                print 'Site Number: {}'.format(site_num_col)


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
                        print '  Site Status Collector: {}'.format(site_stat_col)
                        print '  Site Status Survey123: {}'.format(site_stat_visit)
                        print '     Date of Last Visit: {}'.format(date_of_visit)
                        del v_row
                    except:
                        print '   No visits for that site'

                if site_stat_col != site_stat_visit:
                    print '***  Site Status not the same! ***'
                    mismatched_site_status.append('Site: "<b>{}</b>" has a Site Status of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, site_stat_col, site_stat_visit))
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
                        print '  Cleanup Recommended Collector: {}'.format(cleanup_rec_col)
                        print '  Cleanup Recommended Survey123: {}'.format(cleanup_rec_visit)
                        print '             Date of Last Visit: {}'.format(date_of_visit)
                        del v_row
                    except:
                        print '   No visits for that site'

                if cleanup_rec_col != cleanup_rec_visit:
                    print '***  Cleanup Recommended not the same! ***'
                    mismatched_cleanup_rec.append('Site: "<b>{}</b>" has a Cleanup Recommended of: "<b>{}</b>" in Collector and: "<b>{}</b>" in Survey123'.format(site_num_col, cleanup_rec_col, cleanup_rec_visit))
                del visits_search_cur

                #---------------------------------------------------------------
                #         Get most recent date each site has been cleaned
                # TODO: Get this section written

                # For each site get the most recent visit (that had 'Site Cleaning' as the Reason_For_Visit)
                #   and get the Date_Of_Visit (for that visit)
                #   This date will be

                print '\n------------------------------------------------------'

        del sites_search_cur


        #-----------------------------------------------------------------------
        #                     Send QA/QC Warning Emails

        # Send an email if there were any mismatched Site Statuses
        if len(mismatched_site_status) > 0:

            mismatched_site_status_str = '<br>'.join(mismatched_site_status)

            subj = 'WARNING.  There were mismatched Site Statuses in {}'.format(name_of_script)
            body = """Below is a list of sites that have a different <u>Site Status</u>
            in Collector and in the most recent visit for that site in Survey123.<br>
            Please go into the appropriate database to make the corrections:<br><br>
            {}""".format(mismatched_site_status_str)

            Email_W_Body(subj, body, email_admin_ls, cfgFile)


        # Send an email if there were any mismatched Cleanup Recommended
        if len(mismatched_cleanup_rec) > 0:

            mismatched_cleanup_rec_str = '<br>'.join(mismatched_cleanup_rec)

            subj = 'WARNING.  There were mismatched Cleanup Recommended in {}'.format(name_of_script)
            body = """Below is a list of sites that have a different <u>Cleanup Recommended</u>
            in Collector and in the most recent visit for that site in Survey123.<br>
            Please go into the appropriate database to make the corrections:<br><br>
            {}""".format(mismatched_cleanup_rec_str)

            Email_W_Body(subj, body, email_admin_ls, cfgFile)
    except Exception as e:
        print 'ERROR!!!'
        print str(e)

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

    print 'Starting Email_W_Body()'

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

    print 'Successfully emailed results.'


if __name__ == '__main__':
    main()
