#-------------------------------------------------------------------------------
# Purpose:
"""
This script strips out the "name_of_field_to_delete" [WORK_DESC]
From any CSV in:
  "folder_with_original_csvs"
And puts the formatted CSV into:
  "folder_to_put_formatted_csvs"

Without the [WORK_DESC] field.

This is done because that field has carriage returns that cause the
Import CSV to FGDB Table to fail.

This script is run before any CSV to FGDB Table is attempted
"""
#
# Author:      mgrue
#
# Created:     27/08/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, datetime, ConfigParser, sys, time, csv

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Format_CSV_Extracts'


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
    root_folder                  = config.get('Paths_Local', 'Root_Folder')
    folder_with_original_csvs    = config.get('Paths_Local', 'Folder_With_Original_CSVs')
    folder_to_put_formatted_csvs = config.get('Paths_Local', 'Folder_With_Formatted_CSVs')


    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Set field name to be deleted
    name_of_field_to_delete = 'WORK_DESC'


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
    try:
        if os.path.exists(success_file):
            print 'Deleting old file at:\n  {}\n'.format(success_file)
            os.remove(success_file)
        if os.path.exists(error_file):
            print 'Deleting old file at:\n  {}\n'.format(error_file)
            os.remove(error_file)

    except Exception as e:
        success = False
        print '\n*** ERROR with Deleting previously created SUCCESS/ERROR files ***'
        print str(e)


    #---------------------------------------------------------------------------
    #          Delete any previously created Formatted CSVs
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # List all files in folder_to_put_formatted_csvs
            print('\n-----------------------------------------------------------------')
            print('Listing all files to see if any previously existing CSV files need to be deleted at:\n  {}\n'.format(folder_to_put_formatted_csvs))
            files = [f for f in os.listdir(folder_to_put_formatted_csvs) if os.path.isfile(os.path.join(folder_to_put_formatted_csvs, f))]

            old_csv_files_to_delete = []  # List of files to be deleted

            for f in files:
                if f.endswith('.csv'):
                    ##print f  # For testing

                    # Add the full path of the file to "old_csv_files_to_delete"
                    old_csv_files_to_delete.append(os.path.join(folder_to_put_formatted_csvs, f))


            # Delete previously existing CSV files
            if len(old_csv_files_to_delete) == 0:
                print('  Ok. No files to delete')

            else:
                print('Deleting previously existing CSV files:')
                for file_to_delete in old_csv_files_to_delete:
                    print('  {}'.format(file_to_delete))
                    os.remove(file_to_delete)

            del files

        except Exception as e:
            success = False
            print '\n*** ERROR with Deleting any previously created Formatted CSVs ***'
            print str(e)


    #---------------------------------------------------------------------------
    #            Format Original CSVs to "folder_to_put_formatted_csvs"
    #---------------------------------------------------------------------------
    if success == True:
        try:
            print('\n---------------------------------------------------------')

            # List all files in folder_with_original_csvs
            print('Listing all files that need to be formatted at:\n  {}\n'.format(folder_with_original_csvs))
            files = [f for f in os.listdir(folder_with_original_csvs) if os.path.isfile(os.path.join(folder_with_original_csvs, f))]

            csv_files_to_be_formatted = []

            for f in files:
                if f.endswith('.csv'):
                    ##print f  # For testing

                    # Add the full path of the file to "csv_files_to_be_formatted"
                    csv_files_to_be_formatted.append(os.path.join(folder_with_original_csvs, f))


            if len(csv_files_to_be_formatted) == 0:
                success = False
                print('*** WARNING! No files to format at:\n  {}'.format(folder_with_original_csvs))


            # Format the CSV files
            else:
                print('Formatting Original CSV files:')
                csv_files_to_be_formatted.sort()

                for file_to_format in csv_files_to_be_formatted:
                    print('\n  -----------------------------------------------')
                    print('  Processing CSV:  {}'.format(os.path.basename(file_to_format)))
                    print('    Orig CSV:       {}:'.format(file_to_format))

                    formatted_file = os.path.join(folder_to_put_formatted_csvs, os.path.basename(file_to_format))
                    print '    Formatted CSV:  {}'.format(formatted_file)

                    #-----------------------------------------------------------
                    # Find the index of the field to delete
                    with open(file_to_format,"rb") as source:
                        reader = csv.reader(source)

                        headers = reader.next()
                        ##print headers  # For testing

                        if name_of_field_to_delete not in headers:
                            index_of_field_to_delete = -99
                            print('\n    Field [{}] is not in this CSV, copying over w/o removing a field'.format(name_of_field_to_delete))

                        # Find the column (index) of the field to delete
                        if name_of_field_to_delete in headers:
                            index_of_field_to_delete = 0

                            for header in headers:
                                if header != name_of_field_to_delete:
                                    index_of_field_to_delete += 1
                                else:
                                    break

                            print '\n    Field [{}] is at column index: {}'.format(name_of_field_to_delete, index_of_field_to_delete)

                        del source, reader


                    #-----------------------------------------------------------
                    # Copy over the CSV

                    with open(file_to_format,"rb") as source:
                        reader = csv.reader(source)
                        with open(formatted_file,"wb") as result:
                            wtr= csv.writer(result)
                            for r in reader:
                                try:

                                    # If the name_of_field_to_delete was found, then write to result_csv without the name_of_field_to_delete
                                    if index_of_field_to_delete != -99:
                                        ##print r[0]  # For testing
                                        del r[index_of_field_to_delete]

                                    wtr.writerow(r)
                                except IndexError:
                                    pass
                                    ##print 'No more rows with data to process'  # For testing


        except Exception as e:
            success = False
            print '\n*** ERROR with Formatting Original CSVs ***'
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
if __name__ == '__main__':
    main()
