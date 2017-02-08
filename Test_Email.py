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

import ConfigParser, smtplib

from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.text import MIMEText

def main():

    errorSTATUS = 0
    cfgFile = r"U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Master\accounts.txt"
    email_list = ['michael.grue@sdcounty.ca.gov']
    prod_FGDB = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data'
    attach_folder = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data\Sci_Monitoring_pics'
    Downloaded_features = ['feature1', 'feature2', 'feature3']
    New_Loc_Descs = ['List of descriptions', '  new suggestion...', '  new suggestion...']



    Email_Results(errorSTATUS, cfgFile, email_list, prod_FGDB, attach_folder, Downloaded_features, New_Loc_Descs)

#-------------------------------------------------------------------------------

def Email_Results(errorSTATUS, cfgFile, dpw_email_list, prod_FGDB, attach_folder, dl_features_ls, new_loc_descs):
    print 'Emailing Results...'



    # If there are no errors and at least one feature was downloaded
    if (errorSTATUS == 0 and (len(dl_features_ls) > 0)):
        print '  Sending "No Errors" email...'

        # Send this email to the dpw_email_list
        email_list = dpw_email_list

        # Format the Subject for the 'No Errors' email
        subj = 'SUCCESSFULLY completed DPW_Science_and_Monitoring.py script.'

        # Format the Body in html
        body  = ("""\
        <html>
          <head></head>
          <body>
            <p>There were <b>{num}</b> features downloaded this run.<br>
               You can find the updated FGDB at:  <i>{fgdb}</i><br>
               The images are located at:  <i>{af}</i><br>
            </p>
          </body>
        </html>
        """.format(num = len(dl_features_ls), fgdb = prod_FGDB, af = attach_folder))

    #---------------------------------------------------------------------------
    #                              Send the Email
    COMMASPACE = ', '

    # Set the subj, From, To, and body
    msg = MIMEMultipart()
    msg['Subject']   = subj
    msg['From']      = "Python Script"
    msg['To']        = COMMASPACE.join(dpw_email_list)  # Join each item in list with a ', '
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

