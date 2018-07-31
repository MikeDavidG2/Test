#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     13/07/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, os, datetime
arcpy.env.overwriteOutput = True

def main():

    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Name of this script
    name_of_script = 'DEV_TRACKER_Process_Applicant_GPAs.py'

    # Set name to give outputs for this script
    shorthand_name    = 'In_Process_Applicant_GPAs'

    # Paths to folders and local FGDBs
    folder_with_csvs  = r"P:\20180510_development_tracker\tables\CSV_Extract_20180713"
    name_of_csv       = 'In-Process Applicant General Plan Amendments (Map 8).csv'
    path_to_csv       = os.path.join(folder_with_csvs, name_of_csv)


    root_folder       = r'P:\20180510_development_tracker\DEV'

    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder       = '{}\{}'.format(root_folder, 'Data')

    imported_csv_fgdb = '{}\{}'.format(data_folder, '1_Imported_CSVs.gdb')

    wkg_fgdb       = '{}\{}'.format(data_folder, '6_{}.gdb'.format(shorthand_name))

    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)


    # Paths to SDE Feature Classes
    PARCELS_HISTORICAL = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCEL_HISTORICAL'
    PARCELS_ALL        = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCELS_ALL'


    # Set field names
    apn_fld           = 'PARCEL_NBR'
    record_id_fld     = 'RECORD_ID'
    du_fld            = 'DWP'


    # Misc variables
    success = True


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
    #                      Create FGDBs if needed
    #---------------------------------------------------------------------------
    # Create import FGDB if it does not exist
    if not arcpy.Exists(imported_csv_fgdb):
        out_folder_path, out_name = os.path.split(imported_csv_fgdb)
        print 'Creating FGDB: "{}" at:\n  {}\n'.format(out_name, out_folder_path)
        arcpy.CreateFileGDB_management(out_folder_path, out_name)

    # Create working FGDB if it does not exist
    if not arcpy.Exists(wkg_fgdb):
        out_folder_path, out_name = os.path.split(wkg_fgdb)
        print 'Creating FGDB: "{}" at:\n  {}\n'.format(out_name, out_folder_path)
        arcpy.CreateFileGDB_management(out_folder_path, out_name)


    #-------------------------------------------------------------------
    #                   Import CSV into FGDB Table
    #-------------------------------------------------------------------

    # Set paths to Feature Classes / Tables
    name_of_csv_table = '{}_Tbl'.format(shorthand_name)
    csv_table = os.path.join(imported_csv_fgdb, name_of_csv_table)

    print '------------------------------------------------------------------'
    print 'Importing CSV to FGDB Table:\n  From:\n    {}'.format(path_to_csv)
    print '  To:\n    {}'.format(imported_csv_fgdb)
    print '  As:\n    {}\n'.format(os.path.basename(csv_table))

    # Import CSV to FGDB Table
    arcpy.TableToTable_conversion(path_to_csv, imported_csv_fgdb, os.path.basename(csv_table))


    #-------------------------------------------------------------------
    #         Get the parcels from PARCELS_ALL and PARCELS_HISTORICAL
    #-------------------------------------------------------------------

    # Format the APN field to remove the dashes
    expression = '!{}!.replace("-","")'.format(apn_fld)
    print 'Removing dashes in the field "{}" to equal: {}\n'.format(apn_fld, expression)
    arcpy.CalculateField_management(csv_table, apn_fld, expression, 'PYTHON_9.3')

    # Get a list of parcels from the imported CSV table
    print 'Getting a list of unique parcels from the imported CSV table:'
    unique_apns_in_csv = []  # List of unique APNs
    duplicate_apns_in_csv = []  # List of duplicates for QA/QC later in script
    count = 0
    with arcpy.da.SearchCursor(csv_table, [apn_fld]) as cursor:
        for row in cursor:
            apn = row[0]

            if apn not in unique_apns_in_csv:
                unique_apns_in_csv.append(apn)
            elif apn not in duplicate_apns_in_csv:
                duplicate_apns_in_csv.append(apn)

            count += 1
    del cursor
    print '  There are a total of "{}" APNs in the imported CSV table'.format(count)
    print '  "{}" Are in the unique APNs list, while "{}" APNs appear in the data 2 times or more\n'.format(len(unique_apns_in_csv), len(duplicate_apns_in_csv))

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           PARCELS_ALL
    #          Select from PARCELS_ALL and export to local FGDB

    # Make Feature Layer for PARCELS_ALL
    arcpy.MakeFeatureLayer_management(PARCELS_ALL, 'parcels_all_lyr')

    # Select parcels from PARCELS_ALL that are in the imported CSV table
    print '--------------------------------------------------------------------'
    print 'Selecting parcels from PARCELS_ALL that are in the imported CSV table'
    for apn in unique_apns_in_csv:

        where_clause = "APN = '{}'".format(apn)
        ##print 'Finding APN: {}'.format(apn)  # For testing
        arcpy.SelectLayerByAttribute_management('parcels_all_lyr', 'ADD_TO_SELECTION', where_clause)

    # Get the count of selected parcels
    count = Get_Count_Selected('parcels_all_lyr')

    # Export the selected parcels (if any)
    if count != 0:
        out_path = wkg_fgdb
        out_name = 'From_PARCELS_ALL'
        from_parcels_all_fc = os.path.join(out_path, out_name)
        print 'Exporting "{}" selected parcels from PARCELS_ALL to:\n  {}\n'.format(count, from_parcels_all_fc)
        arcpy.FeatureClassToFeatureClass_conversion('parcels_all_lyr', out_path, out_name)
    else:
        'No features selected from PARCELS_ALL'

    # Delete the layer with the selection on it
    arcpy.Delete_management('parcels_all_lyr')

    #---------------------------------------------------------------------------
    #        Find out which APNs from the CSV were not found in PARCELS_ALL

    print 'Finding out which APNs from the imported CSV table were not found in PARCELS_ALL\n'

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


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           PARCELS_HISTORICAL
    #          Select from PARCELS_HISTORICAL and export to local FGDB

    # Make Feature Layer for PARCELS_HISTORICAL
    arcpy.MakeFeatureLayer_management(PARCELS_HISTORICAL, 'parcels_historical_lyr')

    # Select parcels from PARCELS_HISTORICAL that are in the imported CSV table
    print '--------------------------------------------------------------------'
    print 'Selecting parcels from PARCELS_HISTORICAL that are in the imported CSV table'
    for apn in apns_not_found_in_parcels_all:

        where_clause = "APN = '{}'".format(apn)
        ##print 'Finding APN: {}'.format(apn)  # For testing
        arcpy.SelectLayerByAttribute_management('parcels_historical_lyr', 'ADD_TO_SELECTION', where_clause)

    # Get the count of selected parcels
    count = Get_Count_Selected('parcels_historical_lyr')

    # Export the selected parcels (if any)
    if count != 0:
        out_path = wkg_fgdb
        out_name = 'From_PARCELS_HISTORICAL'
        from_parcels_hist_fc = os.path.join(out_path, out_name)
        print 'Exporting "{}" selected parcels from PARCELS_HISTORICAL to:\n  {}\{}'.format(count, out_path, out_name)
        arcpy.FeatureClassToFeatureClass_conversion('parcels_historical_lyr', out_path, out_name)
    else:
        'No features selected from PARCELS_HISTORICAL'

    # Delete the layer with the selection on it
    arcpy.Delete_management('parcels_historical_lyr')


    #---------------------------------------------------------------------------
    #        Find out which APNs from the CSV were not found in PARCELS_HISTORICAL

    print '\nFinding out which APNs from the imported CSV table were not found in PARCELS_HISTORICAL or PARCELS_ALL'

    # Get a list of parcels that WERE found in PARCELS_HISTORICAL
    apns_found_in_parcels_hist = []
    apns_not_found_anywhere = []
    with arcpy.da.SearchCursor(from_parcels_hist_fc, ['APN']) as cursor:
        for row in cursor:
            apns_found_in_parcels_hist.append(row[0])
    del cursor

    # Get a list of parcels that were NOT found in PARCELS_ALL or PARCELS_HISTORICAL
    for apn in apns_not_found_in_parcels_all:
        if apn not in apns_found_in_parcels_hist:
            apns_not_found_anywhere.append(apn)

    print '  There were "{}" APNs not found in PARCELS_HISTORICAL or PARCELS_ALL\n'.format(len(apns_not_found_anywhere))


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                                  QA/QC Data
    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    print '--------------------------------------------------------------------'
    print '                      Start QA/QC Section'
    print '---------------------------------------------------------------------'
    print ''
    data_pass_QAQC_tests = True
    #---------------------------------------------------------------------------
    # 1)  Which APNs from the CSV were not found in PARCELS_ALL or PARCELS_HISTORICAL?
    print '1) Finding which APNs from the CSV were not found in PARCELS_ALL or PARCELS_HISTORICAL'
    if len(apns_not_found_anywhere) != 0:
        data_pass_QAQC_tests = False
        print '  WARNING!  There are "{}" APNs that were not found in PARCELS_ALL or PARCELS_HISTORICAL:'.format(len(apns_not_found_anywhere))
        for apn in apns_not_found_anywhere:
            print '    APN:  {}'.format(apn)

            # Get the Record ID(s) associated with that APN
            fields = [apn_fld, record_id_fld]
            where_clause = "{} = '{}'".format(apn_fld, apn)
            with arcpy.da.SearchCursor(csv_table, fields, where_clause) as cursor:
                for row in cursor:
                    print '    With Record ID: {}'.format(row[1])
    else:
        print '\n  OK! All APNs were found in either PARCELS_ALL or PARCELS_HISTORICAL'


    #---------------------------------------------------------------------------
    # 2)  Find if Parcels showed up more than one time in the CSV table
    print '\n2) Finding if parcels showed up more than one time in the CSV table:'
    if len(duplicate_apns_in_csv) != 0:
        data_pass_QAQC_tests = False
        print '\n  WARNING!  There are "{}" APNs that were duplicated in the CSV:'.format(len(duplicate_apns_in_csv))
        for apn in duplicate_apns_in_csv:
            print '    {}'.format(apn)

            # Get the Record ID(s) associated with that APN
            fields = [apn_fld, record_id_fld]
            where_clause = "{} = '{}'".format(apn_fld, apn)
            with arcpy.da.SearchCursor(csv_table, fields, where_clause) as cursor:
                for row in cursor:
                    print '    With Record ID: {}'.format(row[1])

        print '  This might mean that only the parcel from the newest project'
        print '  should be considered in the analysis.  Further human analysis needed.'
    else:
        print '  OK! There were 0 duplicate APNs found in the CSV extract'


    #---------------------------------------------------------------------------
    # 3)  Is there an overlap with a current parcel and an historic parcel?
    print '\n3) Finding any overlaps with current parcels and historic parcels:'

    # Intersect the two FC's to see if there are any overlaps
    in_features       = [from_parcels_all_fc, from_parcels_hist_fc]
    intersect_fc = os.path.join(wkg_fgdb, 'Parcels_ALL_and_HIST_int')
    print '  Intersecting:'
    for fc in in_features:
        print '    {}'.format(fc)
    print '  To create FC:\n    {}\n'.format(intersect_fc)
    arcpy.Intersect_analysis(in_features, intersect_fc)

    # Find out if there are any overlapping parcels
    overlap = False
    with arcpy.da.SearchCursor(intersect_fc, 'OBJECTID') as cursor:
        for row in cursor:
            overlap = True
            break

    if overlap == False:
        print '  OK! There are no overlapping parcels'

    # If there is an overlap, get a list of the parcels that overlap and report on them
    if overlap == True:
        print '  INFO!  There are overlapping parcels from current and historic parcels:'
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
                    print '    APN: "{}" overlaps with APN: "{}"'.format(apn_1, apn_2)
                    print '    but the overlap ({} acres) is <= the script-defined cutoff for analysis ({} acres)'.format(acreage, acreage_cutoff_for_overlap)

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
                            print '    There is overlap between CURRENT parcel "{}" and HISTORIC parcel "{}"'.format(current_apn, historic_apn)
                            print '    But as both are from the same project: "{}", there will be no overlap when the data is dissolved'.format(record_ids_current[0])
                            print '    No need for human analysis, but PDS may want to know that they should update the historic apn in the above project'
                    else:
                        data_pass_QAQC_tests = False
                        print '    WARNING!  The overlap between CURRENT parcel "{}" and HISTORIC parcel "{}" may cause double counting'.format(current_apn, historic_apn)
                        print '    Please let PDS know that they should remove the historic parcel and add current parcel(s) in Accela for project {}'.format(record_ids_historic[0])

        del int_cursor


    #---------------------------------------------------------------------------
    # 4)  Check any critical fields to ensure there are no blank values
    print '\n4) Finding any critical fields that are blank in imported CSV table:\n'
    critical_fields = ['RECORD_ID', 'DWP', 'PARCEL_NBR']
    for f in critical_fields:

        # Set the where clause
        if f == 'DWP':  # Set a where clause for an integer field
            where_clause = "{0} IS NULL".format(f)
        else:  # Set a where clause for a string field
            where_clause = "{0} IS NULL or {0} = ''".format(f)

        # Get list of ids
        print '  Checking where: {}:'.format(where_clause)
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
            print '    WARNING! There are records in the CSV extract that have a NULL value in column: "{}":'.format(f)
            for id_num in ids_w_nulls:
                if (id_num == None) or (id_num == ''):
                    print '      No Record ID available to report'
                else:
                    print '      {}'.format(id_num)
        if len(ids_w_nulls) == 0:
            print '    OK! No null values in {}'.format(f)

        print ''

    print '----------------------------------------------------------------'
    print '                      Finish QA/QC Section'
    print '----------------------------------------------------------------'
    print 'Data Passed all QA/QC tests = {}\n'.format(data_pass_QAQC_tests)


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                  Merge the two parcel FCs, and
    #        Join the result polys with the imported CSV table

    # Merge the current and historical parcels
    in_features = [from_parcels_all_fc, from_parcels_hist_fc]
    merged_fc = os.path.join(wkg_fgdb, 'Parcels_ALL_and_HIST_merge')
    print 'Merging:'
    for f in in_features:
        print '  {}'.format(f)
    print 'To create:\n  {}\n'.format(merged_fc)
    arcpy.Merge_management(in_features, merged_fc)

    # Create a layer with the CSV Imported table joined to the merged FC
    print 'Joining CSV Imported table to the merged FC'
    joined_tbl_lyr = Join_2_Objects_By_Attr(merged_fc, 'APN', csv_table, apn_fld, 'KEEP_ALL')

    # Save the joined layer to disk
    out_path = wkg_fgdb
    out_name = 'Parcels_ALL_and_HIST_merge_joined'
    parcels_merged_joined_fc = os.path.join(out_path, out_name)
    print 'Saving joined layer to:\n  {}\n'.format(parcels_merged_joined_fc)
    arcpy.FeatureClassToFeatureClass_conversion(joined_tbl_lyr, out_path, out_name)


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           Process the Projects

    # Rename the fields in the joined FC back to what they were named in the CSV
    #   (The join performed above names the CSV fields with a prefix of the
    #    table that they came from.  I.e. "In_Process_Applicant_GPAs_Tbl_RECORD_ID")
    # The renaming will simplify readability and scripting below
    print 'Renaming the field names in the joined table back to the names from the imported CSV table:'
    fields_from_csv = arcpy.ListFields(parcels_merged_joined_fc, '{}*'.format(name_of_csv_table))
    for f in fields_from_csv:
        old_name = f.name
        new_name = old_name.replace("{}_".format(name_of_csv_table),"")

        if new_name != 'OBJECTID':  # Don't try to name a field "OBJECTID", just skip this one
            ##print '  Changing Field: "{}"\n  To:  "{}"'.format(old_name, new_name)  # For testing purposes
            arcpy.AlterField_management(parcels_merged_joined_fc, old_name, new_name)


    # The data is now ready for processing
    try:
        Process_Projects(parcels_merged_joined_fc, record_id_fld, du_fld)
    except Exception as e:
        success = False
        print '*** ERROR with Process_Projects() ***'
        print str(e)

    #---------------------------------------------------------------------------
    # Write a file to disk to let other scripts know if this script ran
    # successfully or not
    print '--------------------------------------------------------------------'
    try:
        # Set a file_name depending on the 'success' variable.
        if success == True:
            file_name = 'SUCCESS_running_{}.txt'.format(name_of_script.split('.')[0])

        else:
            file_name = 'ERROR_running_{}.txt'.format(name_of_script.split('.')[0])

        # Write the file
        file_path = '{}\{}'.format(success_error_folder, file_name)
        print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
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
    print 'Data passed QA/QC tests = {}'.format(data_pass_QAQC_tests)
    print 'Successfully ran script = {}'.format(success)
    time.sleep(3)
    sys.stdout = orig_stdout
    sys.stdout.flush()

    if success == True:
        print '\nSUCCESSFULLY ran {}'.format(name_of_script)
        print 'Please find log file at:\n  {}\n'.format(log_file_date)
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
        print '      Made FEATURE LAYER for: {}'.format(target_obj)
    except:
        arcpy.MakeTableView_management(target_obj, 'target_obj')
        print '      Made TABLE VIEW for: {}'.format(target_obj)

    # Create the layer or view for the to_join_obj using try/except
    try:
        arcpy.MakeFeatureLayer_management(to_join_obj, 'to_join_obj')
        print '      Made FEATURE LAYER for: {}'.format(to_join_obj)
    except:
        arcpy.MakeTableView_management(to_join_obj, 'to_join_obj')
        print '      Made TABLE VIEW for: {}'.format(to_join_obj)

    # Join the layers
    print '      Joining "{}"\n         With "{}"\n           On "{}"\n          And "{}"\n         Type "{}"\n'.format(target_obj, to_join_obj, target_join_field, to_join_field, join_type)
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
def Process_Projects(fc, record_id_fld, du_fld):
    """
    """
    print '\n------------------------------------------------------------------'
    print 'Starting Process_Parcels()'
    print '  Processing FC at:\n    {}\n'.format(fc)

    # Set the names of the fields to be added
    parcel_acres_fld    = 'Parcel_Acres'
    project_acres_fld   = 'Project_Acres'
    density_fld         = 'DENSITY'


    #---------------------------------------------------------------------------
    # Get a list of unique RECORD_IDs
    print '  Getting list of all RECORD_IDs:'
    project_ids = []
    with arcpy.da.SearchCursor(fc, [record_id_fld]) as cursor:
        for row in cursor:
            project_ids.append(row[0])
    del cursor

    # Get a list of all the UNIQUE ID's
    # set() returns a list of only unique values
    unique_project_ids = sorted(set(project_ids))
    print '    There are "{}" unique project IDs\n'.format(len(unique_project_ids))


    #---------------------------------------------------------------------------
    # Add fields to hold calculations
    print '  Adding fields:'

    fields_to_add = [parcel_acres_fld, project_acres_fld, density_fld]

    for field_name in fields_to_add:
        field_type = 'DOUBLE'
        print '    [{}] as a:  {}'.format(field_name, field_type)
        arcpy.AddField_management(fc, field_name, field_type)


    #---------------------------------------------------------------------------
    #                             Calculate fields

    # Repair geometry to ensure correct geometry calculation below
    print '\n  Repairing Geometry'
    arcpy.RepairGeometry_management(fc)

    # Calc Acres for each Parcel
    expression      = '!shape.area@acres!'
    expression_type = 'PYTHON_9.3'

    print '\n  Calculating field:\n    {} = {}\n'.format(parcel_acres_fld, expression)
    arcpy.CalculateField_management(fc, parcel_acres_fld, expression, expression_type)


    # Calc Total Project Acres for each Project
    print '  Calculating field: {} to equal the total acreage of each project'.format(project_acres_fld)
    for project in unique_project_ids:

        ##print '  Calculating total acreage of project:  {}'.format(project)  # For testing

        # Get the acreage of the project
        total_project_acres = 0

        where_clause = "{} = '{}'".format(record_id_fld, project)
        fields       = [record_id_fld, parcel_acres_fld, project_acres_fld]
        with arcpy.da.SearchCursor(fc, fields, where_clause) as cursor:
            for row in cursor:
                acres = row[1]
                total_project_acres = (total_project_acres + acres)

        ##print '    Total Project Acres:  {}\n'.format(total_project_acres)  # For testing
        del cursor

        # Set the acreage of the project into the fc
        where_clause = "{} = '{}'".format(record_id_fld, project)
        fields       = [record_id_fld, project_acres_fld]
        with arcpy.da.UpdateCursor(fc, fields, where_clause) as cursor:
            for row in cursor:
                row[1] = total_project_acres
                cursor.updateRow(row)
        del cursor


    # Calc DENSITY designation for each Project
    expression = "!{}!/!{}!".format(du_fld, project_acres_fld)
    print '\n  Calculating field:\n    {} = {}\n'.format(density_fld, expression)
    arcpy.CalculateField_management(fc, density_fld, expression, expression_type)


    #---------------------------------------------------------------------------
    # Dissolve to the project level
    dissolve_fields = [record_id_fld, 'PROJECT_NAME', 'OPEN_DATE', 'WORK_DESC', 'RECORD_STATUS', 'STATUS_DATE', du_fld, project_acres_fld, density_fld]
    dissolve_fc     = os.path.join(os.path.dirname(fc), 'Parcels_Applicant_joined_diss')
    print '\n  Dissolving FC:\n    {}\n  To:\n    {}\n  On Fields:'.format(fc, dissolve_fc)
    for f in dissolve_fields:
        print '    {}'.format(f)

    arcpy.Dissolve_management(fc, dissolve_fc, dissolve_fields, '#', 'SINGLE_PART')


    #---------------------------------------------------------------------------
    # Delete any records that do not have a value in the Dwelling Unit field
    #   (which would result in not having a value in the Density field)
    print '\n\n  Checking for any records that do not have a value in the Dwelling Unit field'
    print '    since this would cause a null value in the density field, resulting in bad data'
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

    #---------------------------------------------------------------------------
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

    print '\nFinished Process_Parcels()'


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

    print '\n    Starting Select_By_Attribute()...'

    # Use try/except to handle either object type (Feature Layer / Table)
    try:
        arcpy.MakeFeatureLayer_management(path_to_obj, 'lyr')
    except:
        arcpy.MakeTableView_management(path_to_obj, 'lyr')

    print '      Selecting "lyr" with a selection type: {}, where: "{}"'.format(selection_type, where_clause)
    arcpy.SelectLayerByAttribute_management('lyr', selection_type, where_clause)

    print '    Finished Select_By_Attribute()\n'
    return 'lyr'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
