#-------------------------------------------------------------------------------

# Purpose:
"""
To update the FUTURE Development Potential (Map 10) data in SDE by
Adding or subtracting the HEXBINs and CPASGs values from previous scripts

We are first finding the predicted available DU per HEX (or CPASG) by:
    Map 06 + Map 08 (Current Development Potential + In-Process GPAs)
We are then subtracting from those predicted values:
    Map 07 (In-Process DUs)

(Map 06 + Map 08) - Map 07

The end result is a HEXBIN FC and a CPASG Table that has the values of the number
of DU that can still be added to each HEXBIN or CPASG (WITH taking into account
any "In-Process" DU's)
"""
#
# Author:      mgrue
#
# Created:     24/07/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, os, math, datetime, ConfigParser, sys, time

arcpy.env.overwriteOutput = True

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Future_Dev_Potentl_Map_10'


    # Name of this script
    name_of_script = 'DEV_TRACKER_Process_{}.py'.format(shorthand_name)


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
    folder_with_formatted_csvs = config.get('Paths_Local',   'Folder_With_Formatted_CSVs')
    prod_SDE_conn_file         = config.get('Prod_SDE_Info', 'Prod_SDE_Conn_File')
    prod_SDE_prefix            = config.get('Prod_SDE_Info', 'Prod_SDE_Prefix')
    edit_SDE_conn_File         = config.get('Edit_SDE_Info', 'Edit_SDE_Conn_File')
    edit_SDE_prefix            = config.get('Edit_SDE_Info', 'Edit_SDE_Prefix')
    edit_SDE_fds               = config.get('Edit_SDE_Info', 'Edit_SDE_FDS')


    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder       = '{}\{}'.format(root_folder, 'Data')

    wkg_fgdb          = '{}\{}'.format(data_folder, '{}.gdb'.format(shorthand_name))


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Misc variables
    success = True


    #---------------------------------------------------------------------------
    #             Set Variables used by both the HEXBIN and CPASG


    # Set field names this script will create (new)
    curnt_dev_potentl_map_06_new_fld  = 'Curnt_Dev_Potentl_Map_06'
    in_process_DU_map_07_new_fld      = 'In_Process_DU_Map_07'
    in_process_GPAs_map_08_new_fld    = 'In_Process_GPAs_Map_08'
    future_dev_potentl_map_10_new_fld = 'VALUE_Future_Dev_Potentl_Map_10'


    #---------------------------------------------------------------------------
    #                         Set HEXBIN Variables

    # Paths to SDE Feature Classes
    GRID_HEX_060_ACRES              = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + 'GRID_HEX_060_ACRES')
    curnt_dev_potentl_map_06_hex_fc = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_06_Curnt_Dev_Potentl_HEXBIN')
    in_process_DU_map_07_hex_fc     = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_07_In_Process_DU_HEXBIN')
    in_process_GPAs_map_08_hex_fc   = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_08_In_Process_GPA_HEXBIN')


    # Set field names of existing data (exst)
    hexbin_id_exst_fld                    = 'HEXAGONID'
    curnt_dev_potentl_map_06_exst_hex_fld = 'VALUE_Curnt_Dev_Potentl_Map_06'
    in_process_DU_map_07_exst_hex_fld     = 'VALUE_In_Process_DU_Map_07'
    in_process_GPAs_map_08_exst_hex_fld   = 'VALUE_In_Process_GPA_Map_08'


    # SDE HEXBIN FC to be updated
    prod_binned_fc                  = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + edit_SDE_fds, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_10_Future_Dev_Potentl_HEXBIN')


    #---------------------------------------------------------------------------
    #                         Set CPASG Variables

    # Paths to SDE Tables
    CMTY_PLAN_CN_2011                  = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + 'CMTY_PLAN_CN_2011')
    curnt_dev_potentl_map_06_cpasg_tbl = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_06_Curnt_Dev_Potentl_CPASG')
    in_process_DU_map_07_cpasg_tbl     = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_07_In_Process_DU_CPASG')
    in_process_GPAs_map_08_cpasg_tbl   = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_08_In_Process_GPA_CPASG')


    # Set field names of existing data (exst)
    cmty_plan_id_exst_fld                   = 'CPASG'
    cmty_plan_label_exst_fld                = 'CPASG_LABEL'
    curnt_dev_potentl_map_06_exst_cpasg_fld = 'VALUE_Curnt_Dev_Potentl_Map_06'
    in_process_DU_map_07_exst_cpasg_fld     = 'VALUE_In_Process_DU_Map_07'
    in_process_GPAs_map_08_exst_cpasg_fld   = 'VALUE_In_Process_GPA_Map_08'


    # SDE CPASG Table to be updated
    prod_cpasg_tbl                      = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_Map_10_Future_Dev_Potentl_CPASG')


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
    #                      Create FGDBs if needed
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # Delete and create working FGDB
            if arcpy.Exists(wkg_fgdb):
                print 'Deleting FGDB at:\n  {}\n'.format(wkg_fgdb)
                arcpy.Delete_management(wkg_fgdb)

            if not arcpy.Exists(wkg_fgdb):
                out_folder_path, out_name = os.path.split(wkg_fgdb)
                print 'Creating FGDB at:\n  {}'.format(wkg_fgdb)
                arcpy.CreateFileGDB_management(out_folder_path, out_name)

        except Exception as e:
            success = False
            print '\n*** ERROR with Creating FGDBs ***'
            print str(e)


    #===========================================================================
    #===========================================================================
    #                         PROCESS     HEXBINs
    #===========================================================================
    #===========================================================================
    if success == True:
        try:
            print('\n\n=======================================================')
            print('                   PROCESS     HEXBINs')

            #-------------------------------------------------------------------
            #                   Get a copy of  GRID_HEX_060_ACRES
            #-------------------------------------------------------------------

            print('\nGet a copy of GRID_HEX_060_ACRES:')

            # Copy the FC from SDE to the wkg_fgdb
            hexbin_fc = os.path.join(wkg_fgdb, 'HEXBIN_FC')

            out_path, out_name = os.path.split(hexbin_fc)
            print '\n  Copying FC:\n    {}\n  To:\n    {}\{}'.format(GRID_HEX_060_ACRES, out_path, out_name)
            arcpy.FeatureClassToFeatureClass_conversion(GRID_HEX_060_ACRES, out_path, out_name)


            #-------------------------------------------------------------------
            #                          Add required fields
            #-------------------------------------------------------------------

            print('\nAdding required fields to FC:\n  {}'.format(hexbin_fc))

            field_type = 'DOUBLE'
            fields_to_add = [curnt_dev_potentl_map_06_new_fld,
                             in_process_DU_map_07_new_fld,
                             in_process_GPAs_map_08_new_fld,
                             future_dev_potentl_map_10_new_fld]

            print '\n  Adding field:'
            for field_name in fields_to_add:

                print '    [{}] as a:  {}'.format(field_name, field_type)
                arcpy.AddField_management(hexbin_fc, field_name, field_type)


            #-------------------------------------------------------------------
            #        Get the values from the existing data into the hexbin_fc
            #-------------------------------------------------------------------

            #          Get the values in each hexbin from Map 06
            print('\n---------------------------------------------------------')
            print('Getting the values in each hexbin from Map 06:')

            Join_and_Calc_Fields_HEX(hexbin_fc, hexbin_id_exst_fld, curnt_dev_potentl_map_06_hex_fc, curnt_dev_potentl_map_06_exst_hex_fld, curnt_dev_potentl_map_06_new_fld)


            #-------------------------------------------------------------------
            #          Get the values in each hexbin from Map 07
            print('\n---------------------------------------------------------')
            print('Getting the values in each hexbin from Map 07:')

            Join_and_Calc_Fields_HEX(hexbin_fc, hexbin_id_exst_fld, in_process_DU_map_07_hex_fc, in_process_DU_map_07_exst_hex_fld, in_process_DU_map_07_new_fld)


            #-------------------------------------------------------------------
            #          Get the values in each hexbin from Map 08
            print('\n---------------------------------------------------------')
            print('Getting the values in each hexbin from Map 08:')

            Join_and_Calc_Fields_HEX(hexbin_fc, hexbin_id_exst_fld, in_process_GPAs_map_08_hex_fc, in_process_GPAs_map_08_exst_hex_fld, in_process_GPAs_map_08_new_fld)


            #-------------------------------------------------------------------
            #              Calculate the VALUE field for Map 10
            print('\n\n-------------------------------------------------------')

            # Set the expression for the calculation
            expression = '(!{map_06}!+!{map_08}!)-!{map_07}!'.format(map_06=curnt_dev_potentl_map_06_new_fld,
                                                                     map_07=in_process_DU_map_07_new_fld,
                                                                     map_08=in_process_GPAs_map_08_new_fld)


            # Calculate field
            print '\n  Calculating field [{}] to equal: "{}"\n'.format(future_dev_potentl_map_10_new_fld, expression)
            arcpy.CalculateField_management(hexbin_fc, future_dev_potentl_map_10_new_fld, expression, 'PYTHON_9.3')


            #-------------------------------------------------------------------
            #     Delete the prod data and append the working data to prod

            print('\n---------------------------------------------------------')
            print 'Get working data to prod:'

            print '\n  Deleting rows at:\n    {}'.format(prod_binned_fc)
            arcpy.DeleteRows_management(prod_binned_fc)

            print '\n  Append rows from:\n    {}\n  To:\n    {}'.format(hexbin_fc, prod_binned_fc)
            arcpy.Append_management(hexbin_fc, prod_binned_fc)


        except Exception as e:
            success = False
            print '\n*** ERROR with Processing Hexbins ***'
            print str(e)


    #===========================================================================
    #===========================================================================
    #                         PROCESS     CPASGs
    #===========================================================================
    #===========================================================================
    if success == True:
        try:
            print('\n\n=======================================================')
            print('                   PROCESS     CPASGs')

            #-------------------------------------------------------------------
            #              Get a table with every CPASG and Format It
            #-------------------------------------------------------------------

            print('\nGet a table with every CPASG and format it:')

            # Set the path to the hexbin table to be created
            cpasg_tbl = os.path.join(wkg_fgdb, 'CPASG_Table')

            freq_fields = [cmty_plan_label_exst_fld, cmty_plan_id_exst_fld]

            print '\n  Performing Frequency Analysis on FC:\n      {}'.format(CMTY_PLAN_CN_2011)
            print '    Frequency Fields:'
            for f in freq_fields:
                print '      {}'.format(f)
            print '    To create FC at:\n      {}'.format(cpasg_tbl)
            arcpy.Frequency_analysis(CMTY_PLAN_CN_2011, cpasg_tbl, freq_fields)


            # Add the 'Countywide' feature
            print '\n  Adding feature "Countywide"'
            fields = [cmty_plan_label_exst_fld, cmty_plan_id_exst_fld]
            with arcpy.da.InsertCursor(cpasg_tbl, fields) as cursor:
                cursor.insertRow(('Countywide', 190000))
            del cursor


            # Change the CPASG_LABEL to CPASG_NAME to be consistent with other scripts
            old_name = cmty_plan_label_exst_fld
            new_name = 'CPASG_NAME'
            print '\n  Changing Field: "{}"\n  To:  "{}"'.format(old_name, new_name)  # For testing purposes
            arcpy.AlterField_management(cpasg_tbl, old_name, new_name)


            # Delete the [FREQUENCY] field for readability
            print '\n  Deleting [FREQUENCY] field for readability'
            arcpy.DeleteField_management(cpasg_tbl, 'FREQUENCY')


            #-------------------------------------------------------------------
            #                          Add required fields
            #-------------------------------------------------------------------

            print('\nAdding required fields to FC:\n  {}'.format(cpasg_tbl))

            field_type = 'DOUBLE'
            fields_to_add = [curnt_dev_potentl_map_06_new_fld,
                             in_process_DU_map_07_new_fld,
                             in_process_GPAs_map_08_new_fld,
                             future_dev_potentl_map_10_new_fld]

            print '\n  Adding field:'
            for field_name in fields_to_add:

                print '    [{}] as a:  {}'.format(field_name, field_type)
                arcpy.AddField_management(cpasg_tbl, field_name, field_type)


            #-------------------------------------------------------------------
            #        Get the values from the existing data into the cpasg_tbl
            #-------------------------------------------------------------------

            #          Get the values in each CPASG from Map 06
            print('\n---------------------------------------------------------')
            print('Getting the values in each CPASG from Map 06:')

            Join_and_Calc_Fields_CPASG(cpasg_tbl, cmty_plan_id_exst_fld, curnt_dev_potentl_map_06_cpasg_tbl, curnt_dev_potentl_map_06_exst_cpasg_fld, curnt_dev_potentl_map_06_new_fld)


            #-------------------------------------------------------------------
            #          Get the values in each CPASG from Map 07
            print('\n---------------------------------------------------------')
            print('Getting the values in each CPASG from Map 07:')

            Join_and_Calc_Fields_CPASG(cpasg_tbl, cmty_plan_id_exst_fld, in_process_DU_map_07_cpasg_tbl, in_process_DU_map_07_exst_cpasg_fld, in_process_DU_map_07_new_fld)


            #-------------------------------------------------------------------
            #          Get the values in each CPASG from Map 08
            print('\n---------------------------------------------------------')
            print('Getting the values in each CPASG from Map 08:')

            Join_and_Calc_Fields_CPASG(cpasg_tbl, cmty_plan_id_exst_fld, in_process_GPAs_map_08_cpasg_tbl, in_process_GPAs_map_08_exst_cpasg_fld, in_process_GPAs_map_08_new_fld)


            #-------------------------------------------------------------------
            #              Calculate the VALUE field for Map 10
            print('\n\n-------------------------------------------------------')

            # Set the expression for the calculation
            expression = '(!{map_06}!+!{map_08}!)-!{map_07}!'.format(map_06=curnt_dev_potentl_map_06_new_fld,
                                                                     map_07=in_process_DU_map_07_new_fld,
                                                                     map_08=in_process_GPAs_map_08_new_fld)


            # Calculate field
            print 'Calculating field [{}] to equal: "{}"\n'.format(future_dev_potentl_map_10_new_fld, expression)
            arcpy.CalculateField_management(cpasg_tbl, future_dev_potentl_map_10_new_fld, expression, 'PYTHON_9.3')


            #-------------------------------------------------------------------
            #      Delete the prod data and append the working data to prod

            print('\n---------------------------------------------------------')
            print 'Get working data to prod:'

            print '\n  Deleting rows at:\n    {}'.format(prod_cpasg_tbl)
            arcpy.DeleteRows_management(prod_cpasg_tbl)

            print '\n  Append rows from:\n    {}\n  To:\n    {}'.format(cpasg_tbl, prod_cpasg_tbl)
            arcpy.Append_management(cpasg_tbl, prod_cpasg_tbl)


        except Exception as e:
            success = False
            print '*** ERROR with Processing CPASGs ***'
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
def Join_and_Calc_Fields_HEX(hexbin_fc, hexbin_id_exst_fld, hex_fc_w_values, exst_fld_w_values, new_fld_to_calc):
    """
    Get a lyr with the hex_fc_w_values joined to the working hexbin_fc
    Then calculate the new_fld_to_calc to equal the exst_fld_w_values
    """
    print '\n  Starting Join_and_Calc_Fields_HEX()'

    # Get a lyr that has the hexbin_fc joined to the existing HEX GRID on the 'HEXBINID' field
    lyr = Join_2_Objects_By_Attr(hexbin_fc, hexbin_id_exst_fld, hex_fc_w_values, hexbin_id_exst_fld, 'KEEP_ALL')


    # Set the expression for the calculation
    fc_name = os.path.basename(hex_fc_w_values)
    expression = '!{}.{}!'.format(fc_name, exst_fld_w_values)


    # Calculate field
    print '\n  Calculating field [{}] to equal: "{}"\n'.format(new_fld_to_calc, expression)
    arcpy.CalculateField_management(lyr, new_fld_to_calc, expression, 'PYTHON_9.3')
    arcpy.Delete_management(lyr)


    print('Finished Join_and_Calc_Fields_HEX()')
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Join_and_Calc_Fields_CPASG(cpasg_tbl, cmty_plan_id_exst_fld, cpasg_tbl_w_values, exst_fld_w_values, new_fld_to_calc):
    """
    Get a lyr with the cpasg_tbl_w_values joined to the working cpasg_tbl
    Then calculate the new_fld_to_calc to equal the exst_fld_w_values
    """
    print '\n  Starting Join_and_Calc_Fields_CPASG()'

    # Get a lyr that has the cpasg_tbl joined to the existing HEX GRID on the 'HEXBINID' field
    lyr = Join_2_Objects_By_Attr(cpasg_tbl, cmty_plan_id_exst_fld, cpasg_tbl_w_values, cmty_plan_id_exst_fld, 'KEEP_ALL')


    # Set the expression for the calculation
    fc_name = os.path.basename(cpasg_tbl_w_values)
    expression = '!{}.{}!'.format(fc_name, exst_fld_w_values)


    # Calculate field
    print '\n  Calculating field [{}] to equal: "{}"\n'.format(new_fld_to_calc, expression)
    arcpy.CalculateField_management(lyr, new_fld_to_calc, expression, 'PYTHON_9.3')
    arcpy.Delete_management(lyr)


    print('Finished Join_and_Calc_Fields_CPASG()')
    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                    FUNCTION Join 2 Objects by Attribute

