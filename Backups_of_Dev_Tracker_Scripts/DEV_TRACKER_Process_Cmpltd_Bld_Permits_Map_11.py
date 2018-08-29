#-------------------------------------------------------------------------------

# Purpose:
"""
POINTS/UNIT_COUNT Data Processing

To create a point feature class from a CSV when you want a count of points
based on a supplied quantity field

The CSV needs to have an X and Y
column, and should have an APN field (to help find the X and Y coordinates if
there is no X or Y data.

The output should be points with a quantity field named [UNIT_COUNT]
"""
# Author:      mgrue
#
# Created:     22/05/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, os, datetime, shutil, ConfigParser, time, sys

arcpy.env.overwriteOutput = True

def main():

    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Cmpltd_Bld_Permits_Map_11'


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
    name_of_csv       = 'Existing Dwelling Units (2011 General Plan Forward) (Map 3 & Map 11).csv'
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


    # Set Field names from the CSV
    apn_fld       = 'PARCEL_NBR'
    x_fld         = 'LONGITUDE'
    y_fld         = 'LATITUDE'
    record_id_fld = 'RECORD_ID'
    du_fld        = 'HOUSING_UNITS'


    # Misc variables
    success = True
    data_pass_QAQC_tests = True


    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Calling Functions

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
        print '*** ERROR with Creating FGDBs() ***'
        print str(e)


    #-------------------------------------------------------------------
    #                   Import CSV into FGDB Table
    #-------------------------------------------------------------------

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
        print '*** ERROR with Import CSV into FGDB Table() ***'
        print str(e)


    #-------------------------------------------------------------------
    #                   Find and Fix Invalid XYs
    #-------------------------------------------------------------------

    try:
        Find_And_Fix_Invalid_XYs(csv_table, wkg_fgdb, PARCEL_HISTORICAL, PARCELS_ALL, apn_fld, x_fld, y_fld)

    except Exception as e:
        success = False
        print '*** ERROR with Find_And_Fix_Invalid_XYs() ***'
        print str(e)


    #-------------------------------------------------------------------
    #                Perform QA/QC Imported Table
    #-------------------------------------------------------------------

    try:
        data_pass_QAQC_tests = QA_QC(csv_table, record_id_fld, apn_fld, x_fld, y_fld)

    except Exception as e:
        success = False
        print '*** ERROR with QA_QC() ***'
        print str(e)


    #-------------------------------------------------------------------
    #                     Create the Points
    #-------------------------------------------------------------------

    try:
        out_name   = '{}_Pts_READY2BIN'.format(shorthand_name)
        points_fc  = '{}\{}'.format(wkg_fgdb, out_name)

        # Create points
        success = Create_Points_From_XY_Table(csv_table, points_fc, x_fld, y_fld)

    except Exception as e:
        success = False
        print '*** ERROR with Create_Points_From_XY_Table() ***'
        print str(e)


    #------------------------------------------------------------------
    #    Change field names so the Bin_Processed_Data.py script will work
    #------------------------------------------------------------------
    # This is because the binning script will expect for the Dwelling Unit
    # Field to be named [UNIT_COUNT]
    try:
        old_name = du_fld
        new_name = 'UNIT_COUNT'
        print '\nChanging Field:\n  "{}"\nTo:\n  "{}"\nIn FC:\n  {}'.format(old_name, new_name, points_fc)  # For testing purposes
        arcpy.AlterField_management(points_fc, old_name, new_name)

    except Exception as e:
        success = False
        print '*** ERROR with Changing Field Names ***'
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
    print 'Data Passes QA/QC tests = {}'.format(data_pass_QAQC_tests)
    print 'Success = {}'.format(success)
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
#                             FUNCTION: Find_And_Fix_Invalid_XYs()
def Find_And_Fix_Invalid_XYs(csv_table, wkg_fgdb, PARCEL_HISTORICAL, PARCELS_ALL, apn_fld, x_fld, y_fld):
    """
      csv_table (str): Full path to the table with the XY fields to be validated
        and populated if invalid.
      wkg_fgdb (str): Full path to the working FGDB.
      PARCEL_HISTORICAL (str): Full path to the PARCEL_HISTORICAL FC in SDE.
      PARCELS_ALL (str): Full path to the PARCELS_ALL FC (This may be a subset
        of the SDE FC in order to increase performance).
      apn_fld (str): Name of the field with the APN values.  This field
        MUST BE A STRING FIELD. If this field has dashes "-", it is OK because
        this function will strip them out so that they can be joined
        to the PARCEL_HISTORICAL, and PARCELS_ALL Feature Classes.
      x_fld (str): Name of the field with the X values.
      y_fld (str): Name of the field with the Y values.


    """
    print '\n------------------------------------------------------------------'
    print 'Starting Find_And_Fix_Invalid_XYs()'


    # Format the APN field to remove the dashes
    expression = '!{}!.replace("-","")'.format(apn_fld)
    print '\n  Removing dashes in the field "{}" to equal: {}\n'.format(apn_fld, expression)
    arcpy.CalculateField_management(csv_table, apn_fld, expression, 'PYTHON_9.3')


    # Get list of any parcels that do not have a valid XY in the Imported Table
    # The where clause finds any wildly incorrect XY rows or <NULL> rows
    fields = [apn_fld]
    where_clause = """
    "{1}" < 32 OR
    "{1}" > 34 OR
    "{0}" < -118 OR
    "{0}" > -116 OR
    "{1}" IS NULL OR
    "{0}" IS NULL
    """.format(x_fld, y_fld)
    apns_w_invalid_xy = []
    print '  Getting list of APNs with invalid XYs:'
    with arcpy.da.SearchCursor(csv_table, fields, where_clause) as cursor:
        for row in cursor:
            apn = row[0]
            ##print '    {}'.format(apn)  # For testing
            apns_w_invalid_xy.append(apn)

    #---------------------------------------------------------------------------
    #            Find if there were APNs with invalid XYs
    #                   and save them to disk if so
    if len(apns_w_invalid_xy) == 0:
        print '    OK! There were 0 APNs with invalid XYs.'

    else:
        print '    Info. There were "{}" APNs with invalid XYs.  Finding XY data now.'.format(len(apns_w_invalid_xy))

        # Create a FC with NAD 1983 spatial reference to hold the parcels w/ invalid XYs
        out_name = 'Missing_XY_Info'
        spatial_reference = arcpy.SpatialReference(4269)  # 4269 is the WKID of "NAD 1983"
        missing_xy_fc = os.path.join(wkg_fgdb, out_name)
        print '\n  Creating Feature class to hold parcels w/invalid XY data at:\n    {}'.format(missing_xy_fc)
        arcpy.CreateFeatureclass_management(wkg_fgdb, out_name, 'POLYGON', PARCELS_ALL, '', '', spatial_reference)

        #-----------------------------------------------------------------------
        #         First try to find the missing XYs in PARCEL_HISTORICAL
        print '\n  ------------------------------------------------------------'
        print '  Finding any APNs with invalid XY in PARCEL_HISTORICAL:'

        # Make layer to make selections
        arcpy.MakeFeatureLayer_management(PARCEL_HISTORICAL, 'par_hist_lyr')

        # Loop through all APNs with invalid XYs, select them in PARCEL_HISTORICAL and append to missing_xy_fc
        for apn in apns_w_invalid_xy:
            where_clause = "APN = '{}'".format(apn)
            arcpy.SelectLayerByAttribute_management('par_hist_lyr', 'ADD_TO_SELECTION', where_clause)

        count = Get_Count_Selected('par_hist_lyr')

        if count == 0:
            print '    There were 0 APNs found in PARCEL_HISTORICAL, nothing to append'
        else:
            print '    Appending "{}" records from PARCEL_HISTORICAL to:\n      {}'.format(count, missing_xy_fc)
            arcpy.Append_management('par_hist_lyr', missing_xy_fc, 'NO_TEST')


        #-----------------------------------------------------------------------
        #          Next try to find the missing XYs in PARCELS_ALL
        print '\n  ------------------------------------------------------------'
        print '  Finding any APNs with invalid XY in PARCELS_ALL:'

        # Make layer to make selections on
        arcpy.MakeFeatureLayer_management(PARCELS_ALL, 'par_all_lyr')

        # Loop through all APNs with invalid XYs, select them in PARCELS_ALL and append to missing_xy_fc
        for apn in apns_w_invalid_xy:
            where_clause = "APN = '{}'".format(apn)
            arcpy.SelectLayerByAttribute_management('par_all_lyr', 'ADD_TO_SELECTION', where_clause)

        count = Get_Count_Selected('par_all_lyr')

        if count == 0:
            print '    There were 0 APNs found in PARCELS_ALL, nothing to append'
        else:
            print '    Appending "{}" records from PARCELS_ALL to:\n      {}'.format(count, missing_xy_fc)
            arcpy.Append_management('par_all_lyr', missing_xy_fc, 'NO_TEST')


    #---------------------------------------------------------------------------
    #                 Get XY centroid info from 'missing_xy_fc'
    #                  and update 'csv_table' with XY info
    print '\n  ------------------------------------------------------------'
    print '  Getting XY Centroid info from:\n    {}\n  And updating info in:\n    {}\n'.format(missing_xy_fc, csv_table)
    for apn in apns_w_invalid_xy:

        # Get the XY info from missing_xy_fc
        fields = ['APN', 'Shape@XY']
        where_clause = "APN = '{}'".format(apn)
        with arcpy.da.SearchCursor(missing_xy_fc, fields, where_clause) as cursor:
            for row in cursor:
                apn = row[0]
                x_value, y_value = row[1]

                ##print '  APN: {}\n    X = {}\n    Y = {}'.format(apn, x_value, y_value)  # For testing

                # Calculate the XY values into the Import Table
                tbl_fields = [apn_fld, x_fld, y_fld]
                tbl_where_clause = "{} = '{}'".format(apn_fld, apn)
                with arcpy.da.UpdateCursor(csv_table, tbl_fields, tbl_where_clause) as updt_cursor:
                    for updt_row in updt_cursor:
                        print '  APN: {}  |  X = {}  |  Y = {}'.format(apn, x_value, y_value)
                        updt_row[1] = x_value
                        updt_row[2] = y_value
                        updt_cursor.updateRow(updt_row)

    print '\nFinished Find_And_Fix_Invalid_XYs()'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                             FUNCTION: QA_QC()
