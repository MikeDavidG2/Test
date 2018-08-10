#-------------------------------------------------------------------------------

# Purpose:
"""
POLYGONS/DENSITY Data Processing

To merge the data from the following scripts:
  ...Map_08_A.py (Applicant Initiated, In Process GPAs)
and
  ...Map_08_B.py (County Initiated, In Process GPAs)

then find the delta between:
  The merged data
with
  The original housing model (From Map 01)


The output should be polygons with a density field named [DENSITY]
"""
#
# Author:      mgrue
#
# Created:     24/07/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, os, math, datetime

arcpy.env.overwriteOutput = True

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'In_Process_GPA_Map_08_C'


    # Name of this script
    name_of_script = 'DEV_TRACKER_Process_{}.py'.format(shorthand_name)


    # Paths to folders and local FGDBs
##    folder_with_csvs  = r"P:\20180510_development_tracker\tables\CSV_Extract_20180726"
##    name_of_csv       = 'In-Process County General Plan Amendments (Map 8).csv'
##    path_to_csv       = os.path.join(folder_with_csvs, name_of_csv)


    root_folder       = r'P:\20180510_development_tracker\DEV'

    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder       = '{}\{}'.format(root_folder, 'Data')

##    imported_csv_fgdb = '{}\{}'.format(data_folder, '1_Imported_CSVs.gdb')

    wkg_fgdb          = '{}\{}'.format(data_folder, '{}.gdb'.format(shorthand_name))

    applicant_GPAs_fc = '{}\{}\{}'.format(data_folder, 'In_Process_GPA_Map_08_A.gdb', 'Parcels_Applicant_joined_diss_READY2MERGE')

    county_GPAs_fc    = '{}\{}\{}'.format(data_folder, 'In_Process_GPA_Map_08_B.gdb', 'Parcels_County_joined_diss_HOUSING_int_diss_READY2MERGE')


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Paths to SDE Feature Classes
    sde_connection_file = r'P:\20180510_development_tracker\DEV\Scripts\Connection_Files\AD@ATLANTIC@SDE.sde'
##    PARCELS_HISTORICAL = r'P:\20180510_development_tracker\DEV\Scripts\Connection_Files\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCEL_HISTORICAL'
##    PARCELS_ALL        = r'P:\20180510_development_tracker\DEV\Scripts\Connection_Files\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCELS_ALL'
    PDS_HOUSING_MODEL_OUTPUT_2011 = r'{}\{}'.format(sde_connection_file, 'SDE.SANGIS.PDS_HOUSING_MODEL_OUTPUT_2011')

    # Set field names
##    apn_fld       = 'APNS'
    record_id_fld = 'RECORD_ID'
    gp_code_fld   = 'GPCODE95'
    density_fld   = 'DENSITY'
    housing_model_density_fld = 'EFFECTIVE_DENSITY'
##    unconstrained_density_fld = 'Unconstrained_DENSITY'

    # Misc variables
    success = True
    data_pass_QAQC_tests = True


    # This is the acreage that an overlap
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

##    # Turn all 'print' statements into a log-writing object
##    try:
##        log_file = r'{}\{}'.format(log_file_folder, name_of_script.split('.')[0])
##        orig_stdout, log_file_date, dt_to_append = Write_Print_To_Log(log_file, name_of_script)
##    except Exception as e:
##        success = False
##        print '\n*** ERROR with Write_Print_To_Log() ***'
##        print str(e)


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
    #       Find any Overlaps between the Applicant GPA and County GPA
    #---------------------------------------------------------------------------
    if success == True:
        try:
            Find_Overlaps(wkg_fgdb, applicant_GPAs_fc, county_GPAs_fc, record_id_fld)

        except Exception as e:
            success = False
            print '\n*** ERROR with Find_Overlaps() ***'
            print str(e)


    #---------------------------------------------------------------------------
    #               Merge the Applicant and County GPAs
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # Merge the Applicant GPA and County GPA
            in_features = [applicant_GPAs_fc, county_GPAs_fc]
            merged_fc = os.path.join(wkg_fgdb, 'In_Process_ALL_GPAs')
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
    #           Intersect the Merged GPAs with the Housing Model Output
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
##    sys.stdout = orig_stdout
    sys.stdout.flush()

    if success == True:
        print '\nSUCCESSFULLY ran {}'.format(name_of_script)
    else:
        print '\n*** ERROR with {} ***'.format(name_of_script)

##    print 'Please find log file at:\n  {}\n'.format(log_file_date)
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


