#-------------------------------------------------------------------------------
# Name:        DEV_TRACKER_Process_County_GPAs.py
# Purpose:
"""
To process the "In-Process County General Plan Amendments (Map 8).csv" by
producing a Feature Class that contains the outlines of Record ID's (projects)
and their DENSITY by polygon
"""

#
# Author:      mgrue
#
# Created:     19/07/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, os, datetime

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Name of this script
    name_of_script = 'DEV_TRACKER_Process_County_GPAs.py'


    # Field Names from the extract
    apn_fld           = 'APNS'
    record_id_fld     = 'RECORD_ID'
    gp_code_fld       = 'GPCODE95'

    # Field Names created by script
    density_fld       = 'DENSITY'


    # Paths to folders and local FGDBs
    folder_with_csvs  = r"P:\20180510_development_tracker\tables\CSV_Extract_20180713"
    name_of_csv       = 'In-Process County General Plan Amendments (Map 8).csv'
    path_to_csv       = os.path.join(folder_with_csvs, name_of_csv)

    shorthand_name    = 'In_Process_County_GPAs'

    root_folder             = r'P:\20180510_development_tracker\DEV'
    log_file_folder         = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')
    data_folder             = '{}\{}'.format(root_folder, 'Data')
    imported_csv_fgdb       = '{}\{}'.format(data_folder, '1_Imported_CSVs.gdb')
    wkg_fgdb                = '{}\{}'.format(data_folder, '7_{}.gdb'.format(shorthand_name))
    apn_tbl                 = '{}\{}'.format(wkg_fgdb, 'APNs_Seperated')
    in_process_all_gpa_fgdb = '{}\{}'.format(data_folder, '8_In_Process_All_GPAs.gdb')

    # Hard coded path to the FC that represents the final data from the In Process Applicant GPA script
    in_process_applicant_gpa_fc = r'P:\20180510_development_tracker\DEV\Data\6_In_Process_Applicant_GPAs.gdb\Parcels_Applicant_joined_diss'

    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)


    # Paths to SDE Feature Classes
    PARCELS_HISTORICAL = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCEL_HISTORICAL'

    PARCELS_ALL        = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCELS_ALL'


    # Misc variables
    success = True
    arcpy.env.overwriteOutput = True

    # This is the acreage that an overlap of a current parcel and a historic parcel
    # from two different projects needs to be greater than in order for the
    # script to flag it as needing human analysis
    acreage_cutoff_for_overlap = 0.1

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
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Running

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


    # Delete and create working FGDB
    if arcpy.Exists(wkg_fgdb):
        print 'Deleting FGDB at:\n  {}\n'.format(wkg_fgdb)
        arcpy.Delete_management(wkg_fgdb)

    if not arcpy.Exists(wkg_fgdb):
        out_folder_path, out_name = os.path.split(wkg_fgdb)
        print 'Creating FGDB: {}\{}\n'.format(out_folder_path, out_name)
        arcpy.CreateFileGDB_management(out_folder_path, out_name)

    # Create merged FGDB if it does not exist
    if not arcpy.Exists(in_process_all_gpa_fgdb):
        out_folder_path, out_name = os.path.split(in_process_all_gpa_fgdb)
        print 'Creating FGDB: "{}" at:\n  {}\n'.format(out_name, out_folder_path)
        arcpy.CreateFileGDB_management(out_folder_path, out_name)

    #---------------------------------------------------------------------------
    #                       Import CSV into FGDB Table
    #---------------------------------------------------------------------------

    # Set paths to Feature Classes / Tables
    name_of_csv_table = '{}_Tbl'.format(shorthand_name)
    csv_table = os.path.join(imported_csv_fgdb, name_of_csv_table)

    print '------------------------------------------------------------------'
    print 'Importing CSV to FGDB Table:\n  From:\n    {}'.format(path_to_csv)
    print '  To:\n    {}'.format(imported_csv_fgdb)
    print '  As:\n    {}\n'.format(os.path.basename(csv_table))

    # Import CSV to FGDB Table
    arcpy.TableToTable_conversion(path_to_csv, imported_csv_fgdb, os.path.basename(csv_table))


    #---------------------------------------------------------------------------
    #                            Seperate the APNs
    #             (from many APNs in one cell to one row per APN)
    #---------------------------------------------------------------------------

    Seperate_APNs(csv_table, apn_tbl, record_id_fld, apn_fld, gp_code_fld)


    #---------------------------------------------------------------------------
    #         Get the parcels from PARCELS_ALL and PARCELS_HISTORICAL
    #---------------------------------------------------------------------------
    # Set path for the FC to be created from PARCELS_ALL
    out_path = wkg_fgdb
    out_name = 'From_PARCELS_ALL'
    from_parcels_all_fc = os.path.join(out_path, out_name)

    # Set path for the FC to be created from PARCELS_HISTORICAL
    out_path = wkg_fgdb
    out_name = 'From_PARCELS_HISTORICAL'
    from_parcels_hist_fc = os.path.join(out_path, out_name)

    # Get parcels (and lists of APNs)
    (apns_found_in_parcels_all,
    apns_found_in_parcels_hist,
    apns_not_found_anywhere) = Get_Parcels(apn_tbl, PARCELS_ALL, PARCELS_HISTORICAL, from_parcels_all_fc, from_parcels_hist_fc, apn_fld)


    #---------------------------------------------------------------------------
    #         Perform QA/QC on the extracted data and the parcels
    #---------------------------------------------------------------------------
    data_pass_QAQC_tests = QA_QC(apn_tbl, wkg_fgdb, from_parcels_all_fc, from_parcels_hist_fc, apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere, apn_fld, record_id_fld, gp_code_fld, acreage_cutoff_for_overlap, gen_plan_dict)


    #---------------------------------------------------------------------------
    #            Join the Parcel FC with the tabular extracted data
    #---------------------------------------------------------------------------
    #        Merge from_parcels_all_fc and from_parcels_hist_fc (if needed)
    if arcpy.Exists(from_parcels_hist_fc):  # Only merge if there are parcels from PARCELS_HISTORICAL

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
        joined_name     = 'Parcels_ALL_and_HIST_merge_joined'

    else:
        # Set that we want to join to the 'From PARCELS_ALL FC' and set the name of the joined FC
        fc_to_be_joined = from_parcels_all_fc
        joined_name     = 'Parcels_ALL_joined'

    # Create a layer with the APN table joined to the parcel FC
    print '\nJoining APN table to the parcel FC'
    joined_tbl_lyr = Join_2_Objects_By_Attr(fc_to_be_joined, 'APN', apn_tbl, apn_fld, 'KEEP_ALL')

    # Save the joined layer to disk
    out_path = wkg_fgdb
    parcels_joined_fc = os.path.join(out_path, joined_name)
    print 'Saving joined layer to:\n  {}\n'.format(parcels_joined_fc)
    arcpy.FeatureClassToFeatureClass_conversion(joined_tbl_lyr, out_path, joined_name)

    # Rename the fields in the joined FC back to what they were named in the CSV
    #   (The join performed above names the CSV fields with a prefix of the
    #    table that they came from.  I.e. "In_Process_Applicant_GPAs_Tbl_RECORD_ID")
    # The renaming will simplify readability and scripting below
    print 'Renaming the field names in the joined table back to the names from the imported CSV table:'
    where_clause = '{}*'.format(os.path.basename(apn_tbl))
    print '  Where:  {}'.format(where_clause)
    fields_from_csv = arcpy.ListFields(parcels_joined_fc, where_clause)
    for f in fields_from_csv:
        old_name = f.name
        new_name = old_name.replace("{}_".format(os.path.basename(apn_tbl)),"")

        if new_name != 'OBJECTID':  # Don't try to name a field "OBJECTID", just skip this one
            print '  Changing Field: "{}"\n  To:  "{}"'.format(old_name, new_name)  # For testing purposes
            arcpy.AlterField_management(parcels_joined_fc, old_name, new_name)


    #---------------------------------------------------------------------------
    #                   Add DENSITY field and calculate it
    #---------------------------------------------------------------------------

    # Add field to hold density
    print '\nAdding field:'
    field_name = density_fld
    field_type = 'DOUBLE'
    print '  [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(parcels_joined_fc, field_name, field_type)


    # Calculate the Density field by using the below dictionary

    # Calculate field by getting the code from the FC and then getting the
    #   correct value from the dictionary
    print '\nCalculating Density field based on the GP Dictionary provided at the beginning of the script'
    fields = [gp_code_fld, density_fld]
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
    dissolve_fields = [record_id_fld, 'PROJECT_NAME', 'OPEN_DATE', 'WORK_DESC', 'RECORD_STATUS', 'STATUS_DATE', gp_code_fld, density_fld]
    dissolve_fc     = os.path.join(wkg_fgdb, 'Parcels_County_joined_diss')
    print '\nDissolving FC:\n  {}\nTo:\n  {}\nOn Fields:'.format(parcels_joined_fc, dissolve_fc)
    for f in dissolve_fields:
        print '  {}'.format(f)

    arcpy.Dissolve_management(parcels_joined_fc, dissolve_fc, dissolve_fields, '#', 'SINGLE_PART')


    # Delete any records with -99 density
    fields = [density_fld]
    where_clause = "{} = -99".format(density_fld)
    count = 0
    print '\nDeleting any rows where: "{}" in FC at:\n  {}'.format(where_clause, dissolve_fc)
    with arcpy.da.UpdateCursor(dissolve_fc, fields, where_clause) as cursor:
        for row in cursor:
            ##print '  {}'.format(row[0])  # For testing
            cursor.deleteRow()
            count +=1

    print '\n  There were {} records deleted\n'.format(count)


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                     Merge Applicant and County GPA data
    #---------------------------------------------------------------------------
    """
    This section is intended to merge data that was processed by another script
    (3_DEV_TRACKER_Process_Applicant_GPAs.py) with the data that was processed
    by this script above.  Basically we got an extract of the Applicant initiated GPA's
    that was processed by the other script and an extract of the County initiated GPA's
    We first need to check to see if there is any overlap between these two
    datasets (and report on it if so).
    Then we need to merge them together so that they are both in one Feature Class
    """

    #---------------------------------------------------------------------------
    #                              QA/QC for overlap
    # Intersect the two datasets (Applicant GPAs and County GPAs) to see if there is any
    # overlap and report if so

    print 'Performing QA/QC to see if there are any overlapse from the Applicant GPAs and the County GPAs\n'
    in_features = [in_process_applicant_gpa_fc, dissolve_fc]
    intersect_fc = os.path.join(in_process_all_gpa_fgdb, 'Applicant_County_GPAs_int')
    print '\nIntersecting:'
    for fc in in_features:
        print '  {}'.format(fc)
    print 'To create FC:\n  {}\n'.format(intersect_fc)
    arcpy.Intersect_analysis(in_features, intersect_fc)

    # Find out if there are any overlapping projects
    overlap = False
    with arcpy.da.SearchCursor(intersect_fc, 'OBJECTID') as cursor:
        for row in cursor:
            overlap = True
            break

    if overlap == False:
        print '  OK! There are no overlaps'

    # If there is an overlap, get a list of the projects that overlap and report on them
    if overlap == True:

        # Repair the geometry
        arcpy.RepairGeometry_management(intersect_fc)

        print '  There are overlapping projects from the Applicant GPAs and County GPAs:'
        id_of_overlap = []
        fields = ['RECORD_ID', 'RECORD_ID_1', 'Shape_Area']
        with arcpy.da.SearchCursor(intersect_fc, fields) as int_cursor:
            for row in int_cursor:
                id_1 = row[0]
                id_2 = row[1]
                sq_ft = row[2]

                # Get the acreage of the overlap feature
                acreage = sq_ft/43560

                if acreage <= acreage_cutoff_for_overlap:
                    print '    APN: "{}" overlaps with APN: "{}"'.format(apn_1, apn_2)
                    print '    but the overlap ({} acres) is <= the script-defined cutoff for analysis ({} acres)'.format(acreage, acreage_cutoff_for_overlap)

                # Only analyze overlaps that are large enough to matter
                if acreage > acreage_cutoff_for_overlap:
                    data_pass_QAQC_tests = False
                    print '    WARNING! The below projects overlap:'
                    print '      Record ID:  {}\n      Record ID:  {}\n      By "{}" acres'.format(id_1, id_2, acreage)
                    print '    The area of overlap will be double counted.\n'


    #---------------------------------------------------------------------------
    #                          Merge the two FCs
    print 'Merge the two FCs to create one FC with All In Process GPAs'
    in_features = [dissolve_fc, in_process_applicant_gpa_fc]
    merged_fc   = os.path.join(in_process_all_gpa_fgdb, 'In_Process_GPAs')

    print '\nMerging:'
    for fc in in_features:
        print '  {}'.format(fc)
    print 'To create FC:\n  {}\n'.format(merged_fc)
    arcpy.Merge_management(in_features, merged_fc)



    #---------------------------------------------------------------------------
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
def Seperate_APNs(csv_table, apn_tbl, record_id_fld, apn_fld, gp_code_fld):
    """
    Seperate the APNs that are in one cell and create one row for every APN
    while still keeping all the data that was in the extract
    """

    print '\n------------------------------------------------------------------'
    print 'Starting Seperate_APNs()\n'


    # Get the schema from the imported table and delete the existing data
    print '  Get the schema from the imported table and delete the existing data:'
    print '    Copying table from:\n      {}\n    To:\n      {}\n'.format(csv_table, apn_tbl)
    out_path, out_name = os.path.split(apn_tbl)
    arcpy.TableToTable_conversion(csv_table, out_path, out_name)

    print '    Deleting rows in:\n    {}\n'.format(apn_tbl)
    arcpy.DeleteRows_management(apn_tbl)


    #---------------------------------------------------------------------------
    #          Seperate the APNs listed in one cell to have one APN per cell

    print '  Seperate the APNs listed in one cell to have one APN per cell'

    # Set the field names in the order that they appear in the extract
    search_fields = [record_id_fld, apn_fld, gp_code_fld]

    with arcpy.da.SearchCursor(csv_table, search_fields) as search_cursor:
        for row in search_cursor:
            # Set the values from the cursor into temp variables
            rec_id      = row[0]
            apn         = row[1]
            gp_cd       = row[2]

            # Format the APN string and get a list of APNs that were in the one cell
            apn = apn.replace(' ', '')  # Remove any whitespace
            apn_list = apn.split(',')   # Create a list based off each comma

            # For each apn that was in the cell, create a new record with only that APN
            # But retain all the information that was in the extract
            for apn in apn_list:
                ##print '  Record ID: {}  has APN: {}  and GP code: {}'.format(rec_id, apn, gp_cd)  # For testing

                # The schema for the seperate APN table should be identical to the CSV extract
                # So the fields we want to write data to should be the same name
                # and in the same order
                insert_fields = search_fields

                row_value     = [(rec_id, apn, gp_cd)]

                with arcpy.da.InsertCursor(apn_tbl, insert_fields) as insert_cursor:
                    for row in row_value:
                        insert_cursor.insertRow(row)

    print '\nFinished Seperate_APNs()'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Get_Parcels(apn_tbl, PARCELS_ALL, PARCELS_HISTORICAL, from_parcels_all_fc, from_parcels_hist_fc, apn_fld):
    """
    Get the parcel footprint and tabular data from PARCELS_ALL and PARCELS_HISTORICAL
    and select which parcels to export from the apn_tbl. Save the exports in the
    wkg_fgdb
    """

    print '\n--------------------------------------------------------------------'
    print 'Start Get_Parcels()\n'

    print '  Getting APNs from table:\n    {}'.format(apn_tbl)

    # Format the APN field to remove the dashes
    expression = '!{}!.replace("-","")'.format(apn_fld)
    print '\n  Removing dashes in the field "{}" to equal: {}\n'.format(apn_fld, expression)
    arcpy.CalculateField_management(apn_tbl, apn_fld, expression, 'PYTHON_9.3')

    # Get a list of parcels from the seperated APN table
    print '  Getting a list of unique parcels from the seperated APN table:'
    unique_apns_in_csv = []  # List of unique APNs
    count = 0
    with arcpy.da.SearchCursor(apn_tbl, [apn_fld]) as cursor:
        for row in cursor:
            apn = row[0]

            if apn not in unique_apns_in_csv:
                unique_apns_in_csv.append(apn)

            count += 1
    del cursor
    print '    There are a total of "{}" rows in the seperated APN table'.format(count)
    print '    There are "{}" unique APNs in the seperated APN table\n'.format(len(unique_apns_in_csv))


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           PARCELS_ALL
    #          Select from PARCELS_ALL and export to local FGDB

    # Make Feature Layer for PARCELS_ALL
    arcpy.MakeFeatureLayer_management(PARCELS_ALL, 'parcels_all_lyr')

    # Select parcels from PARCELS_ALL that are in the seperated APN table
    print '  ------------------------------------------------------------------'
    print '  Selecting parcels from PARCELS_ALL that are in the seperated APN table:'
    for apn in unique_apns_in_csv:

        where_clause = "APN = '{}'".format(apn)
        ##print 'Finding APN: {}'.format(apn)  # For testing
        arcpy.SelectLayerByAttribute_management('parcels_all_lyr', 'ADD_TO_SELECTION', where_clause)

    # Get the count of selected parcels
    print '    Getting count of selected parcels'
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

    print '\n  Finding out which APNs from the seperated APN table were not found in PARCELS_ALL:'

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
        print '  There were "{}" APNs not found in PARCELS_ALL, searching PARCELS_HISTORICAL\n'.format(len(apns_not_found_in_parcels_all))


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                           PARCELS_HISTORICAL
    #          Select from PARCELS_HISTORICAL and export to local FGDB

    apns_found_in_parcels_hist = []
    apns_not_found_anywhere = []

    if search_historic_parcels == True:

        # Make Feature Layer for PARCELS_HISTORICAL
        arcpy.MakeFeatureLayer_management(PARCELS_HISTORICAL, 'parcels_historical_lyr')

        # Select parcels from PARCELS_HISTORICAL that are in the seperated APN table
        print '--------------------------------------------------------------------'
        print 'Selecting parcels from PARCELS_HISTORICAL that are in the seperated APN table'
        for apn in apns_not_found_in_parcels_all:

            where_clause = "APN = '{}'".format(apn)
            ##print 'Finding APN: {}'.format(apn)  # For testing
            arcpy.SelectLayerByAttribute_management('parcels_historical_lyr', 'ADD_TO_SELECTION', where_clause)

        # Get the count of selected parcels
        count = Get_Count_Selected('parcels_historical_lyr')

        # Export the selected parcels (if any)
        if count != 0:
            out_path, out_name = os.path.split(from_parcels_hist_fc)
            print 'Exporting "{}" selected parcels from PARCELS_HISTORICAL to:\n  {}\{}'.format(count, out_path, out_name)
            arcpy.FeatureClassToFeatureClass_conversion('parcels_historical_lyr', out_path, out_name)
        else:
            'No features selected from PARCELS_HISTORICAL'

        # Delete the layer with the selection on it
        arcpy.Delete_management('parcels_historical_lyr')


        #---------------------------------------------------------------------------
        #                 Find out which APNs from the CSV
        #       were not found in PARCELS_HISTORICAL or PARCELS_ALL

        print '\nFinding out which APNs from the seperated APN table were not found in PARCELS_HISTORICAL or PARCELS_ALL'

        # First, find delea list of parcels that WERE found in PARCELS_HISTORICAL
        if arcpy.Exists(from_parcels_hist_fc):
            with arcpy.da.SearchCursor(from_parcels_hist_fc, ['APN']) as cursor:
                for row in cursor:
                    apns_found_in_parcels_hist.append(row[0])
            del cursor

        # Next, get a list of parcels that were NOT found in PARCELS_ALL or PARCELS_HISTORICAL
        for apn in apns_not_found_in_parcels_all:
            if apn not in apns_found_in_parcels_hist:
                apns_not_found_anywhere.append(apn)

        print '  There were "{}" APNs not found in PARCELS_HISTORICAL or PARCELS_ALL\n'.format(len(apns_not_found_anywhere))

    print 'Finished Get_Parcels()'

    return apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def QA_QC(apn_tbl, wkg_fgdb, from_parcels_all_fc, from_parcels_hist_fc, apns_found_in_parcels_all, apns_found_in_parcels_hist, apns_not_found_anywhere, apn_fld, record_id_fld, gp_code_fld, acreage_cutoff_for_overlap, gen_plan_dict):
    """
    """

    print '\n--------------------------------------------------------------------'
    print 'Start QA_QC()'

    data_pass_QAQC_tests = True

    #---------------------------------------------------------------------------
    # 1)  Which APNs from the CSV were not found in PARCELS_ALL or PARCELS_HISTORICAL?
    print '  1) Finding which APNs from the CSV were not found in PARCELS_ALL or PARCELS_HISTORICAL:'

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
            with arcpy.da.SearchCursor(apn_tbl, fields, where_clause) as cursor:
                for row in cursor:
                    print '      With Record ID: {}'.format(row[1])

            del cursor


    #---------------------------------------------------------------------------
    # 2)  Find if Parcels showed up more than one time in the CSV table
    print '\n  2) Finding if parcels showed up more than one time in the CSV table:'

    # Get a list of parcels from the seperated APN table
    print '    Getting a list of unique parcels from the seperated APN table:'
    unique_apns_in_csv = []  # List of unique APNs
    duplicate_apns_in_csv = []
    count = 0
    with arcpy.da.SearchCursor(apn_tbl, [apn_fld]) as cursor:
        for row in cursor:
            apn = row[0]

            if apn not in unique_apns_in_csv:
                unique_apns_in_csv.append(apn)
            elif apn not in duplicate_apns_in_csv:
                duplicate_apns_in_csv.append(apn)
    del cursor

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
            with arcpy.da.SearchCursor(apn_tbl, fields, where_clause) as cursor:
                for row in cursor:
                    print '        With Record ID: {}'.format(row[1])

        print '\n    This might mean that only the parcel from the newest project'
        print '    should be considered in the analysis.  Further human analysis needed.'



    #---------------------------------------------------------------------------
    # 3)  Is there an overlap with a current parcel and an historic parcel?
    print '\n  3) Finding any overlaps with current parcels and historic parcels:'

    # Check to see if any parcels came from PARCELS_HISTORICAL, no need to check
    #   If there are no parcels from PARCELS_HISTORICAL
    if not arcpy.Exists(from_parcels_hist_fc):
        print '\n      OK! There were no parcels found in PARCELS_HISTORICAL'
        print '      Therefore there can be no overlap'

    else:  # There might be an overlap, continue checking...

        # Intersect the two FC's to see if there are any overlaps
        in_features = [from_parcels_all_fc, from_parcels_hist_fc]
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
            print '    OK! There are no overlapping parcels'

        # If there is an overlap, get a list of the parcels that overlap and report on them
        if overlap == True:
            print '    INFO!  There are overlapping parcels from current and historic parcels:'
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
                        with arcpy.da.SearchCursor(apn_tbl, fields, where_clause) as csv_cursor:
                            for row in csv_cursor:
                                record_ids_historic.append(row[1])
                        del csv_cursor

                        # Get the Record ID(s) associated with the current APN
                        record_ids_current = []
                        fields = [apn_fld, record_id_fld]
                        where_clause = "{} = '{}'".format(apn_fld, current_apn)
                        with arcpy.da.SearchCursor(apn_tbl, fields, where_clause) as csv_cursor:
                            for row in csv_cursor:
                                record_ids_current.append(row[1])
                        del csv_cursor

                        # If the apn of the current and the apn of the historic overlapping parcels
                        # are each only in one project, and if the project is the same project,
                        # then the dissolve that happens below will remove any double-counting
                        if (len(record_ids_current) == 1) and (len(record_ids_historic) == 1) and (record_ids_current[0] == record_ids_historic[0]):
                                print '      There is overlap between CURRENT parcel "{}" and HISTORIC parcel "{}"'.format(current_apn, historic_apn)
                                print '      But as both are from the same project: "{}", there will be no overlap when the data is dissolved'.format(record_ids_current[0])
                                print '      No need for human analysis, but PDS may want to know that they should update the historic apn in the above project'
                        else:
                            data_pass_QAQC_tests = False
                            print '      WARNING!  The overlap between CURRENT parcel "{}" and HISTORIC parcel "{}" may cause double counting'.format(current_apn, historic_apn)
                            print '      Please let PDS know that they should remove the historic parcel and add current parcel(s) in Accela for project {}'.format(record_ids_historic[0])

            del int_cursor


    #---------------------------------------------------------------------------
    # 4)  Check any critical fields to ensure there are no blank values
    print '\n  4) Finding any critical fields that are blank in imported CSV table:\n'
    critical_fields = [record_id_fld, apn_fld, gp_code_fld]
    for f in critical_fields:

        # Set the where clause
        if f == 'GPCODE95':  # Set a where clause for an integer field
            where_clause = "{0} IS NULL".format(f)
        else:  # Set a where clause for a string field
            where_clause = "{0} IS NULL or {0} = ''".format(f)

        # Get list of ids
        print '    Checking where: {}:'.format(where_clause)
        ids_w_nulls = []  # List to hold the ID of reports with null values
        with arcpy.da.SearchCursor(apn_tbl, critical_fields, where_clause) as cursor:
            for row in cursor:
                record_id = row[0]
                ids_w_nulls.append(record_id)
        del cursor

        # Get a sorted list of only unique values
        ids_w_nulls = sorted(set(ids_w_nulls))

        # Report on the sorted list
        if len(ids_w_nulls) != 0:
            data_pass_QAQC_tests = False
            print '      WARNING! There are records in the CSV extract that have a NULL value in column: "{}":'.format(f)
            for id_num in ids_w_nulls:
                if (id_num == None) or (id_num == ''):
                    print '        No Record ID available to report'
                else:
                    print '        {}'.format(id_num)
        if len(ids_w_nulls) == 0:
            print '      OK! No null values in {}'.format(f)

        print ''

    #---------------------------------------------------------------------------
    # 5) Confirm that all GP codes are valid using the general plan dictionary
    #    defined at the beginning of this script (gen_plan_dict)
    print '\n  5) Finding any invalid values in the GP Code field:'
    fields = [gp_code_fld]
    invalid_gp_codes = []
    any_gp_22_cd = False  # flag to control if there are any GP 22 codes
    with arcpy.da.SearchCursor(apn_tbl, fields) as cursor:
        for row in cursor:
            gp_code = row[0]

            # See if the code exists in the dictionary and see if the code = 22 (which has an unknown density)
            try:
                gen_plan_dict[gp_code]

                if gp_code == 22:
                    data_pass_QAQC_tests = False
                    any_gp_22_cd = True

            # This except will catch if there is not a matching code in the dict
            except KeyError:
                data_pass_QAQC_tests = False
                if gp_code not in invalid_gp_codes:
                    invalid_gp_codes.append(gp_code)  # Get a unique list of invalid codes
    del cursor

    # Report on any invalid GP codes
    if len(invalid_gp_codes) == 0:
        print '    OK!  There were no invalid GP codes.'

    else:
        print '    WARNING! There is at least one GP Code that is is not valid,'
        print '      The parcel with this code will be deleted later in the script.'

        # Loop through each invalid code and print out the projects that have that code in them
        for invalid_cd in invalid_gp_codes:
            print '\n    Invalid Code: {}'.format(invalid_cd)
            print '    Is found in Record ID:'

            # Make a cursor with where_clause equals [GPCODE95] = <an invalid code>
            invalid_record_ids = []
            fields = [record_id_fld, gp_code_fld]
            where_clause = "{} = {}".format(gp_code_fld, invalid_cd)
            with arcpy.da.SearchCursor(apn_tbl, fields, where_clause) as cursor:
                for row in cursor:
                    invalid_record_id = row[0]

                    # Get a unique list of invalid record ids
                    if invalid_record_id not in invalid_record_ids:
                        invalid_record_ids.append(invalid_record_id)
            del cursor

            # Print out the unique list of invalid record ids
            for invalid_id in invalid_record_ids:
                print '      {}'.format(invalid_id)

    # Report if there are any records with a GP code of 22
    if any_gp_22_cd == True:
        print '\n    WARNING!  There is a GP code in the extract that does not have'
        print '      a density value available.  Code: 22 (Specific Plan Area) is technically a valid GP code'
        print '      BUT, there is no Density information available for this code'
        print '      As a result, this script will give any parcel with this GP code'
        print '      a value of 0 in its density column.'


    #---------------------------------------------------------------------------
    print '\n  ----------------------------------------------------------------'
    print '  Data Passed all QA/QC tests = {}\n'.format(data_pass_QAQC_tests)

    print 'Finished QA_QC()'

    return data_pass_QAQC_tests


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
if __name__ == '__main__':
    main()