def QA_QC(csv_table, record_id_fld, apn_fld, x_fld, y_fld):
    """
    """
    print '\n--------------------------------------------------------------------'
    print 'Start QA_QC()'

    data_pass_QAQC_tests = True

    #---------------------------------------------------------------------------
    # 1)  Which APNs from the CSV were not found in PARCELS_ALL or PARCEL_HISTORICAL?
    print '\n  1) Finding which APNs still have invalid XYs:\n'

    # Get list of any parcels that do not have a valid XY in the Imported Table
    fields = [apn_fld]

    where_clause = """
    "{1}" < 32 OR
    "{1}" > 34 OR
    "{0}" < -118 OR
    "{0}" > -116 OR
    "{1}" IS NULL OR
    "{0}" IS NULL
    """.format(x_fld, y_fld)

    apns_w_invalid_xy = []
    with arcpy.da.SearchCursor(csv_table, fields, where_clause) as cursor:
        for row in cursor:
            apn = row[0]
            ##print apn  # For testing
            apns_w_invalid_xy.append(apn)
    del cursor

    # Get a sorted list of only unique values
    apns_w_invalid_xy = sorted(set(apns_w_invalid_xy))

    #---------------------------------------------------------------------------
    #            Find if there were APNs with invalid XYs
    #                   and report them if so
    if len(apns_w_invalid_xy) == 0:
        print '    OK! There were 0 APNs with invalid XYs.'

    else:
        data_pass_QAQC_tests = False
        print '    WARNING! There were still "{}" APNs with invalid XYs'.format(len(apns_w_invalid_xy))
        print '    These APNs do not have XY information, and are not found in PARCELS_ALL or PARCEL_HISTORICAL'
        print '    These APNs cannot-therefore-be mapped and will not appear in the point Feature Class'
        print '    See below for list of records with invalid XYs:'

        for apn in apns_w_invalid_xy:
            print '      APN:  {}'.format(apn)

            # Get the Record ID(s) associated with that APN
            fields = [apn_fld, record_id_fld]
            where_clause = "{} = '{}'".format(apn_fld, apn)
            with arcpy.da.SearchCursor(csv_table, fields, where_clause) as cursor:
                for row in cursor:
                    print '        With Record ID: {}'.format(row[1])

            del cursor

    #---------------------------------------------------------------------------
    # 2)  Check any critical fields (besides the XY fields)
    #     to ensure there are no blank values

    print '\n  2) Finding any critical fields that are blank in imported CSV table:\n'
    critical_fields = [record_id_fld, apn_fld]
    for f in critical_fields:

        # Set a where clause for a string field
        where_clause = "{0} IS NULL or {0} = ''".format(f)

        # Get list of ids
        print '    Checking where: "{}":'.format(where_clause)
        ids_w_nulls = []  # List to hold the ID of reports with null values
        with arcpy.da.SearchCursor(csv_table, critical_fields, where_clause) as cursor:
            for row in cursor:
                record_id = row[0]
                ids_w_nulls.append(record_id)
        del cursor

        # Get a sorted list of only unique values
        ids_w_nulls = sorted(set(ids_w_nulls))

        # Report on the sorted list
        if len(ids_w_nulls) == 0:
            print '      OK! No blank values in {}'.format(f)

        else:
            data_pass_QAQC_tests = False
            print '      WARNING! There are records in the CSV extract that have a blank value in column: "{}":'.format(f)
            for id_num in ids_w_nulls:
                if (id_num == None) or (id_num == ''):
                    print '        No Record ID available to report'
                else:
                    print '        {}'.format(id_num)


        print ''

    print '  Data Pass QA/QC tests = {}'.format(data_pass_QAQC_tests)
    print 'Finished QA_QC()'
    return data_pass_QAQC_tests


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                    FUNCTION: Create_Points_From_XY_Table
def Create_Points_From_XY_Table(xy_table, points_fc, x_field, y_field):
    """
    PARAMETERS:

    RETURNS:

    FUNCTION:
    """
    print '\n----------------------------------------------------------------'
    print 'Starting Create_Points_From_XY_Table()\n'

    # Misc Variables
    success = True
    WKID = 4269  # 4269 is the WKID of "NAD 1983"

    # Set the WKID into a Spatial Reference
    spatial_reference = arcpy.SpatialReference(WKID)

    # Make an XY Event Layer
    print '  Making XY Event Layer from:\n    {}\n'.format(xy_table)
    XY_Event_lyr = 'XY_Event_lyr'
    arcpy.MakeXYEventLayer_management(xy_table, x_field, y_field, XY_Event_lyr, spatial_reference)

    # Save the Event Layer
    print '  Saving the Event Layer to:\n    {}\n'.format(points_fc)
    arcpy.CopyFeatures_management(XY_Event_lyr, points_fc)

    # Repair Geometry to remove any features w/o geometry
    print '  Repairing geometry to remove any NULL Geometry'
    arcpy.RepairGeometry_management(points_fc)

    print '\nFinished Create_Points_From_XY_Table()'

    return success


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