def Join_2_Objects_By_Attr(target_obj, target_join_field, to_join_obj, to_join_field, join_type):
    """
    PARAMETERS:
      target_obj (str): The full path to the FC or Table that you want to have
        another object join to.

      target_join_field (str): The field name in the target_obj to be used as the
        primary key.

      to_join_obj (str): The full path to the FC or Table that you want to join
        to the target_obj.

      to_join_field (str): The field name in the to_join_obj to be used as the
        foreign key.

      join_type (str): Specifies what will be done with records in the input
        that match a record in the join table. Valid values:
          KEEP_ALL
          KEEP_COMMON

    RETURNS:
      target_obj (lyr): Return the layer/view of the joined object so that
        it can be processed.

    FUNCTION:
      To join two different objects via a primary key field and a foreign key
      field by:
        1) Creating a layer or table view for each object ('target_obj', 'to_join_obj')
        2) Joining the layer(s) / view(s) via the 'target_join_field' and the
           'to_join_field'

    NOTE:
      This function returns a layer/view of the joined object, remember to delete
      the joined object (arcpy.Delete_management(target_obj)) if performing
      multiple joins in one script.
    """

    print '\n    Starting Join_2_Objects_By_Attr()...'

    # Create the layer or view for the target_obj using try/except
    try:
        arcpy.MakeFeatureLayer_management(target_obj, 'target_obj')
        ##print '      Made FEATURE LAYER for: {}'.format(target_obj)
    except:
        arcpy.MakeTableView_management(target_obj, 'target_obj')
        ##print '      Made TABLE VIEW for: {}'.format(target_obj)

    # Create the layer or view for the to_join_obj using try/except
    try:
        arcpy.MakeFeatureLayer_management(to_join_obj, 'to_join_obj')
        ##print '      Made FEATURE LAYER for: {}'.format(to_join_obj)
    except:
        arcpy.MakeTableView_management(to_join_obj, 'to_join_obj')
        ##print '      Made TABLE VIEW for: {}'.format(to_join_obj)

    # Join the layers
    print '      Joining "{}"\n         With "{}"\n           On "{}"\n          And "{}"\n         Type "{}"'.format(target_obj, to_join_obj, target_join_field, to_join_field, join_type)
    arcpy.AddJoin_management('target_obj', target_join_field, 'to_join_obj', to_join_field, join_type)

    # Delete the lyr/view that is no longer needed
    arcpy.Delete_management('to_join_obj')

    # Print the fields (only really needed during testing)
##    fields = arcpy.ListFields('target_obj')
##    print '\n  Fields in joined layer:'
##    for field in fields:
##        print '    ' + field.name

    print '    Finished Join_2_Objects_By_Attr()'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
