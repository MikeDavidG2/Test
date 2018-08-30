#-------------------------------------------------------------------------------
# Purpose:
"""
TODO: Update documentation here
"""
#
# Author:      mgrue
#
# Created:     27/08/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, datetime, ConfigParser, sys, time, arcpy

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Copy_Edit_SDE_To_Prod_SDE'


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
    root_folder                = config.get('Paths_Local',   'Root_Folder')
    prod_SDE_conn_file         = config.get('Prod_SDE_Info', 'Prod_SDE_Conn_File')
    prod_SDE_prefix            = config.get('Prod_SDE_Info', 'Prod_SDE_Prefix')
    edit_SDE_conn_File         = config.get('Edit_SDE_Info', 'Edit_SDE_Conn_File')
    edit_SDE_prefix            = config.get('Edit_SDE_Info', 'Edit_SDE_Prefix')
    edit_SDE_fds               = config.get('Edit_SDE_Info', 'Edit_SDE_FDS')

    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])

    # Number of SUCCESS files this script needs to see in the success_error_folder
    # in order to safely run
    desired_num_success_files = 17


    # Misc variables
    success = True


    #---------------------------------------------------------------------------
    #                         Set Edit SDE Paths

    # Paths to Feature Classes
    approved_gpa_map_02_hex_fc_EDIT       = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_02_Approved_GPA_HEXBIN')
    existing_du_map_03_hex_fc_EDIT        = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_03_Existing_DU_HEXBIN')
    approved_du_map_04_hex_fc_EDIT        = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_04_Approved_DU_HEXBIN')
    grading_in_process_map_05_hex_fc_EDIT = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_05_Grading_In_Process_HEXBIN')
    curnt_dev_potentl_map_06_hex_fc_EDIT  = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_06_Curnt_Dev_Potentl_HEXBIN')
    in_process_DU_map_07_hex_fc_EDIT      = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_07_In_Process_DU_HEXBIN')
    in_process_GPAs_map_08_hex_fc_EDIT    = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_08_In_Process_GPA_HEXBIN')
    gp_delta_map_09_hex_fc_EDIT           = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_09_GP_Delta_HEXBIN')
    future_dev_potentl_map_10_hex_fc_EDIT = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_10_Future_Dev_Potentl_HEXBIN')
    cmpltd_bld_permits_map_11_hex_fc_EDIT = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_11_Cmpltd_Bld_Permits_HEXBIN')
    annex_aquitns_map_12_hex_fc_EDIT      = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_12_Annex_Aquitns_HEXBIN')

    hex_fc_EDIT_list = [approved_gpa_map_02_hex_fc_EDIT,
                        existing_du_map_03_hex_fc_EDIT,
                        approved_du_map_04_hex_fc_EDIT,
                        grading_in_process_map_05_hex_fc_EDIT,
                        curnt_dev_potentl_map_06_hex_fc_EDIT,
                        in_process_DU_map_07_hex_fc_EDIT,
                        in_process_GPAs_map_08_hex_fc_EDIT,
                        gp_delta_map_09_hex_fc_EDIT,
                        future_dev_potentl_map_10_hex_fc_EDIT,
                        cmpltd_bld_permits_map_11_hex_fc_EDIT,
                        annex_aquitns_map_12_hex_fc_EDIT
                       ]


    # Paths to Tables
    approved_gpa_map_02_cpasg_tbl_EDIT       = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_02_Approved_GPA_CPASG')
    existing_du_map_03_cpasg_tbl_EDIT        = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_03_Existing_DU_CPASG')
    approved_du_map_04_cpasg_tbl_EDIT        = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_04_Approved_DU_CPASG')
    grading_in_process_map_05_cpasg_tbl_EDIT = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_05_Grading_In_Process_CPASG')
    curnt_dev_potentl_map_06_cpasg_tbl_EDIT  = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_06_Curnt_Dev_Potentl_CPASG')
    in_process_DU_map_07_cpasg_tbl_EDIT      = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_07_In_Process_DU_CPASG')
    in_process_GPAs_map_08_cpasg_tbl_EDIT    = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_08_In_Process_GPA_CPASG')
    gp_delta_map_09_cpasg_tbl_EDIT           = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_09_GP_Delta_CPASG')
    future_dev_potentl_map_10_cpasg_tbl_EDIT = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_10_Future_Dev_Potentl_CPASG')
    cmpltd_bld_permits_map_11_cpasg_tbl_EDIT = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_11_Cmpltd_Bld_Permits_CPASG')
    annex_aquitns_map_12_cpasg_tbl_EDIT      = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_12_Annex_Aquitns_CPASG')

    cpasg_tbl_EDIT_list =  [approved_gpa_map_02_cpasg_tbl_EDIT,
                            existing_du_map_03_cpasg_tbl_EDIT,
                            approved_du_map_04_cpasg_tbl_EDIT,
                            grading_in_process_map_05_cpasg_tbl_EDIT,
                            curnt_dev_potentl_map_06_cpasg_tbl_EDIT,
                            in_process_DU_map_07_cpasg_tbl_EDIT,
                            in_process_GPAs_map_08_cpasg_tbl_EDIT,
                            gp_delta_map_09_cpasg_tbl_EDIT,
                            future_dev_potentl_map_10_cpasg_tbl_EDIT,
                            cmpltd_bld_permits_map_11_cpasg_tbl_EDIT,
                            annex_aquitns_map_12_cpasg_tbl_EDIT
                           ]


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
    #          Only run the Export if all previously run scripts were
    #                          SUCCESSFULLY run
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # List all files in "success_error_folder"
            print('\n-----------------------------------------------------------------')
            print('Listing all files at:\n  {}\nTo confirm that all previous scripts ran sucessfully'.format(success_error_folder))
            files = [f for f in os.listdir(success_error_folder) if os.path.isfile(os.path.join(success_error_folder, f))]

            # Check to see if any files start with 'ERROR'
            print('\n  Checking to see if any scripts produced an "ERROR" file:')
            for f in files:
                if f.startswith('ERROR'):
                    success = False
                    print('*** WARNING! There is an "ERROR" file at:\n  {}\n'.format(os.path.join(success_error_folder, f)))


            # If there were no ERROR files,
            # Check to confirm there are the correct number of files that start with "SUCCESS"
            if success == True:
                print('\n  Checking to see if there are the correct number of "SUCCESS" files::')
                count_success = 0
                for f in files:
                    if f.startswith('SUCCESS'):
                        count_success += 1

                if count_success != desired_num_success_files:
                    success = False
                    print('*** WARNING!  There should be {} "SUCCESS" files, but there are only {}'.format(desired_num_success_files, count_success))
                    print('This means that some previously run scripts were not successfully run.')
                    print('But they did not produce an ERROR file for some reason')


            if success == False:
                print('\nThe above "WARNINGS" mean that this script will not be run')
                print('Please fix the previously run scripts and rerun this script')

            else:
                print('    OK! All previously run scripts were "SUCCESSFULLY" run.  Continuing to run this script.')

        except Exception as e:
            success = False
            print '\n*** ERROR with Checking if all previously run scripts were SUCCESSFULLY run ***'
            print str(e)


    #---------------------------------------------------------------------------
    #             Copy the Tables from Edit SDE to Prod SDE
    #---------------------------------------------------------------------------
    if success == True:
        print('\n\n-----------------------------------------------------------')
        print('-----------------------------------------------------------')
        print('Copy the Tables from Edit SDE to Prod SDE:')

        for edit_tbl in cpasg_tbl_EDIT_list:
            try:
                if not arcpy.Exists(edit_tbl):
                    success = False
                    print('*** WARNING! This Edit Table does not exist:\n  {}'.format(edit_tbl))

                else:
                    print('\n  -----------------------------------------------')

                    # Get the name of the Table (w/o the edit_SDE_prefix)
                    edit_tbl_name = os.path.basename(edit_tbl)
                    edit_tbl_name = edit_tbl_name.replace(edit_SDE_prefix, "")

                    print("  Processing:  {}".format(os.path.basename(edit_tbl_name)))

                    # Set the path to the Table in Prod SDE based on the name of the Edit SDE Table
                    prod_tbl = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + edit_tbl_name)

                    #-----------------------------------------------------------
                    # Delete the prod data and append the working data to prod
                    if not arcpy.Exists(prod_tbl):
                        success = False
                        print('*** WARNING! This Prod Table does not exist:\n  {}'.format(prod_tbl))

                    else:

                        print '\n    Deleting rows at:\n      {}'.format(prod_tbl)
                        arcpy.DeleteRows_management(prod_tbl)

                        print '\n    Append rows from:\n      {}\n    To:\n      {}'.format(edit_tbl, prod_tbl)
                        arcpy.Append_management(edit_tbl, prod_tbl)


            except Exception as e:
                success = False
                print '\n*** ERROR with Processing: ***\n  {}'.format(edit_tbl)
                print str(e)


    #---------------------------------------------------------------------------
    #             Copy the Feature Classes from Edit SDE to Prod SDE
    #---------------------------------------------------------------------------
    if success == True:
        print('\n\n-----------------------------------------------------------')
        print('-----------------------------------------------------------')
        print('Copy the Feature Classes from Edit SDE to Prod SDE:')

        for edit_fc in hex_fc_EDIT_list:
            try:
                if not arcpy.Exists(edit_fc):
                    success = False
                    print('*** WARNING! This Edit FC does not exist:\n  {}'.format(edit_fc))

                else:
                    print('\n  -----------------------------------------------')

                    # Get the name of the FC (w/o the edit_SDE_prefix)
                    edit_fc_name = os.path.basename(edit_fc)
                    edit_fc_name = edit_fc_name.replace(edit_SDE_prefix, "")

                    print("  Processing:  {}".format(os.path.basename(edit_fc_name)))

                    # Set the path to the FC in Prod SDE based on the name of the Edit SDE FC
                    prod_fc = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + edit_fc_name)

                    #-----------------------------------------------------------
                    # Delete the prod data and append the working data to prod
                    if not arcpy.Exists(prod_fc):
                        success = False
                        print('*** WARNING! This Prod FC does not exist:\n  {}'.format(prod_fc))

                    else:

                        print '\n    Deleting features at:\n      {}'.format(prod_fc)
                        arcpy.DeleteFeatures_management(prod_fc)

                        print '\n    Append features from:\n      {}\n    To:\n      {}'.format(edit_fc, prod_fc)
                        arcpy.Append_management(edit_fc, prod_fc)


            except Exception as e:
                success = False
                print '\n*** ERROR with Processing: ***\n  {}'.format(edit_fc)
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
