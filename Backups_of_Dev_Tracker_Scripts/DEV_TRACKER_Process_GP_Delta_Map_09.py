#-------------------------------------------------------------------------------

# Purpose:
"""
POLYGONS/DENSITY Data Processing

To merge the data from the following scripts:
  DEV_TRACKER_Process_Approved_DU_Map_04.py
and
  DEV_TRACKER_Process_In_Process_DU_Map_07.py

then find the delta between:
  The merged data
with
  The original housing model (From Map 01)

Intent to show the Approved and In Process DU's above/below the estimated capacity
(PDS_HOUSING_MODEL_OUTPUT_2011).

This script uses the 'READY2BIN' data from both the Map 04 script and the Map 07 script
Therefore this script should only be run if map 04 and 07 have been sucessfully
run.


The output should be polygons with a density field named [DENSITY]
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
    shorthand_name    = 'GP_Delta_Map_09'


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


    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder      = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder          = '{}\{}'.format(root_folder, 'Data')

    wkg_fgdb             = '{}\{}'.format(data_folder, '{}.gdb'.format(shorthand_name))

    approved_DU_Map_04   = '{}\{}\{}'.format(data_folder, 'Approved_DU_Map_04.gdb', 'Parcels_joined_diss_expld_READY2BIN')

    in_process_DU_Map_07 = '{}\{}\{}'.format(data_folder, 'In_Process_DU_Map_07.gdb', 'Parcels_joined_diss_expld_READY2BIN')


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Paths to SDE Feature Classes
    PDS_HOUSING_MODEL_OUTPUT_2011 = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + 'PDS_HOUSING_MODEL_OUTPUT_2011')


    # Set field names
    record_id_fld = 'RECORD_ID'
    density_fld   = 'DENSITY'
    housing_model_density_fld = 'EFFECTIVE_DENSITY'


    # Misc variables
    success = True
    data_pass_QAQC_tests = True


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
    #                      Delete and Create FGDBs if needed
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # Delete and create working FGDB
            if arcpy.Exists(wkg_fgdb):
                print 'Deleting FGDB at:\n  {}\n'.format(wkg_fgdb)
                arcpy.Delete_management(wkg_fgdb)

            if not arcpy.Exists(wkg_fgdb):
                out_folder_path, out_name = os.path.split(wkg_fgdb)
                print 'Creating FGDB at:\n  {}\n'.format(wkg_fgdb)
                arcpy.CreateFileGDB_management(out_folder_path, out_name)

        except Exception as e:
            success = False
            print '\n*** ERROR with Creating FGDBs ***'
            print str(e)


    #---------------------------------------------------------------------------
    #       Find any Overlaps between the Approved and In Process DU's
    #---------------------------------------------------------------------------
    if success == True:
        try:
            data_pass_QAQC_tests = Find_Overlaps(wkg_fgdb, approved_DU_Map_04, in_process_DU_Map_07, record_id_fld)

        except Exception as e:
            success = False
            print '\n*** ERROR with Find_Overlaps() ***'
            print str(e)


    #---------------------------------------------------------------------------
    #               Merge the Approved and In Process DU's
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # Merge the Applicant GPA and County GPA
            in_features = [approved_DU_Map_04, in_process_DU_Map_07]
            merged_fc = os.path.join(wkg_fgdb, 'Aprovd_InProces_merge')
            print('\n---------------------------------------------------------')
            print 'Merging:'
            for f in in_features:
                print '  {}'.format(f)
            print 'To create:\n  {}\n'.format(merged_fc)
            arcpy.Merge_management(in_features, merged_fc)

        except Exception as e:
            success = False
            print '\n*** ERROR with Merging FCs ***'
            print str(e)


    #---------------------------------------------------------------------------
    #           Intersect the Merged DUs with the Housing Model Output
    #---------------------------------------------------------------------------
    if success == True:
        try:
            int_fc_name = '{}_HOUSING_OUTPUT_int'.format(os.path.basename(merged_fc))
            Find_Density_Delta(merged_fc, density_fld, PDS_HOUSING_MODEL_OUTPUT_2011, housing_model_density_fld, int_fc_name, record_id_fld)

        except Exception as e:
            success = False
            print '\n*** ERROR with Find_Density_Delta() ***'
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
    print 'Data passed QA/QC tests = {}'.format(data_pass_QAQC_tests)
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
def Find_Overlaps(wkg_fgdb, fc_1, fc_2, record_id_fld):
    """
    To find and report on the overlaps between two FC's
    """

    print('\n----------------------------------------------------------------')
    print('Starting Find_Overlaps():')

    data_pass_QAQC_tests = True

    # Intersect the two FC's to see if there are any overlaps
    print('  Intersect two FCs to see if there are any overlaps:')
    in_features = [fc_1, fc_2]
    intersect_fc = os.path.join(wkg_fgdb, 'Aprovd_InProces_int')
    print '\n    Intersecting:'
    for fc in in_features:
        print '      {}'.format(fc)
    print '    To create FC:\n      {}\n'.format(intersect_fc)
    arcpy.Intersect_analysis(in_features, intersect_fc)


    # Find out if there are any overlapping parcels
    overlap = False
    with arcpy.da.SearchCursor(intersect_fc, 'OBJECTID') as cursor:
        for row in cursor:
            overlap = True
            break

    if overlap == False:
        print '  OK! There are no overlapping parcels\n'

    # If there is an overlap, get a unique list of the parcels that overlap and report on them
    if overlap == True:
        data_pass_QAQC_tests = False

        print('  INFO!  There are overlapping parcels:\n')
        print('    Report format is <Record ID 1> overlaps with <Record ID 2>')
        print('      RECORD ID 1 is from:\n        {}'.format(fc_1))
        print('      RECORD ID 2 is from:\n        {}\n'.format(fc_2))

        projects_that_overlap = []
        fields = [record_id_fld, '{}_1'.format(record_id_fld), 'Shape_Area']
        with arcpy.da.SearchCursor(intersect_fc, fields) as int_cursor:
            for row in int_cursor:
                rec_id_1 = row[0]
                rec_id_2 = row[1]

                report = '    RECORD ID: "{}" overlaps with "{}"'.format(rec_id_1, rec_id_2)
                if report not in projects_that_overlap:
                    projects_that_overlap.append(report)
        del int_cursor

        for report in projects_that_overlap:
            print report

    #---------------------------------------------------------------------------
    print ('\nFinished Find_Overlaps()')
    return data_pass_QAQC_tests

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Find_Density_Delta(fc_1, density_fld_fc1, fc_2, density_fld_fc2, int_fc_name, record_id_fld):
    """
    """
    print('\n-----------------------------------------------------------------')
    print('Starting Find_Density_Delta()')


    # Set variables
    density_delta_fld = 'Density_Delta'
    final_density_fld = 'DENSITY'

    print('\n  FC 1:\n    {}'.format(fc_1))
    print('  FC 2:\n    {}'.format(fc_2))

    #---------------------------------------------------------------------------
    #                       Intersect fc_1 with fc_2
    in_features = [fc_1, fc_2]
    wkg_fgdb = os.path.dirname(fc_1)
    intersect_fc = os.path.join(wkg_fgdb, int_fc_name)
    print '\n  Intersecting:'
    for fc in in_features:
        print '    {}'.format(fc)
    print '  To create FC:\n    {}\n'.format(intersect_fc)
    arcpy.Intersect_analysis(in_features, intersect_fc)


    #---------------------------------------------------------------------------
    #                      Add field to hold Density Delta
    print '\n  Adding field:'
    field_name = density_delta_fld
    field_type = 'DOUBLE'
    print '    [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(intersect_fc, field_name, field_type)


    #---------------------------------------------------------------------------
    #                     Calculate the Density Delta
    expression = '!{}!-!{}!'.format(density_fld_fc1, density_fld_fc2)
    print '\n  Calculating field [{}] to equal: {}\n'.format(density_delta_fld, expression)
    arcpy.CalculateField_management(intersect_fc, density_delta_fld, expression, 'PYTHON_9.3')


    #---------------------------------------------------------------------------
    #          Dissolve to reduce rows and remove unneeded fields
    dissolve_fields = [record_id_fld, density_fld_fc1, density_fld_fc2, density_delta_fld]

    dissolve_fc     = os.path.join(wkg_fgdb, '{}_diss_READY2BIN'.format(os.path.basename(intersect_fc)))
    print '\n  Dissolving FC:\n    {}\n  To:\n    {}\n  On Fields:'.format(intersect_fc, dissolve_fc)
    for f in dissolve_fields:
        print '    {}'.format(f)

    arcpy.Dissolve_management(intersect_fc, dissolve_fc, dissolve_fields, '#', 'SINGLE_PART')


    #---------------------------------------------------------------------------
    #                         Rename Fields for Readability

    print('\n  Renaming fields for readability to FC:\n    {}\n'.format(dissolve_fc))

    old_name = density_fld_fc1
    new_name = 'Density_from_FC_1'
    print('    Changing field name from: [{}] to: [{}]'.format(old_name, new_name))
    arcpy.AlterField_management(dissolve_fc, old_name, new_name, new_name)

    old_name = density_fld_fc2
    new_name = 'Density_from_FC_2'
    print('    Changing field name from: [{}] to: [{}]'.format(old_name, new_name))
    arcpy.AlterField_management(dissolve_fc, old_name, new_name, new_name)

    #---------------------------------------------------------------------------
    #           Add [DENSITY] field and calc to equal Density Delta
    # This is also done for readability and so the BINNING script will use the
    # correct field: [DENSITY].
    print '\n  Adding field:'
    field_name = final_density_fld
    field_type = 'DOUBLE'
    print '    [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(dissolve_fc, field_name, field_type)

    # Calculate
    expression = '!{}!'.format(density_delta_fld)
    print '\n  Calculating field [{}] to equal: {}\n'.format(final_density_fld, expression)
    arcpy.CalculateField_management(dissolve_fc, final_density_fld, expression, 'PYTHON_9.3')

    print('Finished Find_Density_Delta()')
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
