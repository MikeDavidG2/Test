#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     04/09/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, csv, ConfigParser, datetime, time, sys, shutil


def main():

    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Create_QA_QC_File'


    # Name of this script
    name_of_script = 'DEV_TRACKER_{}.py'.format(shorthand_name)


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                   Use cfgFile to set the below variables

    # Find a connection to the config file
    # You can set multiple config files (to easily move this script to another network)
    # Recommended (A = BLUE network) and (B = COUNTY network)
    cfgFile_A     = r"P:\20180510_development_tracker\DEV\Scripts\Config_Files\DEV_TRACKER_Main_Config_File.ini"
    cfgFile_B     = r"D:\DEV_TRACKER\PROD\Scripts\Config_Files\DEV_TRACKER_Main_Config_File.ini"

    if os.path.exists(cfgFile_A):
        cfgFile = cfgFile_A  # Use config file A

    elif os.path.exists(cfgFile_B):
        cfgFile = cfgFile_B  # Use config file B

    else:
        print("*** ERROR! cannot find valid INI file ***\nMake sure a valid INI file exists at:\n  {}\nOR:\n  {}".format(cfgFile_A, cfgFile_B))
        print 'You may have to change the name/location of the INI file,\nOR change the variable in this script.'
        success = False
        time.sleep(10)
        return  # Stop the script

    if os.path.isfile(cfgFile):
        print 'Using INI file found at:\n  {}\n'.format(cfgFile)
        config = ConfigParser.ConfigParser()
        config.read(cfgFile)


    # Get variables from .ini file
    root_folder = config.get('Paths_Local', 'Root_Folder')
    pds_share_folder  = config.get('Paths_Local', 'Folder_To_Share_w_PDS')


    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    qa_qc_folder = os.path.join(pds_share_folder, 'QA_QC_Folder')


    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Dictionary of the 'Script Name'  :  'Extract Name'
    log_file_dict = {'DEV_TRACKER_Format_CSV_Extracts'                 : 'SHOULDNT HAVE A QA/QC SECTION',
                     'DEV_TRACKER_Process_Approved_GPA_Map_02'         : 'Approved General Plan Amendments (2011 General Plan Forward) (Map 2).csv',
                     'DEV_TRACKER_Process_Existing_DU_Map_03'          : 'Existing Dwelling Units (2011 General Plan Forward) (Map 3 & Map 11).csv',
                     'DEV_TRACKER_Process_Approved_DU_Map_04'          : 'Dwelling Units - Discretionary Approved (2011 GP Forward) (Map 4).csv',
                     'DEV_TRACKER_Process_Grading_In_Process_Map_05'   : 'Dwelling Units - Land Development Grading In-Process (Map 5).csv',
                     'DEV_TRACKER_Process_In_Process_DU_Map_07'        : 'Dwelling Units - Discretionary In-Process (Map 7).csv',
                     'DEV_TRACKER_Process_In_Process_GPA_Map_08_A'     : 'In-Process Applicant General Plan Amendments (Map 8).csv',
                     'DEV_TRACKER_Process_In_Process_GPA_Map_08_B'     : 'In-Process County General Plan Amendments (Map 8).csv',
                     'DEV_TRACKER_Process_In_Process_GPA_Map_08_C'     : 'No extract, but combination of data from the two Map 08 extracts',
                     'DEV_TRACKER_Process_GP_Delta_Map_09'             : 'No extract, but combination of data from Map 04 and Map 07 extracts',
                     'DEV_TRACKER_Process_Cmpltd_Bld_Permits_Map_11'   : 'Existing Dwelling Units (2011 General Plan Forward) (Map 3 & Map 11).csv',
                     'DEV_TRACKER_Process_Annex_Aquitns_Map_12'        : 'SHOULDNT HAVE A QA/QC SECTION',
                     'DEV_TRACKER_Bin_Processed_Data'                  : 'SHOULDNT HAVE A QA/QC SECTION',
                     'DEV_TRACKER_Process_Curnt_Dev_Potentl_Map_06'    : 'SHOULDNT HAVE A QA/QC SECTION',
                     'DEV_TRACKER_Process_Future_Dev_Potentl_Map_10'   : 'SHOULDNT HAVE A QA/QC SECTION',
                     'DEV_TRACKER_Update_LAST_DATA_UPDATE'             : 'SHOULDNT HAVE A QA/QC SECTION',
                     'DEV_TRACKER_Export_MXD_to_PDF'                   : 'SHOULDNT HAVE A QA/QC SECTION',
                     'DEV_TRACKER_Create_QA_QC_File'                   : 'SHOULDNT HAVE A QA/QC SECTION'
                    }


    # Misc variables
    success = True


    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Main Function

    # Make sure the log file folder exists, create it if it does not
    if not os.path.exists(log_file_folder):
        print 'NOTICE, log file folder does not exist, creating it now\n'
        os.mkdir(log_file_folder)

    # Turn all 'print' statements into a log-writing object
    try:
        log_file = r'{}\{}'.format(log_file_folder, name_of_script.split('.')[0])
        orig_stdout, log_file_date, dt_to_append = Write_Print_To_Log(log_file, name_of_script)
    except Exception as e:
        success = False
        print '\n*** ERROR with Write_Print_To_Log() ***'
        print str(e)


    #---------------------------------------------------------------------------
    #          Delete any previously created SUCCESS/ERROR files
    #---------------------------------------------------------------------------
    if os.path.exists(success_file):
        print 'Deleting old file at:\n  {}\n'.format(success_file)
        os.remove(success_file)
    if os.path.exists(error_file):
        print 'Deleting old file at:\n  {}\n'.format(error_file)
        os.remove(error_file)


    #---------------------------------------------------------------------------
    #                      Create Folders if needed
    #---------------------------------------------------------------------------
    if success == True:
        try:

            # Create the qa_qc_folder if it does not exist
            if not os.path.exists(qa_qc_folder):
                print 'INFO, folder "{}" does not exist, creating it now'.format(os.path.basename(qa_qc_folder))
                os.mkdir(qa_qc_folder)

        except Exception as e:
            success = False
            print '\n*** ERROR with Creating Folders ***'
            print str(e)


    #---------------------------------------------------------------------------
    #                        Create the QA/QC File
    #---------------------------------------------------------------------------
    if success == True:

        try:
            qa_qc_file   = os.path.join(qa_qc_folder, 'DEV_TRACKER_QA_QC_Warnings_{}.log'.format(dt_to_append))
            Create_QA_QC_File(log_file_folder, qa_qc_file, log_file_dict)

        except Exception as e:
            success = False
            print '\n*** ERROR with Create_QA_QC_File() ***'
            print str(e)

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    # Write a file to disk to let other scripts know if this script ran
    # successfully or not
    print '\n------------------------------------------------------------------'
    try:

        # Set a file_name depending on the 'success' variable.
        if success == True:
            file_to_create = success_file
        else:
            file_to_create = error_file

        # Write the file
        print '\nCreating file:\n  {}\n'.format(file_to_create)
        open(file_to_create, 'w')

    except Exception as e:
        success = False
        print '*** ERROR with Writing a Success or Fail file() ***'
        print str(e)


    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    # Footer for log file
    finish_time_str = [datetime.datetime.now().strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                    {}'.format(finish_time_str)
    print '              Finished {}'.format(name_of_script)
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

    # End of script reporting
    print 'Successfully ran script = {}'.format(success)
    time.sleep(3)
    sys.stdout = orig_stdout
    sys.stdout.flush()

    if success == True:
        print '\nSUCCESSFULLY ran {}'.format(name_of_script)
    else:
        print '\n*** ERROR with {} ***'.format(name_of_script)

    print 'Please find log file at:\n  {}\n'.format(log_file_date)
    print '\nSuccess = {}'.format(success)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                            START DEFINING FUNCTIONS
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


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
      log_file_date (str): Full path to the log file with the date appended to it.
      dt_to_append (str): Date and time in string format 'YYYY_MM_DD__HH_MM_SS'

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

    return orig_stdout, log_file_date, dt_to_append


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
def Create_QA_QC_File(log_file_folder, qa_qc_file, log_file_dict):
    """
    PARAMETERS:
      log_file_folder (str): Path to the folder that contains the log files that
        may contain text from the QA_QC() function.

      qa_qc_file (str): Path to the folder where the new QA/QC file will be
        created.

      log_file_dict (dictionary): Dictionary of the 'Script Name'  :  'Extract Name'
        This is used to get the extract name from the name of the log file

    RETURNS:
      None

    FUNCTION:
      Creates one QA/QC File by aggregating all the text from the QA_QC()
      functions from the most recent log file from each script.
    """

    print('\n-----------------------------------------------------------------')
    print('Starting Create_QA_QC_File()')

    #---------------------------------------------------------------------------
    # Move any old QA/QC files to an archived folder
    qa_qc_folder = os.path.dirname(qa_qc_file)
    old_qa_qc_files = [f for f in os.listdir(qa_qc_folder) if f.startswith(os.path.basename(qa_qc_file[:-25]))]

    previous_qa_qc_folder = os.path.join(qa_qc_folder, 'Previous_QA_QC_Warnings')

    # Create the previous_qa_qc_folder if it does not exist
    if not os.path.exists(previous_qa_qc_folder):
        print 'INFO, folder "{}" does not exist, creating it now'.format(os.path.basename(previous_qa_qc_folder))
        os.mkdir(previous_qa_qc_folder)

    # Move the files from 'qa_qc_folder' to 'previous_qa_qc_folder'
    for f in old_qa_qc_files:
        src  = os.path.join(qa_qc_folder, f)
        dest = os.path.join(previous_qa_qc_folder, f)
        shutil.move(src, dest)


    #---------------------------------------------------------------------------
    # Get a list of ALL the log files in the log_file_folder
    print('\n  Getting list of all log files in log file folder at:\n    {}'.format(log_file_folder))

    log_files_all = [f for f in os.listdir(log_file_folder) if os.path.isfile(os.path.join(log_file_folder, f))]


    #---------------------------------------------------------------------------
    # Get a list of ALL the log files w/o a date appended to the end
    # Then get a unique list of those log files
    print('\n  Getting list of all unique log files (w/o the date appended to the end of the file name)')

    log_files_wo_date = []

    for f in log_files_all:
        log_files_wo_date.append(f[:-25])
        ##print f[:-25]  # For testing

    log_files_wo_date = sorted(set(log_files_wo_date))


    #---------------------------------------------------------------------------
    # Get a list of the most recently created log file for each script
    # Go through log_files_wo_date and find the most recently created log file
    print('\n  Geting a list of the most recently created log file from each script')

    most_recent_log_files = []
    for file_wo_date in log_files_wo_date:
        files = [f for f in log_files_all if f.startswith(file_wo_date)]

        files.sort(reverse=True)  # Get a unique, sorted list

        most_recent_log_files.append(files[0])  # The first item in the list is the most recently created file

    most_recent_log_files.sort()


    #---------------------------------------------------------------------------
    # Get QA/QC data from log files (if it exists) and write it to a common qa_qc_file
    for most_recent_log_file in most_recent_log_files:

        file_wo_date = most_recent_log_file[:-25]
        header = log_file_dict[file_wo_date]

        print('\n  -----------------------------------------------------------')
        print('  Processing data from:\n    {}'.format(header))

        source_log_file = os.path.join(log_file_folder, most_recent_log_file)
        print('\n  Looking for QA/QC Info in log file at:\n    {}'.format(source_log_file))

        with open(source_log_file, "r") as source:
            reader = csv.reader(source)
            with open(qa_qc_file, "ab") as result:
                writer = csv.writer(result)

                write_row = False  # Flag to control if we are writing to the qa_qc_file

                for row in reader:
                    ##print row  # For testing


                    #-----------------------------------------------------------
                    # Determine how to handle the row
                    if len(row) == 0 and write_row == False:  # If the row is blank and we don't want to write, pass
                        pass

                    elif len(row) == 0 and write_row == True:  # If the row is blank and we do want to write, write a blank row
                        writer.writerow([])

                    elif row[0].startswith('Start QA_QC()'):  # If the row isn't blank and starts with the QA/QC function, start writing to the qa_qc_file
                        write_row = True

                        # Set header for each log file
                        writer.writerow([])
                        writer.writerow(['++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'])
                        writer.writerow(['++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'])
                        writer.writerow(['Extract:  {}'.format(header)])
                        writer.writerow([])
                        writer.writerow(['QA Info from log file:  {}'.format(most_recent_log_file)])

                    elif row[0].startswith('Finished QA_QC()'):  # If the row isn't blank and ends the QA/QC function, stop writing to the qa_qc_file
                        write_row = False


                    #-----------------------------------------------------------
                    # If the row is in between 'Start QA_QC()' and 'Finished QA_QC()'
                    # Then write to the qa_qc_file
                    if len(row) != 0:
                        if (write_row == True) and (row[0] != 'Start QA_QC()'):

                            row[0] = row[0].replace('"', '')  # Remove any of the double quotes

                            ##print row  # For testing

                            writer.writerow(row)

    print('\nFinished Create_QA_QC_File()')


if __name__ == '__main__':
    main()
