#-------------------------------------------------------------------------------

# Purpose:
"""
POLYGONS/DENSITY Data Processing

Process the Approved GPA (Map 02)

To create a polygon feature class from a CSV when you want a shape of a project
with a DENSITY for the whole project

The CSV needs to have an APN field

The output should be polygons with a density field named [DENSITY]
"""
#
# Author:      mgrue
#
# Created:     24/07/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, os, math, datetime, ConfigParser, time, sys

arcpy.env.overwriteOutput = True

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Approved_GPA_Map_02'


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
    name_of_csv       = 'Approved General Plan Amendments (2011 General Plan Forward) (Map 2).csv'
    path_to_csv       = os.path.join(folder_with_formatted_csvs, name_of_csv)

    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder       = '{}\{}'.format(root_folder, 'Data')

    imported_csv_fgdb = '{}\{}'.format(data_folder, '1_Imported_CSVs.gdb')

    wkg_fgdb          = '{}\{}'.format(data_folder, '{}.gdb'.format(shorthand_name))


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Paths to SDE Feature Classes
    PARCELS_ALL       = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + 'PARCELS_ALL')
    PARCEL_HISTORICAL = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + 'PARCEL_HISTORICAL')


    # Set field names
    apn_fld       = 'PARCEL_NBR'
    record_id_fld = 'RECORD_ID'
    proj_name_fld = 'PROJECT_NAME'
    du_fld        = 'DWP'


    # Misc variables
    success = True
    data_pass_QAQC_tests = True


    # This is the acreage that an overlap of a current parcel and a historic parcel
    # from two different projects needs to be greater than in order for the
    # script to flag it as needing human analysis
    acreage_cutoff_for_overlap = 0.1


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
    #                      Create FGDBs if needed
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # Create import FGDB if it does not exist
            if not arcpy.Exists(imported_csv_fgdb):
                out_folder_path, out_name = os.path.split(imported_csv_fgdb)
                print 'Creating FGDB at:\n  {}\n'.format(imported_csv_fgdb)
                arcpy.CreateFileGDB_management(out_folder_path, out_name)


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


    #-------------------------------------------------------------------
    #                   Import CSV into FGDB Table
    #-------------------------------------------------------------------
    if success == True:
        try:
            # Set paths to Feature Classes / Tables
            name_of_csv_table = '{}_Tbl'.format(shorthand_name)
            csv_table = os.path.join(imported_csv_fgdb, name_of_csv_table)

            print '------------------------------------------------------------------'
            print 'Importing CSV to FGDB Table:\n  From:\n    {}'.format(path_to_csv)
            print '  To:\n    {}\{}'.format(imported_csv_fgdb, os.path.basename(csv_table))

            # Import CSV to FGDB Table
            arcpy.TableToTable_conversion(path_to_csv, imported_csv_fgdb, os.path.basename(csv_table))

        except Exception as e:
            success = False
            print '\n*** ERROR with Importing CSV ***'
            print str(e)

    #---------------------------------------------------------------------------
    #         Get the parcels from PARCELS_ALL and PARCEL_HISTORICAL
    #---------------------------------------------------------------------------
    if success == True:
        # Get parcels
        try:

            # Set path for the FC to be created from PARCELS_ALL
            out_name             = 'From_PARCELS_ALL'
            from_parcels_all_fc  = os.path.join(wkg_fgdb, out_name)

            # Set path for the FC to be created from PARCEL_HISTORICAL
            out_name             = 'From_PARCEL_HISTORICAL'
            from_parcels_hist_fc = os.path.join(wkg_fgdb, out_name)

            Get_Parcels(csv_table, PARCELS_ALL, PARCEL_HISTORICAL, from_parcels_all_fc, from_parcels_hist_fc, apn_fld)

        except Exception as e:
            success = False
            print '*** ERROR with Get_Parcels() ***'
            print str(e)


    if success == True:
        # Get lists of found (or not found) APNs
        try:
            (apns_from_imported_csv,
            apns_found_in_parcels_all,
            apns_found_in_parcels_hist,
            apns_not_found_anywhere) = Get_APN_Lists(csv_table, from_parcels_all_fc, from_parcels_hist_fc, apn_fld)

        except Exception as e:
            success = False
            print '*** ERROR with Get_APN_Lists() ***'
            print str(e)


    #---------------------------------------------------------------------------
    #         Perform QA/QC on the extracted data and the parcels
    #---------------------------------------------------------------------------
    if success == True:
        try:
            data_pass_QAQC_tests = QA_QC(csv_table, from_parcels_all_fc, from_parcels_hist_fc, apns_from_imported_csv, apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere, apn_fld, record_id_fld, du_fld, acreage_cutoff_for_overlap)

        except Exception as e:
            success = False
            print '*** ERROR with QA_QC() ***'
            print str(e)

    #---------------------------------------------------------------------------
    #                       Determine if we need to
    #     merge the FC's 'From_PARCELS_ALL' and 'From_PARCEL_HISTORICAL'
    #           or if we only need to work with 'From_PARCELS_ALL'
    #---------------------------------------------------------------------------
    if success == True:
        if not arcpy.Exists(from_parcels_hist_fc):  # Then there were no parcels from PARCEL_HISTORICAL (nothing to merge)

            # Set that we want to join to the 'From PARCELS_ALL FC' and set the name of the joined FC
            fc_to_be_joined = from_parcels_all_fc
            joined_name     = 'Parcels_ALL_joined'

        else:  # Then there were parcels from PARCEL_HISTORICAL and we want to merge those with parcels from PARCELS_ALL

            # Merge the current and historical parcels
            in_features = [from_parcels_all_fc, from_parcels_hist_fc]
            merged_fc = os.path.join(wkg_fgdb, 'Parcels_ALL_and_HIST_merge')
            print '\nMerging:'
            for f in in_features:
                print '  {}'.format(f)
            print 'To create:\n  {}\n'.format(merged_fc)
            arcpy.Merge_management(in_features, merged_fc)

            # Set that we want to join to the merged FC and set the name of the joined FC
            fc_to_be_joined = merged_fc
            joined_name     = '{}_joined'.format(os.path.basename(merged_fc))


    #---------------------------------------------------------------------------
    #   Join the Parcels with the Imported Table and save in order to get the
    # shapes (from the parcels) and the tabular data (from the imported table)
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # Create a layer with the Imported Table joined to the parcel FC
            print '\nJoining Imported Table to the Parcel FC'
            joined_tbl_lyr = Join_2_Objects_By_Attr(fc_to_be_joined, 'APN', csv_table, apn_fld, 'KEEP_ALL')

            # Save the joined layer to disk
            parcels_joined_fc = os.path.join(wkg_fgdb, joined_name)
            print 'Saving joined layer to:\n  {}\n'.format(parcels_joined_fc)
            arcpy.FeatureClassToFeatureClass_conversion(joined_tbl_lyr, wkg_fgdb, joined_name)
            arcpy.Delete_management(joined_tbl_lyr)

        except Exception as e:
            success = False
            print '*** ERROR with Joining / Saving the Parcel FC with the Imported Table ***'
            print str(e)

    #---------------------------------------------------------------------------
    #                    Clean-up the joined data field names
    #---------------------------------------------------------------------------
    # Rename the fields in the joined FC back to what they were named in the CSV
    # The renaming will simplify readability and scripting below:
    #    The join performed above names the CSV fields with a prefix of the
    #    table that they came from.
    #    I.e. "In_Process_Applicant_GPAs_Tbl_RECORD_ID" will be changed back to "RECORD_ID"
    if success == True:
        try:
            prefix_to_remove = '{}_'.format(os.path.basename(csv_table))

            Remove_FieldName_Prefix(parcels_joined_fc, prefix_to_remove)

        except Exception as e:
            success = False
            print '*** ERROR with Remove_FieldName_Prefix() ***'
            print str(e)

    #---------------------------------------------------------------------------
    #                      Get the DENSITY per project
    #---------------------------------------------------------------------------
    if success == True:
        try:
            Get_DENSITY_Per_Project(parcels_joined_fc, record_id_fld, proj_name_fld, du_fld)

        except Exception as e:
            success = False
            print '*** ERROR with Get_DENSITY_Per_Project() ***'
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
def Get_Parcels(csv_table, PARCELS_ALL, PARCEL_HISTORICAL, from_parcels_all_fc, from_parcels_hist_fc, apn_fld):
    """
    Get the parcel footprint and tabular data from PARCELS_ALL and PARCEL_HISTORICAL
    and select which parcels to export from the csv_table. Save the exports to
    "from_parcels_all_fc" and "from_parcels_hist_fc"
    """

    print '\n--------------------------------------------------------------------'
    print 'Start Get_Parcels()\n'

    print '  Getting APNs from table:\n    {}'.format(csv_table)

    # Format the APN field to remove the dashes
    expression = '!{}!.replace("-","")'.format(apn_fld)
    print '\n  Removing dashes in the field "{}" to equal: {}\n'.format(apn_fld, expression)
    arcpy.CalculateField_management(csv_table, apn_fld, expression, 'PYTHON_9.3')

    # Get a list of parcels from the APN table
    print '  Getting a list of unique parcels from the APN table:'
    unique_apns_in_csv = []  # List of unique APNs
    count = 0
    with arcpy.da.SearchCursor(csv_table, [apn_fld]) as cursor:
        for row in cursor:
            apn = row[0]

            if apn not in unique_apns_in_csv:
                unique_apns_in_csv.append(apn)

            count += 1
    del cursor
    print '    There are a total of "{}" rows in the APN table'.format(count)
    print '    There are "{}" unique APNs in the APN table\n'.format(len(unique_apns_in_csv))


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           PARCELS_ALL
    #          Select from PARCELS_ALL and export to local FGDB

    # Make Feature Layer for PARCELS_ALL
    arcpy.MakeFeatureLayer_management(PARCELS_ALL, 'parcels_all_lyr')

    # Select parcels from PARCELS_ALL that are in the APN table
    print '  ------------------------------------------------------------------'
    print '  Selecting parcels from PARCELS_ALL that are in the APN table:'
    for apn in unique_apns_in_csv:

        where_clause = "APN = '{}'".format(apn)
        ##print 'Finding APN: {}'.format(apn)  # For testing
        arcpy.SelectLayerByAttribute_management('parcels_all_lyr', 'ADD_TO_SELECTION', where_clause)

    # Get the count of selected parcels
    print '    Getting count of selected parcels:'
    count = Get_Count_Selected('parcels_all_lyr')

    # Export the selected parcels (if any)
    if count != 0:
        out_path, out_name = os.path.split(from_parcels_all_fc)
        print '  Exporting "{}" selected parcels from PARCELS_ALL to:\n    {}\{}'.format(count, out_path, out_name)
        arcpy.FeatureClassToFeatureClass_conversion('parcels_all_lyr', out_path, out_name)
    else:
        '    No features selected from PARCELS_ALL'

    # Delete the layer with the selection on it
    arcpy.Delete_management('parcels_all_lyr')


    #---------------------------------------------------------------------------
    #        Find out which APNs from the CSV were not found in PARCELS_ALL

    print '\n  Finding out which APNs from the APN table were not found in PARCELS_ALL:'

    # First get a list of parcels that WERE found in PARCELS_ALL
    apns_found_in_parcels_all = []
    apns_not_found_in_parcels_all = []
    with arcpy.da.SearchCursor(from_parcels_all_fc, ['APN']) as cursor:
        for row in cursor:
            apns_found_in_parcels_all.append(row[0])
    del cursor

    # Next, get a list of parcels that were NOT found in PARCELS_ALL
    for apn in unique_apns_in_csv:
        if apn not in apns_found_in_parcels_all:
            apns_not_found_in_parcels_all.append(apn)

    # Determine if we need to search PARCEL_HISTORICAL
    if len(apns_not_found_in_parcels_all) == 0:
        search_historic_parcels = False
        print '    All APNs in table were found in PARCELS_ALL, no need to search PARCEL_HISTORICAL\n'

    else:
        search_historic_parcels = True
        print '    There were "{}" APNs not found in PARCELS_ALL, searching PARCEL_HISTORICAL\n'.format(len(apns_not_found_in_parcels_all))


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           PARCEL_HISTORICAL
    #          Select from PARCEL_HISTORICAL and export to local FGDB

    apns_found_in_parcels_hist = []
    apns_not_found_anywhere = []

    if search_historic_parcels == True:

        # Make Feature Layer for PARCEL_HISTORICAL
        arcpy.MakeFeatureLayer_management(PARCEL_HISTORICAL, 'parcels_historical_lyr')

        # Select parcels from PARCEL_HISTORICAL that are in the APN table
        print '  ------------------------------------------------------------------'
        print '  Selecting parcels from PARCEL_HISTORICAL that are in the APN table:'
        for apn in apns_not_found_in_parcels_all:

            where_clause = "APN = '{}'".format(apn)
            ##print 'Finding APN: {}'.format(apn)  # For testing
            arcpy.SelectLayerByAttribute_management('parcels_historical_lyr', 'ADD_TO_SELECTION', where_clause)

        # Get the count of selected parcels
        print '    Getting count of selected parcels:'
        count = Get_Count_Selected('parcels_historical_lyr')

        # Export the selected parcels (if any)
        if count != 0:
            out_path, out_name = os.path.split(from_parcels_hist_fc)
            print '  Exporting "{}" selected parcels from PARCEL_HISTORICAL to:\n    {}\{}'.format(count, out_path, out_name)
            arcpy.FeatureClassToFeatureClass_conversion('parcels_historical_lyr', out_path, out_name)
        else:
            '  No features selected from PARCEL_HISTORICAL'

        # Delete the layer with the selection on it
        arcpy.Delete_management('parcels_historical_lyr')

    print '\nFinished Get_Parcels()'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Get_APN_Lists(csv_table, from_parcels_all_fc, from_parcels_hist_fc, apn_fld):
    """
    Get and Return lists of:
      All APN's that are in the csv_table
      Unique APN's that were found from PARCELS_ALL
      Unique APN's that were found from PARCEL_HISTORICAL
      Unique APN's that were not found anywhere
    """
    print '\n--------------------------------------------------------------------'
    print 'Start Get_APN_Lists()\n'

    # Create lists
    apns_from_imported_csv     = []
    apns_found_in_parcels_all  = []
    apns_found_in_parcels_hist = []
    apns_not_found_anywhere    = []


    # Find list of all APNs from the imported CSV table
    if arcpy.Exists(csv_table):
        print '  Getting all APNs from Imported Table:\n    {}'.format(csv_table)
        fields = [apn_fld]
        with arcpy.da.SearchCursor(csv_table, fields) as cursor:
            for row in cursor:
                apn = row[0]
                apns_from_imported_csv.append(apn)
        del cursor
    print '    There were "{}" APNs (Total--not unique) from the Import Table'.format(len(apns_from_imported_csv))
    print '    There were "{}" Unique APNs from the Import Table\n'.format(len(set(apns_from_imported_csv)))


    # Find unique list of APNs from PARCELS_ALL
    if arcpy.Exists(from_parcels_all_fc):
        print '  Getting APNs from FC:\n    {}'.format(from_parcels_all_fc)
        fields = ['APN']
        with arcpy.da.SearchCursor(from_parcels_all_fc, fields) as cursor:
            for row in cursor:
                apn = row[0]

                if apn not in apns_found_in_parcels_all:
                    apns_found_in_parcels_all.append(apn)
        del cursor
    print '    There were "{}" unique parcels found from PARCELS_ALL\n'.format(len(apns_found_in_parcels_all))


    # Find unique list of APNs from PARCEL_HISTORICAL
    if arcpy.Exists(from_parcels_hist_fc):
        print '  Getting APNs from FC:\n    {}'.format(from_parcels_hist_fc)
        fields = ['APN']
        with arcpy.da.SearchCursor(from_parcels_hist_fc, fields) as cursor:
            for row in cursor:
                apn = row[0]

                if apn not in apns_found_in_parcels_hist:
                    apns_found_in_parcels_hist.append(apn)
        del cursor
    print '    There were "{}" unique parcels found from PARCEL_HISTORICAL\n'.format(len(apns_found_in_parcels_hist))


    # Find unique list of APNs not found anywhere
    print '  Getting APNs that were not found in PARCELS_ALL or PARCEL_HISTORICAL'
    for csv_apn in apns_from_imported_csv:
        if (csv_apn not in apns_found_in_parcels_all) and (csv_apn not in apns_found_in_parcels_hist):
            if csv_apn not in apns_not_found_anywhere:
                apns_not_found_anywhere.append(csv_apn)
    print '    There were "{}" unique parcels not found in either FC\n'.format(len(apns_not_found_anywhere))


    print 'Finished Get_APN_Lists()'

    return apns_from_imported_csv, apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def QA_QC(csv_table, from_parcels_all_fc, from_parcels_hist_fc, apns_from_imported_csv, apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere, apn_fld, record_id_fld, du_fld, acreage_cutoff_for_overlap):
    """
    Perform QA/QC on the csv_table.  The below checks are performed:
      1)  Which APNs from the CSV were not found in PARCELS_ALL or PARCEL_HISTORICAL?
      2)  Find if Parcels showed up more than one time in the CSV table
      3)  Is there an overlap with a current parcel and an historic parcel?
      4)  Check any critical fields to ensure there are no blank values

    This is only for reporting purposes, this function does not edit the data
    """

    print '\n--------------------------------------------------------------------'
    print 'Start QA_QC()'

    data_pass_QAQC_tests = True

    #---------------------------------------------------------------------------
    # 1)  Which APNs from the CSV were not found in PARCELS_ALL or PARCEL_HISTORICAL?
    print '\n  1) Finding which APNs from the CSV were not found in PARCELS_ALL or PARCEL_HISTORICAL:\n'

    if len(apns_not_found_anywhere) == 0:
        print '\n    OK! All APNs were found in either PARCELS_ALL or PARCEL_HISTORICAL'

    else:
        data_pass_QAQC_tests = False
        print '    WARNING!  There are "{}" APNs that were not found in PARCELS_ALL or PARCEL_HISTORICAL:'.format(len(apns_not_found_anywhere))
        for apn in apns_not_found_anywhere:
            print '      APN:  {}'.format(apn)

            # Get the Record ID(s) associated with that APN
            fields = [apn_fld, record_id_fld]
            where_clause = "{} = '{}'".format(apn_fld, apn)
            with arcpy.da.SearchCursor(csv_table, fields, where_clause) as cursor:
                for row in cursor:
                    print '        With Record ID: {}'.format(row[1])

            del cursor


    #---------------------------------------------------------------------------
    # 2)  Find if Parcels showed up more than one time in the CSV table
    print '\n\n  2) Finding if parcels showed up more than one time in the CSV table:\n'

    # Get a list of parcels from the APN table
    unique_apns_in_csv = []  # List of unique APNs
    duplicate_apns_in_csv = []
    for apn in apns_from_imported_csv:
        if apn not in unique_apns_in_csv:
            unique_apns_in_csv.append(apn)
        elif apn not in duplicate_apns_in_csv:
            duplicate_apns_in_csv.append(apn)

    if len(duplicate_apns_in_csv) == 0:
        print '    OK! There were 0 duplicate APNs found in the CSV extract'

    else:
        data_pass_QAQC_tests = False
        print '\n    WARNING!  There are "{}" APNs that were duplicated in the CSV:'.format(len(duplicate_apns_in_csv))
        for apn in duplicate_apns_in_csv:
            print '      APN: {}'.format(apn)

            # Get the Record ID(s) associated with that APN
            fields = [apn_fld, record_id_fld]
            where_clause = "{} = '{}'".format(apn_fld, apn)
            with arcpy.da.SearchCursor(csv_table, fields, where_clause) as cursor:
                for row in cursor:
                    print '        With Record ID: {}'.format(row[1])

        print '\n    This might mean that only the parcel from the newest project'
        print '    should be considered in the analysis.  Further human analysis needed.'



    #---------------------------------------------------------------------------
    # 3)  Is there an overlap with a current parcel and an historic parcel?
    print '\n\n  3) Finding any overlaps with current parcels and historic parcels:'

    # Check to see if any parcels came from PARCEL_HISTORICAL, no need to check
    #   If there are no parcels from PARCEL_HISTORICAL
    if not arcpy.Exists(from_parcels_hist_fc):
        print '      OK! There were no parcels found in PARCEL_HISTORICAL'
        print '      Therefore there can be no overlap'

    else:  # There might be an overlap, continue checking...

        # Intersect the two FC's to see if there are any overlaps
        in_features = [from_parcels_all_fc, from_parcels_hist_fc]
        wkg_fgdb = os.path.dirname(from_parcels_all_fc)
        intersect_fc = os.path.join(wkg_fgdb, 'Parcels_ALL_and_HIST_int')
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
            print '    OK! There are no overlapping parcels\n'

        # If there is an overlap, get a list of the parcels that overlap and report on them
        if overlap == True:
            print '    INFO!  There are overlapping parcels from current and historic parcels:\n'
            apns_that_overlap = []
            fields = ['APN', 'APN_1', 'Shape_Area']
            with arcpy.da.SearchCursor(intersect_fc, fields) as int_cursor:
                for row in int_cursor:
                    apn_1 = row[0]
                    apn_2 = row[1]
                    sq_ft = row[2]

                    # Get the acreage of the overlap feature
                    acreage = sq_ft/43560

                    if acreage <= acreage_cutoff_for_overlap:
                        print '      APN: "{}" overlaps with APN: "{}"'.format(apn_1, apn_2)
                        print '      but the overlap ({} acres) is <= the script-defined cutoff for analysis ({} acres)'.format(acreage, acreage_cutoff_for_overlap)

                    # Only analyze overlaps that are large enough to matter
                    if acreage > acreage_cutoff_for_overlap:

                        # Set which apn is current and which is historical
                        if apn_1 in apns_found_in_parcels_hist:
                            historic_apn = apn_1
                        if apn_1 in apns_found_in_parcels_all:
                            current_apn = apn_1

                        if apn_2 in apns_found_in_parcels_hist:
                            historic_apn = apn_2
                        if apn_2 in apns_found_in_parcels_all:
                            current_apn = apn_2

                        # Get the Record ID(s) associated with the historic APN
                        record_ids_historic = []
                        fields = [apn_fld, record_id_fld]
                        where_clause = "{} = '{}'".format(apn_fld, historic_apn)
                        with arcpy.da.SearchCursor(csv_table, fields, where_clause) as csv_cursor:
                            for row in csv_cursor:
                                record_ids_historic.append(row[1])
                        del csv_cursor

                        # Get the Record ID(s) associated with the current APN
                        record_ids_current = []
                        fields = [apn_fld, record_id_fld]
                        where_clause = "{} = '{}'".format(apn_fld, current_apn)
                        with arcpy.da.SearchCursor(csv_table, fields, where_clause) as csv_cursor:
                            for row in csv_cursor:
                                record_ids_current.append(row[1])
                        del csv_cursor

                        # If the apn of the current and the apn of the historic overlapping parcels
                        # are each only in one project, and if the project is the same project,
                        # then the dissolve that happens below will remove any double-counting
                        if (len(record_ids_current) == 1) and (len(record_ids_historic) == 1) and (record_ids_current[0] == record_ids_historic[0]):
                                print '      There is overlap between CURRENT parcel "{}" and HISTORIC parcel "{}"'.format(current_apn, historic_apn)
                                print '      But as both are from the same project: "{}", there will be no overlap when the data is dissolved'.format(record_ids_current[0])
                                print '      No need for human analysis, but PDS may want to know that they should update the historic apn in the above project\n'
                        else:
                            data_pass_QAQC_tests = False
                            print '      WARNING!  The overlap between CURRENT parcel "{}" and HISTORIC parcel "{}" may cause double counting'.format(current_apn, historic_apn)
                            print '      Please let PDS know that they should remove the historic parcel and add current parcel(s) in Accela for project {}\n'.format(record_ids_historic[0])

            del int_cursor


    #---------------------------------------------------------------------------
    # 4)  Check any critical fields to ensure there are no blank values
    print '\n  4) Finding any critical fields that are blank in imported CSV table:\n'
    critical_fields = [record_id_fld, apn_fld, du_fld]
    for f in critical_fields:

        # Set the where clause
        if f == du_fld:  # Set a where clause for an integer field
            where_clause = "{0} IS NULL".format(f)
        else:  # Set a where clause for a string field
            where_clause = "{0} IS NULL or {0} = ''".format(f)

        # Get list of ids
        print '    Checking where: {}:'.format(where_clause)
        ids_w_nulls = []  # List to hold the ID of reports with null values
        with arcpy.da.SearchCursor(csv_table, critical_fields, where_clause) as cursor:
            for row in cursor:
                record_id = row[0]
                ids_w_nulls.append(record_id)
        del cursor

        # Get a sorted list of only unique values
        ids_w_nulls = sorted(set(ids_w_nulls))

        # Report on the sorted list
        if len(ids_w_nulls) != 0:
            data_pass_QAQC_tests = False
            print '      WARNING! There are records in the CSV extract that have a blank value in column: "{}":'.format(f)
            for id_num in ids_w_nulls:
                if (id_num == None) or (id_num == ''):
                    print '        No Record ID available to report'
                else:
                    print '        {}'.format(id_num)
        if len(ids_w_nulls) == 0:
            print '      OK! No blank values in {}'.format(f)

        print ''


    #---------------------------------------------------------------------------
    print '\n  ----------------------------------------------------------------'
    print '  Data Passed all QA/QC tests = {}\n'.format(data_pass_QAQC_tests)

    print 'Finished QA_QC()'

    return data_pass_QAQC_tests


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Remove_FieldName_Prefix(fc_or_table, prefix_to_remove):
    """
    PARAMETERS:
      fc_or_table (str): Full path to a FGDB FC or Table that has a prefix
        you want removed.

      prefix_to_remove (str): The prefix that you want removed from the beginning
        of the field name.  PROBABLY want to include the underscore "_" at the
        end of the prefix.

    RETURNS:
      None

    FUNCTION:
      Used after performing a join and saving the results.  The field names
      will now include a prefix of the name of the FC or Table that originally
      had the field.  This function will remove that prefix.
    """

    print '\n------------------------------------------------------------------'
    print 'Starting Remove_FieldName_Prefix()'

    # Get list of fields that start with the prefix to remove
    where_clause = '{}*'.format(prefix_to_remove)
    print '\n  Removing Fields that start with:  "{}"\n'.format(where_clause)
    fields = arcpy.ListFields(fc_or_table, where_clause)


    # Rename the fields that satisfied the where_clause
    renamed_count = 0
    not_renamed_count = 0
    for f in fields:
        old_name = f.name
        new_name = old_name.replace(prefix_to_remove,"")

        if new_name != 'OBJECTID':  # Don't try to name a field "OBJECTID", just skip this one
            ##print '    Changing Field: "{}"\n    To:  "{}"'.format(old_name, new_name)  # For testing purposes

            try:
                arcpy.AlterField_management(fc_or_table, old_name, new_name)
                renamed_count += 1
            except Exception as e:
                print '      WARNING! Couldn\'t change field name [{}] to [{}].  Name may already exist'.format(old_name, new_name)
                print '{}\n'.format(str(e))
                not_renamed_count += 1


    print '\n  "{}" fields were renamed'.format(renamed_count)
    if not_renamed_count != 0:
        print '  "{}" fields couldn\'t be renamed'.format(not_renamed_count)

    print '\nFinished Remove_FieldName_Prefix()'
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Get_DENSITY_Per_Project(fc_to_process, record_id_fld, proj_name_fld, du_fld):
    """
    The main goal of this function is to find the DENSITY of each project

    This function:

      Dissolves the fc_to_process to the wkg_fgdb (This gets rid of any stacked
        parcels or PARCELS_ALL and PARCEL_HISTORICAL overlap in the same project)

      Cleans up the dissolve_fc if there are any nulls in the DU or RECORD_ID
        fields

      Add fields

      Calculate fields

      Explode to single-part
    """

    print '\n------------------------------------------------------------------'
    print 'Starting Get_DENSITY_Per_Project()'
    print '  Processing FC at:\n    {}\n'.format(fc_to_process)

    # Get the working FGDB based off of the path for 'fc_to_process'
    wkg_fgdb = os.path.dirname(fc_to_process)

    # Set the names of the fields to be added
    project_acres_fld = 'Project_Acres'
    density_fld       = 'DENSITY'


    #---------------------------------------------------------------------------
    #                  Dissolve to the project level
    # We want one row per project for the density calculation, so we want 'MULTI_PART'

    dissolve_fields = [record_id_fld, proj_name_fld, du_fld]
    dissolve_fc     = os.path.join(wkg_fgdb, 'Parcels_joined_diss')
    print '\n  Dissolving FC:\n    {}\n  On Fields:'.format(fc_to_process)
    for f in dissolve_fields:
        print '    {}'.format(f)
    print '  To create FC:\n    {}'.format(dissolve_fc)

    arcpy.Dissolve_management(fc_to_process, dissolve_fc, dissolve_fields, '#', 'MULTI_PART')


    # Repair geometry to ensure correct geometry calculation below
    print '\n  Repairing Geometry before performing area calculations below'
    arcpy.RepairGeometry_management(dissolve_fc)


    #---------------------------------------------------------------------------
    #                       Cleanup the dissolved FC

    # Delete any records that do not have a value in the Dwelling Unit field
    #   (which would result in not having a value in the Density field)
    print '\n\n  Checking for any records that do not have a value in the Dwelling Unit field'
    print '  since this would cause a null value in the density field, resulting in bad data:'
    where_clause = "{} IS NULL".format(du_fld)
    missing_density_lyr = Select_By_Attribute(dissolve_fc, 'NEW_SELECTION', where_clause)

    # Get count of selected records
    count = Get_Count_Selected(missing_density_lyr)

    if count != 0:
        print '    There were "{}" features where "{}"'.format(count, where_clause)
        print '    Deleting those features now in FC:\n      {}'.format(dissolve_fc)
        arcpy.DeleteFeatures_management(missing_density_lyr)
    else:
        print '    OK! No records missing a value in the Dewlling Unit field'


    # Delete any records that do not have a value in the Record ID field
    print '\n\n  Checking for any records that do not have a value in the Record ID field:'
    where_clause = "{0} IS NULL or {0} = ''".format(record_id_fld)
    missing_record_id_lyr = Select_By_Attribute(dissolve_fc, 'NEW_SELECTION', where_clause)

    # Get count of selected records
    count = Get_Count_Selected(missing_record_id_lyr)

    if count != 0:
        print '    There were "{}" features where "{}"'.format(count, where_clause)
        print '    Deleting those features now in FC:\n      {}'.format(dissolve_fc)
        arcpy.DeleteFeatures_management(missing_record_id_lyr)
    else:
        print '    OK! No records missing a value in the Record ID field'
    arcpy.Delete_management(missing_record_id_lyr)


    #---------------------------------------------------------------------------
    #                  Add fields to hold calculations
    print '\n\n  Adding fields:'

    fields_to_add = [project_acres_fld, density_fld]

    for field_name in fields_to_add:
        field_type = 'DOUBLE'
        print '    [{}] as a:  {}'.format(field_name, field_type)
        arcpy.AddField_management(dissolve_fc, field_name, field_type)


    #---------------------------------------------------------------------------
    #                  Calculate fields to find DENSITY

    # Calc Acres for each row
    expression      = '!shape.area@acres!'
    expression_type = 'PYTHON_9.3'

    print '\n  Calculating field:\n    [{}] = {}\n'.format(project_acres_fld, expression)
    arcpy.CalculateField_management(dissolve_fc, project_acres_fld, expression, expression_type)


    # Calc DENSITY designation for each Project
    expression = "!{}!/!{}!".format(du_fld, project_acres_fld)
    print '\n  Calculating field:\n    [{}] = {}\n'.format(density_fld, expression)
    arcpy.CalculateField_management(dissolve_fc, density_fld, expression, expression_type)


    #---------------------------------------------------------------------------
    #            Explode MULTI_PART to SINGLE_PART (for binning script)

    # Explode multipart to singlepart
    diss_single_part_fc = '{}_expld_READY2BIN'.format(dissolve_fc)
    print '  Exploding multipart to single part from:\n    {}\n  To:\n    {}\n'.format(dissolve_fc, diss_single_part_fc)
    arcpy.MultipartToSinglepart_management(dissolve_fc, diss_single_part_fc)

    # Repair the geometry
    print '  Repairing geometry at:\n    {}\n'.format(diss_single_part_fc)
    arcpy.RepairGeometry_management(diss_single_part_fc)


    #---------------------------------------------------------------------------
    print '\nFinished Get_DENSITY_Per_Project()'
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Select_Object()
def Select_By_Attribute(path_to_obj, selection_type, where_clause):
    """
    PARAMETERS:
      path_to_obj (str): Full path to the object (Feature Class or Table) that
        is to be selected.

      selection_type (str): Selection type.  Valid values are:
        NEW_SELECTION
        ADD_TO_SELECTION
        REMOVE_FROM_SELECTION
        SUBSET_SELECTION
        SWITCH_SELECTION
        CLEAR_SELECTION

      where_clause (str): The SQL where clause.

    RETURNS:
      'lyr' (lyr): The layer/view with the selection on it.

    FUNCTION:
      To perform a selection on the object.
    """

    ##print 'Starting Select_Object()...'

    # Use try/except to handle either object type (Feature Layer / Table)
    try:
        arcpy.MakeFeatureLayer_management(path_to_obj, 'lyr')
    except:
        arcpy.MakeTableView_management(path_to_obj, 'lyr')

    ##print '  Selecting "lyr" with a selection type: {}, where: "{}"'.format(selection_type, where_clause)
    arcpy.SelectLayerByAttribute_management('lyr', selection_type, where_clause)

    ##print 'Finished Select_Object()\n'
    return 'lyr'


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

    # Print the fields (only really needed during testing)
    ##fields = arcpy.ListFields('target_obj')
    ##print '  Fields in joined layer:'
    ##for field in fields:
    ##    print '    ' + field.name

    print '    Finished Join_2_Objects_By_Attr()\n'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Get_Count_Selected(lyr):
    """
    PARAMETERS:
      lyr (lyr): The layer that should have a selection on it that we want to test.

    RETURNS:
      count_selected (int): The number of selected records in the lyr

    FUNCTION:
      To get the count of the number of selected records in the lyr.
    """

    print '\n    Starting Get_Count()...'

    # See if there are any selected records
    desc = arcpy.Describe(lyr)

    if desc.fidSet: # True if there are selected records
        result = arcpy.GetCount_management(lyr)
        count_selected = int(result.getOutput(0))

    # If there weren't any selected records
    else:
        count_selected = 0

    print '      Count of Selected: {}'.format(str(count_selected))

    print '    Finished Get_Count()\n'

    return count_selected


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
