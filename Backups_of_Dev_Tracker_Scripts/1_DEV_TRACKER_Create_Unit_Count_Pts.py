#-------------------------------------------------------------------------------
# Name:        DEV_TRACKER_Create_Unit_Count_Pts.py
# Purpose:
"""
To create a point feature class from a CSV when you want a count of points
based on a supplied quantity field (if there is no quantity field and there
should be 1 for each record, this script will add a quantity field and calc it
to equal 1) then proceed with the tallying of quantity into a CPASG table
and a HEXBIN FC.

The CSV needs to have an X and Y
column, and should have an APN field (to help find the X and Y coordinates if
there is no X or Y data.

"""
# Author:      mgrue
#
# Created:     22/05/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, os, datetime, shutil

arcpy.env.overwriteOutput = True

def main():

    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Name of this script
    name_of_script = 'DEV_TRACKER_Create_Unit_Count_Pts.py'


    # Field names in the CSV's (should be consistent for every csv from PDS)
    apn_field_name_in_csv = 'PARCEL_NBR'
    x_field_csv           = 'LONGITUDE'
    y_field_csv           = 'LATITUDE'


    # Paths to folders and local FGDBs
    folder_with_csvs  = r"P:\20180510_development_tracker\tables\CSV_Extract_20180713"

    root_folder       = r'P:\20180510_development_tracker\DEV'

    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder       = '{}\{}'.format(root_folder, 'Data')

    imported_csv_fgdb = '{}\{}'.format(data_folder, '1_Imported_CSVs.gdb')

    invalid_xy_fgdb   = '{}\{}'.format(data_folder, '2_Invalid_XY.gdb')

    points_fgdb       = '{}\{}'.format(data_folder, '3_Points.gdb')

    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)

    # Paths to SDE Feature Classes
    PARCELS_HISTORICAL = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCEL_HISTORICAL'

    PARCELS_ALL        = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCELS_ALL'


    # Control_table variables (Used to pass variables to script.  i.e. The CSV names)
    control_table = r'Database Connections\AD@ATLANTIC@SDW.sde\SDW.PDS.PDS_DEV_TRACKER_CONTROL_TABLE'
    control_table_where_clause = "PROCESS_UNIT_COUNT = 'Yes'"  # Controls which CSVs to process with this script

    # Misc variables
    success = True

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
    #                      Create FGDBs if needed
    #---------------------------------------------------------------------------
    # Create working CSV FGDB if it does not exist
    if not arcpy.Exists(imported_csv_fgdb):
        out_folder_path, out_name = os.path.split(imported_csv_fgdb)
        print 'Creating FGDB: "{}" at:\n  {}\n'.format(out_name, out_folder_path)
        arcpy.CreateFileGDB_management(out_folder_path, out_name)

    # Create invalid XY FGDB if it does not exist
    if not arcpy.Exists(invalid_xy_fgdb):
        out_folder_path, out_name = os.path.split(invalid_xy_fgdb)
        print 'Creating FGDB: "{}" at:\n  {}\n'.format(out_name, out_folder_path)
        arcpy.CreateFileGDB_management(out_folder_path, out_name)

    # Create working Points FGDB if it does not exist
    if not arcpy.Exists(points_fgdb):
        out_folder_path, out_name = os.path.split(points_fgdb)
        print 'Creating FGDB: "{}" at:\n  {}\n'.format(out_name, out_folder_path)
        arcpy.CreateFileGDB_management(out_folder_path, out_name)


    #---------------------------------------------------------------------------
    #                  Get subset of PARCELS_ALL FC from SDE
    #---------------------------------------------------------------------------
    # To increase performance, save a subset of the PARCELS_ALL FC,
    #   Save where SITUS_JURIS = 'CN' to a local FGDB
    in_features  = PARCELS_ALL
    out_path     = invalid_xy_fgdb
    out_name     = 'PARCELS_ALL_CN_JURIS'
    where_clause = "SITUS_JURIS = 'CN'"
    print 'To increase performance, save a subset of the PARCELS_ALL FC to a local FGDB:'
    print '  Saving:\n    {}\n  To:\n    {}\{}\n  Where:\n    {}\n'.format(in_features, out_path, out_name, where_clause)
    arcpy.FeatureClassToFeatureClass_conversion(in_features, out_path, out_name, where_clause)


    # Add an index to the APN field in PARCELS_ALL_CN_JURIS
    PARCELS_ALL_CN_JURIS = '{}\{}'.format(out_path, out_name)
    print '  Adding index to:\n    {}\n'.format(PARCELS_ALL_CN_JURIS)
    arcpy.AddIndex_management(PARCELS_ALL_CN_JURIS, ['APN'], 'apn_index')

    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # Loop through each CSV in the control_table (where PROCESS = True) and:
    #   Import it,
    #   Find and Fix invalid XYs,
    #   Create the Points
    fields = ['NAME_OF_CSV', 'SHORTHAND_NAME', 'PROCESS_UNIT_COUNT']
    with arcpy.da.SearchCursor(control_table, fields, control_table_where_clause) as cursor:
        for row in cursor:

            # Get variables from control_table
            path_to_csv = os.path.join(folder_with_csvs, row[0])
            shorthand_name = row[1]

            try:
                print '\n--------------------------------------------------------'
                print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
                print '--------------------------------------------------------'
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print 'Processing: "{}"'.format(shorthand_name)
                print '  CSV is at:\n    {}\n'.format(path_to_csv)

                # Set paths to Feature Classes / Tables
                name_of_csv_table = '{}_Tbl'.format(shorthand_name)
                csv_table = '{}\{}'.format(imported_csv_fgdb, name_of_csv_table)

                name_of_hist_par_fc = '{}_PARCELS_HISTORICAL'.format(shorthand_name)
                invalid_xy_hist_par_fc = '{}\{}'.format(invalid_xy_fgdb, name_of_hist_par_fc)

                name_of_par_fc = '{}_PARCELS_ALL'.format(shorthand_name)
                invalid_xy_par_fc = '{}\{}'.format(invalid_xy_fgdb, name_of_par_fc)

                name_of_points_fc = '{}_Pts'.format(shorthand_name)
                points_fc = '{}\{}'.format(points_fgdb, name_of_points_fc)


                #-------------------------------------------------------------------
                #                   Import CSV into FGDB Table
                #-------------------------------------------------------------------
                print '  ------------------------------------------------------------------'
                print '  Importing CSV to FGDB Table:\n    From:\n      {}'.format(path_to_csv)
                print '    To:\n      {}'.format(imported_csv_fgdb)
                print '    As:\n      {}\n'.format(os.path.basename(csv_table))

                # Import CSV to FGDB Table
                arcpy.TableToTable_conversion(path_to_csv, imported_csv_fgdb, os.path.basename(csv_table))


                #-------------------------------------------------------------------
                #                    Find Invalid  X's & Y's
                #-------------------------------------------------------------------

                # Find and Fix Invalid XYs
                success = Find_And_Fix_Invalid_XYs(csv_table, x_field_csv, y_field_csv,
                                                   apn_field_name_in_csv, PARCELS_HISTORICAL,
                                                   PARCELS_ALL_CN_JURIS, invalid_xy_hist_par_fc,
                                                   invalid_xy_par_fc)


                #-------------------------------------------------------------------
                #                     Create the Points
                #-------------------------------------------------------------------

                # Create points
                success = Create_Points_From_XY_Table(csv_table, points_fc, x_field_csv, y_field_csv)

            except Exception as e:
                success = False
                print '*** ERROR! Unable to process: {} ***'.format(row[0])
                print str(e)


    #---------------------------------------------------------------------------
    # Write a file to disk to let other scripts know if this script ran
    # successfully or not
    print '--------------------------------------------------------------------'
    try:
        # Delete the success_error_folder to remove any previously written files
        if os.path.exists(success_error_folder):
            print '\nDeleting the folder at:\n  {}'.format(success_error_folder)
            shutil.rmtree(success_error_folder)
            time.sleep(3)

        # Create the empty success_error_folder
        print '\nMaking a folder at:\n  {}'.format(success_error_folder)
        os.mkdir(success_error_folder)

        # Set a file_name depending on the 'success' variable.
        if success == True:
            file_name = 'SUCCESS_running_{}.txt'.format(name_of_script.split('.')[0])

        else:
            file_name = 'ERROR_running_{}.txt'.format(name_of_script.split('.')[0])

        # Write the file
        file_path = '{}\{}'.format(success_error_folder, file_name)
        print '\nCreating file:\n  {}\n'.format(file_path)
        open(file_path, 'w')

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
    print 'Success = {}'.format(success)
    time.sleep(3)
    sys.stdout = orig_stdout
    sys.stdout.flush()

    if success == True:
        print '\nSUCCESSFULLY ran {}'.format(name_of_script)
        print 'Please find log file at:\n  {}\n'.format(log_file_date)
    else:
        print '\n*** ERROR with {} ***'.format(name_of_script)
        print 'Please find log file at:\n  {}\n'.format(log_file_date)


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
def Find_And_Fix_Invalid_XYs(xy_table, x_field, y_field, apn_field_name, PARCELS_HISTORICAL, PARCELS_ALL, invalid_xy_hist_par_fc, invalid_xy_par_fc):
    """
    PARAMETERS:
      xy_table (str): Full path to the table with the XY fields to be validated
        and populated if invalid.
      x_field (str): Name of the field with the X values.
      y_field (str): Name of the field with the Y values.
      apn_field_name (str): Name of the field with the APN values.  This field
        MUST BE A STRING FIELD. If this field has dashes "-", it is OK because
        this function will strip them out so that they can be joined
        to the PARCELS_HISTORICAL, and PARCELS_ALL Feature Classes.
      PARCELS_HISTORICAL (str): Full path to the PARCELS_HISTORICAL FC in SDE.
      PARCELS_ALL (str): Full path to the PARCELS_ALL FC (This may be a subset
        of the SDE FC in order to increase performance).
      invalid_xy_hist_par_fc (str): Full path to the FC to be created to hold the
        APNs that were found in the PARCELS_HISTORICAL FC.  These are the APNs
        that will have their centroid calculated in Decimal Degrees.  Those XY
        values will then be used to update the corresponding record in the
        xy_table.
      invalid_xy_par_fc (str): Full path to the FC to be created to hold the
        APNs that were found in the PARCELS_ALL FC.  These are the APNs
        that will have their centroid calculated in Decimal Degrees.  Those XY
        values will then be used to update the corresponding record in the
        xy_table.

    RETURNS:
      success (bool): True is no errors, False if errors

    FUNCTION:
      SHORT VERSION:
        To Find valid values for invalid (or NULL) X and Y coordinates in a FGDB
        Table by searching for matching APN's in SDE both the PARCELS_HISTORICAL
        Feature Class, and then PARCELS_ALL Feature Class.
        If any matches are found (first in PARCELS_HISTORICAL and then in
        PARCELS_ALL), the XY values are calculated in the temporary
        'invalid_xy_hist_par_fc' and 'invalid_xy_par_fc', then written directly
        to the xy_table.

      LONG VERSION:
        TODO: Write up a detailed version

    """
    print '\n  --------------------------------------------------------------------'
    print '  Starting Find_And_Fix_Invalid_XYs()\n'
    print '    ------------------------------------------------------------------'
    print '    Finding records with invalid XYs:'

    # Misc Variables
    success = True
    WKID = 4269  # 4269 is the WKID of "NAD 1983"

    # Set the counts
    count_invalid_xy        = 0
    count_xy_found_historic = 0
    count_xy_found_par      = 0

    # Set the spatial reference for calculating the CENTROIDS
    #   We want the spatial reference to be in a coordinate system that uses
    #   Decimal Degrees
    spatial_reference = arcpy.SpatialReference(WKID)

    # Make a Cursor of any rows that do not have a valid X and Y (using a where_clause)
    # And remove the dashes "-" from the existing APN field
    where_clause = """
    "LATITUDE" < 32 OR
    "LATITUDE" > 34 OR
    "LONGITUDE" < -118 OR
    "LONGITUDE" > -116 OR
    "LATITUDE" IS NULL OR
    "LONGITUDE" IS NULL
    """
    fields = [apn_field_name]

    with arcpy.da.UpdateCursor(xy_table, fields, where_clause) as cursor:
        for row in cursor:
            if row[0] != None:  # If there is no APN, don't format, but count as invalid XY
                row[0] = row[0].replace('-', '')  # Remove the dashes
                cursor.updateRow(row)
                ##print '    New APN: "{}"'.format(row[0])  # For testing
            count_invalid_xy += 1
    del cursor
    print '      There are "{}" records that have invalid XY\'s\n'.format(count_invalid_xy)  # For testing


    #---------------------------------------------------------------------------
    #                            PARCELS_HISTORIC
    #---------------------------------------------------------------------------
    if count_invalid_xy == 0:
        print '    There are no invalid XYs to find.  No need to search PARCELS_HISTORIC'

    else:  # Then try to find the XYs from PARCELS_HISTORIC
        print '    --------------------------------------------------------------'
        print '    Trying to find XYs from the PARCELS_HISTORICAL FC'
        # Join the CSV table to the PARCELS_HISTORICAL FC
        # This join will only include records from the csv table that didn't have a valid X or Y (because of the formatting above)
        hist_parcels_lyr = Join_2_Objects_By_Attr(PARCELS_HISTORICAL, 'APN', xy_table, apn_field_name, 'KEEP_COMMON')

        # Save the layer
        print '      Saving joined layer to:\n        {}\n'.format(invalid_xy_hist_par_fc)
        arcpy.CopyFeatures_management(hist_parcels_lyr, invalid_xy_hist_par_fc)

        # Add CENTROID_X and CENTROID_Y fields and calculate
        print '      Adding Geometry Attributes (XY Centroid of parcels) to:\n        {}\n'.format(invalid_xy_hist_par_fc)
        spatial_reference = arcpy.SpatialReference(4269)  # 4269 is the WKID of "NAD 1983"
        arcpy.AddGeometryAttributes_management(invalid_xy_hist_par_fc, "CENTROID", '', '', spatial_reference)

        # Update the CSV table with the XY values
        # Loop through each item in the features found in the PARCELS_HISTORICAL FC
        print '      Updating the XY\'s in the Table at:\n        {}\n'.format(xy_table)
        apn_field_name_in_joined_tbl = os.path.basename(xy_table) + '_' + apn_field_name
        fields = [apn_field_name_in_joined_tbl, 'CENTROID_X', 'CENTROID_Y']

        with arcpy.da.SearchCursor(invalid_xy_hist_par_fc, fields) as cursor:
            for row in cursor:
                apn = row[0]
                x_value = row[1]
                y_value = row[2]

                with arcpy.da.UpdateCursor(xy_table, [apn_field_name, x_field, y_field]) as updt_cursor:
                    for updt_row in updt_cursor:
                        if updt_row[0] == apn:  # If the APN in the CSV Table equals the APN in the PARCELS_HISTORICAL FC, get the new XY
                            updt_row[1] = x_value
                            updt_row[2] = y_value
                            updt_cursor.updateRow(updt_row)
                            count_xy_found_historic += 1
                del updt_cursor
        del cursor
        print '      "{}" records in the csv table just received XYs due to PARCELS_HISTORICAL FC\n'.format(count_xy_found_historic)

    count_remaining_invalid_xy = count_invalid_xy - count_xy_found_historic


    #---------------------------------------------------------------------------
    #                            PARCELS_ALL
    #---------------------------------------------------------------------------
    if count_remaining_invalid_xy == 0:
        print '    There are no more invalid XYs to find.  No need to search PARCELS_ALL\n'

    else:  # Then try to find remaining XYs from PARCELS_ALL
        print '    --------------------------------------------------------------'
        print '    There are "{}" remaining records with invalid XYs\n'.format(count_remaining_invalid_xy)
        print '    Trying to find XYs from the PARCELS_ALL FC:'

        # Join the CSV table to the PARCELS_ALL FC
        # This join will only include records from the csv table that didn't have a valid X or Y (because of the formatting above)
        parcels_lyr = Join_2_Objects_By_Attr(PARCELS_ALL, 'APN', xy_table, apn_field_name, 'KEEP_COMMON')

        # Save the layer
        print '      Saving joined layer to:\n        {}\n'.format(invalid_xy_par_fc)
        arcpy.CopyFeatures_management(parcels_lyr, invalid_xy_par_fc)

        # Add CENTROID_X and CENTROID_Y fields and calculate
        print '      Adding Geometry Attributes (XY Centroid of parcels) to:\n        {}\n'.format(invalid_xy_par_fc)
        arcpy.AddGeometryAttributes_management(invalid_xy_par_fc, "CENTROID", '', '', spatial_reference)

        # Update the CSV table with the XY values
        # Loop through each item in the features found in the PARCELS_ALL FC
        print '      Updating the XY\'s in the Table at:\n        {}\n'.format(xy_table)
        apn_field_name_in_joined_tbl = os.path.basename(xy_table) + '_' + apn_field_name
        fields = [apn_field_name_in_joined_tbl, 'CENTROID_X', 'CENTROID_Y']

        with arcpy.da.SearchCursor(invalid_xy_par_fc, fields) as cursor:
            for row in cursor:
                apn = row[0]
                x_value = row[1]
                y_value = row[2]

                with arcpy.da.UpdateCursor(xy_table, [apn_field_name, x_field, y_field]) as updt_cursor:
                    for updt_row in updt_cursor:
                        if updt_row[0] == apn:  # If the APN in the CSV Table equals the APN in the PARCELS_ALL FC, get the new XY
                            updt_row[1] = x_value
                            updt_row[2] = y_value
                            updt_cursor.updateRow(updt_row)
                            count_xy_found_par += 1
                del updt_cursor
        del cursor
        print '      "{}" records in the csv table now have an XY due to PARCELS_ALL FC\n'.format(count_xy_found_par)

    #---------------------------------------------------------------------------
    # Find out how many invalid XYs still exist (if any) and report
    count_remaining_invalid_xy = count_invalid_xy - (count_xy_found_historic + count_xy_found_par)

    if count_remaining_invalid_xy != 0:
        print 'WARNING! There are "{}" Records in the csv table that still do not have valid XY information'.format(count_remaining_invalid_xy)
        print '  The APNs with invalid XY info are:'

        # Get list of the APN for all records that still have invalid XY
        fields = [apn_field_name]
        apns_w_invalid_XY = []
        with arcpy.da.UpdateCursor(xy_table, fields, where_clause) as cursor:
            for row in cursor:
                apns_w_invalid_XY.append(row[0])

        # Print out the list of APNs
        apns_w_invalid_XY.sort()
        for apn in apns_w_invalid_XY:
            print '    {}'.format(apn)

    else:
        print '    INFO! All XYs are now valid'

    print '\n  Finished Find_And_Fix_Invalid_XYs()'

    return success

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                    FUNCTION: Create_Points_From_XY_Table
def Create_Points_From_XY_Table(xy_table, points_fc, x_field, y_field):
    """
    PARAMETERS:

    RETURNS:

    FUNCTION:
    """
    print '\n  ----------------------------------------------------------------'
    print '  Starting Create_Points_From_XY_Table()\n'

    # Misc Variables
    success = True
    WKID = 4269  # 4269 is the WKID of "NAD 1983"

    # Set the WKID into a Spatial Reference
    spatial_reference = arcpy.SpatialReference(WKID)

    # Make an XY Event Layer
    print '    Making XY Event Layer from:\n      {}\n'.format(xy_table)
    XY_Event_lyr = 'XY_Event_lyr'
    arcpy.MakeXYEventLayer_management(xy_table, x_field, y_field, XY_Event_lyr, spatial_reference)

    # Save the Event Layer
    print '    Saving the Event Layer to:\n      {}\n'.format(points_fc)
    arcpy.CopyFeatures_management(XY_Event_lyr, points_fc)

    # Repair Geometry to remove any features w/o geometry
    print '    Repairing geometry to remove any NULL Geometry'
    arcpy.RepairGeometry_management(points_fc)

    print '\n  Finished Create_Points_From_XY_Table()'

    return success

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

    print '\n      Starting Join_2_Objects_By_Attr()...'

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
    print '        Joining: "{}"\n           With: "{}"\n             On: "{}"\n            And: "{}"\n           Type: "{}"'.format(target_obj, to_join_obj, target_join_field, to_join_field, join_type)
    arcpy.AddJoin_management('target_obj', target_join_field, 'to_join_obj', to_join_field, join_type)

    # Print the fields (only really needed during testing)
    ##fields = arcpy.ListFields('target_obj')
    ##print '  Fields in joined layer:'
    ##for field in fields:
    ##    print '    ' + field.name

    print '      Finished Join_2_Objects_By_Attr()\n'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
