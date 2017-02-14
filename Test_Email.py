#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     13/01/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import ConfigParser, smtplib, os, datetime

from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.text import MIMEText

# Dont need below in main script
import time

def main():

    errorSTATUS = 0
    cfgFile = r"U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Master\accounts.txt"
    dpw_email_list = ['michael.grue@sdcounty.ca.gov', 'mikedavidg2@gmail.com']
    lueg_admin_email = ['michael.grue@stcounty.ca.gov']
    prod_FGDB = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data'
    attach_folder = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data\Sci_Monitoring_pics'
    SmpEvntIDs_dl = ['feature1', 'feature2', 'feature3']
    SmpEvntIDs_dl = []
    New_Loc_Descs = ['List of descriptions', '  new suggestion...', '  new suggestion...']
    fileLog = 'C:\\fileLog_address_here'
    start_time = datetime.datetime.now()

    time.sleep(5)
    dt_last_ret_data = datetime.datetime.now()

    # Send info to function
    Email_Results(errorSTATUS, cfgFile, dpw_email_list, lueg_admin_email, fileLog, start_time, dt_last_ret_data, prod_FGDB, attach_folder, SmpEvntIDs_dl, New_Loc_Descs)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                           FUNCTION:  Email Results
def Email_Results(errorSTATUS, cfgFile, dpw_email_list, lueg_admin_email, log_file, start_time_obj, dt_last_ret_data, prod_FGDB, attach_folder, dl_features_ls, new_loc_descs):
    print 'Emailing Results...'

    #---------------------------------------------------------------------------
    #         Do some processing to be used in the body of the email

    # Turn the start_time into a formatted string
    start_time = [start_time_obj.strftime('%m/%d/%Y %I:%M:%S %p')]

    # Get the current time and turn into a formatted string
    finish_time_obj = datetime.datetime.now()
    finish_time = [finish_time_obj.strftime('%m/%d/%Y %I:%M:%S %p')]

    # Turn the date data last retrieved into a formatted string
    data_last_retrieved = [dt_last_ret_data.strftime('%m/%d/%Y %I:%M:%S %p')]

    # Get the number of downloaded features
    num_dl_features = len(dl_features_ls)

    #---------------------------------------------------------------------------
    #                         Write the "Success" email

    # If there are no errors and at least one feature was downloaded
    if (errorSTATUS == 0 and num_dl_features > 0):
        print '  Writing the "Success" email...'

        # Send this email to the dpw_email_list
        email_list = dpw_email_list

        # Format the Subject for the 'Success' email
        subj = 'SUCCESSFULLY Completed DPW_Science_and_Monitoring.py Script'

        # Format the Body in html
        body  = ("""\
        <html>
          <head></head>
          <body>
            <h3>Times:</h3>
            <p>The script started at:             <i>{st}</i><br>
               The script finished at:            <i>{ft}</i><br>
            </p>
            <br>
            <h3>Info and Locations:</h3>
            <p>There were <b>{num}</b> features downloaded this run.<br>
               You can find the updated FGDB at:  <i>{fgdb}</i><br>
               All Images are located at:         <i>{af}</i><br>
               The Log file is located at:        <i>{lf}</i><br>
            </p>
          </body>
        </html>
        """.format(st = start_time[0], ft = finish_time[0], num = num_dl_features,
                   fgdb = prod_FGDB, af = attach_folder, lf = log_file))

    #---------------------------------------------------------------------------
    #                     Write the "No Data Downloaded' email

    # If there were no errors but no data was downloaded
    elif(errorSTATUS == 0 and num_dl_features == 0):
        print '  Writing the "No Data Downloaded" email'

        # Send this email to the dpw_email_list
        email_list = lueg_admin_email

        # Format the Subject for the 'No Data Downloaded' email
        subj = 'No Data Downloaded for DPW_Science_and_Monitoring.py script'

        # Format the Body in html
        body  = ("""\
        <html>
          <head></head>
          <body>
            <h3>Times:</h3>
            <p>The script started at:             <i>{st}</i><br>
               The script finished at:            <i>{ft}</i><br>
            </p>
            <br>
            <h3>Info and Locations:</h3>
            <p>There were <b>{num}</b> features downloaded this run.<br>
               This is NOT an error IF there was no data collected between the date the data was last retrieved... <i>{dlr}</i> ... and now.
               The Log file is located at:        <i>{lf}</i><br>
            </p>
          </body>
        </html>
        """.format(st = start_time, ft = finish_time, num = num_dl_features, dlr = data_last_retrieved, lf = log_file))

    #---------------------------------------------------------------------------
    #                        Write the "Errors" email

    # If there were errors with the script
    elif(errorSTATUS <> 0):
        print '  Writing "Error" email...'

        # Get the current working directory
        cwd = os.getcwd()

        # Send this email to the lueg_admin_emails
        email_list = lueg_admin_email

        # Format the Subject for the 'Errors' email
        subj = 'ERROR with DPW_Science_and_Monitoring.py script'

        # Format the Body in html
        body = ("""\
        <html>
          <head></head>
          <body>
            <p>There were ERRORS with the DPW_Science_and_Monitoring.py script.<br>
               The script started at:             <i>{st}</i><br>
               The error happened at:             <i>{ft}</i><br>
               The Log file is located at:        <i>{lf}</i><br>
               The script is located at:          <i>{cwd}</i><br>
            </p>
          <body>
        </html>

        """.format(st = start_time, ft = finish_time, lf = log_file, cwd = cwd))

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                              Send the Email

    # Set the subj, From, To, and body
    msg = MIMEMultipart()
    msg['Subject']   = subj
    msg['From']      = "Python Script"
    msg['To']        = ', '.join(dpw_email_list)  # Join each item in list with a ', '
    msg.attach(MIMEText(body, 'html'))

    # Get username and password from cfgFile
    config = ConfigParser.ConfigParser()
    config.read(cfgFile)
    email_usr = config.get('email', 'usr')
    email_pwd = config.get('email', 'pwd')

    # Send the email
    SMTP_obj = smtplib.SMTP('smtp.gmail.com',587)
    SMTP_obj.starttls()
    SMTP_obj.login(email_usr, email_pwd)
    SMTP_obj.sendmail(email_usr, email_list, msg.as_string())
    SMTP_obj.quit()

    print 'Successfully Emailed Results'
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()