def Find_Overlaps(wkg_fgdb, fc_1, fc_2, record_id_fld):
    """
    To find and report on the overlaps between two FC's
    """
    print('\n----------------------------------------------------------------')
    print('Starting Find_Overlaps():')

    # Intersect the two FC's to see if there are any overlaps
    print('  Intersect two FCs to see if there are any overlaps:')
    in_features = [fc_1, fc_2]
    intersect_fc = os.path.join(wkg_fgdb, 'Applicant_County_int')
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
        print('  INFO!  There are overlapping parcels:\n')
        print('    Report format is <Record ID 1> overlaps with <Record ID 2>')
        print('      RECORD ID 1 is from:  {}'.format(os.path.basename(fc_1)))
        print('      RECORD ID 2 is from:  {}\n'.format(os.path.basename(fc_2)))

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
    arcpy.AlterField_management(dissolve_fc, old_name, new_name)

    old_name = density_fld_fc2
    new_name = 'Density_from_FC_2'
    print('    Changing field name from: [{}] to: [{}]'.format(old_name, new_name))
    arcpy.AlterField_management(dissolve_fc, old_name, new_name)

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
def Unmerge_APNs(csv_table_w_merged, csv_table_unmerged, record_id_fld, apn_fld, gp_code_fld):
    """
    Unmerge the APNs that are in one cell and create one row for every APN
    while still keeping all the data that was in the extract
    """

    print '\n------------------------------------------------------------------'
    print 'Starting Unmerge_APNs()\n'


    # Get the schema from the imported table and delete the existing data
    print '  Get the schema from the imported table and delete the existing data:'
    print '    Copying table from:\n      {}\n    To:\n      {}\n'.format(csv_table_w_merged, csv_table_unmerged)
    out_path, out_name = os.path.split(csv_table_unmerged)
    arcpy.TableToTable_conversion(csv_table_w_merged, out_path, out_name)

    print '    Deleting rows in:\n    {}\n'.format(csv_table_unmerged)
    arcpy.DeleteRows_management(csv_table_unmerged)

    #---------------------------------------------------------------------------
    #                             Format the APN field

    # Format the APN field to remove the dashes
    expression = '!{}!.replace("-","")'.format(apn_fld)
    print '\n  Removing dashes in the field [{}] to equal: {}\n'.format(apn_fld, expression)
    arcpy.CalculateField_management(csv_table_w_merged, apn_fld, expression, 'PYTHON_9.3')

    # Format the APN field to remove any whitespace
    expression = '!{}!.replace(" ","")'.format(apn_fld)
    print '\n  Removing white space in the field [{}] to equal: {}\n'.format(apn_fld, expression)
    arcpy.CalculateField_management(csv_table_w_merged, apn_fld, expression, 'PYTHON_9.3')


    #---------------------------------------------------------------------------
    #            Unmerge all rows that had more than one APNs
    #                so that there is one APN per cell

    print '  Unmerge the APNs listed in one cell to have one APN per cell'

    # Loop through each row that has more than 10 characters in it (i.e. has more than 1 APN)
    search_fields = [record_id_fld, apn_fld, gp_code_fld]
    where_clause = "CHAR_LENGTH({}) > 10".format(apn_fld)
    with arcpy.da.SearchCursor(csv_table_w_merged, search_fields, where_clause) as search_cursor:
        for row in search_cursor:
            # Set the values from the cursor into temp variables
            rec_id      = row[0]
            apn         = row[1]
            gp_cd       = row[2]


            # Create a list based off each comma
            apn_list = apn.split(',')


            # For each apn that was in the cell, create a new record with only that APN
            # Keep information for the Record ID, APN, and GP Code fields
            for apn in apn_list:
                print '    Record ID: {}  has APN: {}  and GP code: {}'.format(rec_id, apn, gp_cd)  # For testing

                # The schema for the seperate APN table should be identical to the CSV extract
                # So the fields we want to write data to should be the same name
                # and in the same order
                insert_fields = search_fields

                row_value     = [(rec_id, apn, gp_cd)]

                with arcpy.da.InsertCursor(csv_table_unmerged, insert_fields) as insert_cursor:
                    for row in row_value:
                        insert_cursor.insertRow(row)
                del insert_cursor
    del search_cursor


    #---------------------------------------------------------------------------
    #            Salect and Append all the records that had only one
    #                     APN into the csv_table_unmerged
    #              (faster than using the insert cursor above)

    where_clause = "CHAR_LENGTH({}) = 10".format(apn_fld)
    print '\n  Selecting all the records that had only one APN (nothing to unmerge) from:\n    {}'.format(csv_table_w_merged)
    one_apn_lyr = Select_By_Attribute(csv_table_w_merged, 'NEW_SELECTION', where_clause)

    count = Get_Count_Selected(one_apn_lyr)

    if count != 0:
        inputs = [one_apn_lyr]
        target = csv_table_unmerged
        print '  Appending selected records to:\n    {}'.format(target)
        arcpy.Append_management(inputs, target, 'NO_TEST')


    print '\nFinished Unmerge_APNs()'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Get_Parcels(csv_table, PARCELS_ALL, PARCELS_HISTORICAL, from_parcels_all_fc, from_parcels_hist_fc, apn_fld):
    """
    Get the parcel footprint and tabular data from PARCELS_ALL and PARCELS_HISTORICAL
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

    # Determine if we need to search PARCELS_HISTORICAL
    if len(apns_not_found_in_parcels_all) == 0:
        search_historic_parcels = False
        print '    All APNs in table were found in PARCELS_ALL, no need to search PARCELS_HISTORICAL\n'

    else:
        search_historic_parcels = True
        print '    There were "{}" APNs not found in PARCELS_ALL, searching PARCELS_HISTORICAL\n'.format(len(apns_not_found_in_parcels_all))


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           PARCELS_HISTORICAL
    #          Select from PARCELS_HISTORICAL and export to local FGDB

    apns_found_in_parcels_hist = []
    apns_not_found_anywhere = []

    if search_historic_parcels == True:

        # Make Feature Layer for PARCELS_HISTORICAL
        arcpy.MakeFeatureLayer_management(PARCELS_HISTORICAL, 'parcels_historical_lyr')

        # Select parcels from PARCELS_HISTORICAL that are in the APN table
        print '  ------------------------------------------------------------------'
        print '  Selecting parcels from PARCELS_HISTORICAL that are in the APN table:'
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
            print '  Exporting "{}" selected parcels from PARCELS_HISTORICAL to:\n    {}\{}'.format(count, out_path, out_name)
            arcpy.FeatureClassToFeatureClass_conversion('parcels_historical_lyr', out_path, out_name)
        else:
            '  No features selected from PARCELS_HISTORICAL'

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
      Unique APN's that were found from PARCELS_HISTORICAL
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


    # Find unique list of APNs from PARCELS_HISTORICAL
    if arcpy.Exists(from_parcels_hist_fc):
        print '  Getting APNs from FC:\n    {}'.format(from_parcels_hist_fc)
        fields = ['APN']
        with arcpy.da.SearchCursor(from_parcels_hist_fc, fields) as cursor:
            for row in cursor:
                apn = row[0]

                if apn not in apns_found_in_parcels_hist:
                    apns_found_in_parcels_hist.append(apn)
        del cursor
    print '    There were "{}" unique parcels found from PARCELS_HISTORICAL\n'.format(len(apns_found_in_parcels_hist))


    # Find unique list of APNs not found anywhere
    print '  Getting APNs that were not found in PARCELS_ALL or PARCELS_HISTORICAL'
    for csv_apn in apns_from_imported_csv:
        if (csv_apn not in apns_found_in_parcels_all) and (csv_apn not in apns_found_in_parcels_hist):
            if csv_apn not in apns_not_found_anywhere:
                apns_not_found_anywhere.append(csv_apn)
    print '    There were "{}" unique parcels not found in either FC\n'.format(len(apns_not_found_anywhere))


    print 'Finished Get_APN_Lists()'

    return apns_from_imported_csv, apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def QA_QC(csv_table, from_parcels_all_fc, from_parcels_hist_fc, apns_from_imported_csv, apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere, apn_fld, record_id_fld, gp_code_fld, acreage_cutoff_for_overlap):
    """
    Perform QA/QC on the csv_table.  The below checks are performed:
      1)  Which APNs from the CSV were not found in PARCELS_ALL or PARCELS_HISTORICAL?
      2)  Find if Parcels showed up more than one time in the CSV table
      3)  Is there an overlap with a current parcel and an historic parcel?
      4)  Check any critical fields to ensure there are no blank values

    This is only for reporting purposes, this function does not edit the data
    """

    print '\n--------------------------------------------------------------------'
    print 'Start QA_QC()'

    data_pass_QAQC_tests = True

    #---------------------------------------------------------------------------
    # 1)  Which APNs from the CSV were not found in PARCELS_ALL or PARCELS_HISTORICAL?
    print '\n  1) Finding which APNs from the CSV were not found in PARCELS_ALL or PARCELS_HISTORICAL:\n'

    if len(apns_not_found_anywhere) == 0:
        print '\n    OK! All APNs were found in either PARCELS_ALL or PARCELS_HISTORICAL'

    else:
        data_pass_QAQC_tests = False
        print '    WARNING!  There are "{}" APNs that were not found in PARCELS_ALL or PARCELS_HISTORICAL:'.format(len(apns_not_found_anywhere))
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

    # Check to see if any parcels came from PARCELS_HISTORICAL, no need to check
    #   If there are no parcels from PARCELS_HISTORICAL
    if not arcpy.Exists(from_parcels_hist_fc):
        print '      OK! There were no parcels found in PARCELS_HISTORICAL'
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
    critical_fields = [record_id_fld, apn_fld, gp_code_fld]
    for f in critical_fields:

        # Set the where clause
        if f == gp_code_fld:  # Set a where clause for an integer field
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
def Get_DENSITY_Per_Project_w_GP_CD(parcels_joined_fc, record_id_fld, gp_code_fld, unconstrained_density_fld, density_fld):
    """
    The main goal of this function is to find the DENSITY of each project using
    the Area and the dictionary "gen_plan_dict" to relate the GP code and the
    amound of dwelling units allowed per acre
    """
    print '\n------------------------------------------------------------------'
    print 'Starting Get_DENSITY_Per_Project_w_GP_CD()'

    # Set variables
    wkg_fgdb = os.path.dirname(parcels_joined_fc)


    # Dictionary of the {general plan code : general plan description}
    gen_plan_dict = {
        0:0,
        1:30,
        2:24,
        3:15,
        4:10.9,
        5:7.3,
        6:4.3,
        7:2.9,
        8:2,
        9:1,
        10:1,
        11:0.5,
        12:0.5,
        13:0.25,
        14:0.25,
        15:0.25,
        17:0.1,
        18:0.05,
        19:0.025,
        20:0.0125,
        21:0.00625,
        22:0,
        23:0,
        24:0,
        25:0,
        26:0,
        27:0,
        28:0,
        29:0,
        30:0,
        31:0,
        32:0,
        33:0,
        34:0,
        35:0,
        36:0,
        37:0,
        38:0,
        39:30,
        40:20,
        41:2,
        42:0
        }

    #---------------------------------------------------------------------------
    #                      Add field to hold density
    print '\n  Adding field:'
    field_name = unconstrained_density_fld
    field_type = 'DOUBLE'
    print '    [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(parcels_joined_fc, field_name, field_type)


    #---------------------------------------------------------------------------
    #                         Calculate density field
    # Get the code from the FC and then get the correct value from the dictionary
    print '\n  Calculating Density field based on the GP Dictionary provided at the beginning of this function'
    fields = [gp_code_fld, unconstrained_density_fld]
    with arcpy.da.UpdateCursor(parcels_joined_fc, fields) as cursor:
        for row in cursor:
            gp_code = row[0]  # GP Code from the FC

            try:
                row[1] = gen_plan_dict[gp_code]  # Get the description from the dict and add it to the density field
            except KeyError:
                row[1] = -99  # Add this value to the density field to flag it for deletion later in script

            cursor.updateRow(row)
    del cursor


    #---------------------------------------------------------------------------
    #                              Dissolve data
    #---------------------------------------------------------------------------
    # Dissolve to the dissolve_fields
    dissolve_fields = [record_id_fld, gp_code_fld, unconstrained_density_fld]

    dissolve_fc     = os.path.join(wkg_fgdb, 'Parcels_County_joined_diss_READY2MERGE')
    print '\n  Dissolving FC:\n    {}\n  To:\n    {}\n  On Fields:'.format(parcels_joined_fc, dissolve_fc)
    for f in dissolve_fields:
        print '    {}'.format(f)

    arcpy.Dissolve_management(parcels_joined_fc, dissolve_fc, dissolve_fields, '#', 'SINGLE_PART')


    # Delete any records with -99 density
    fields = [unconstrained_density_fld]
    where_clause = "{} = -99".format(unconstrained_density_fld)
    count = 0
    print '\n  Deleting any rows where: "{}" in FC at:\n    {}'.format(where_clause, dissolve_fc)
    with arcpy.da.UpdateCursor(dissolve_fc, fields, where_clause) as cursor:
        for row in cursor:
            ##print '  {}'.format(row[0])  # For testing
            cursor.deleteRow()
            count +=1

    print '\n    There were {} records deleted\n'.format(count)

    print 'Finished Get_DENSITY_Per_Project_w_GP_CD()'
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
