#-------------------------------------------------------------------------------
# Purpose:
"""
To find the 'Date' that each maps data was last updated.

There are basically 3 different methods that this date can be found:
    1. SCRIPT Dependent:
       The date can be the last time that a SCRIPT was sucessfully run
       i.e. Map 12's date should be the date that the Map 12 script was last
       sucessfully run.  This information is kept in the SUCCESS/ERROR files
       that each script in this series creates
       (see 'success_error_folder' variable below for path)

    2. EXTRACT Dependent:
       The date can be the last time that an EXTRACT was created.
       i.e. Map 03's date should be the date that the extract for Map 03 was
       created (as long as the Map 03 script was successfully run).

       i.e. Map 08's date should be the earlier date of the two extracts that
       Map 08 needs to run (as long as all 3 Map 08 scripts were sucessfully run).


    3. MAP Dependent:
       The date can be the earliest date that other MAPS were updated.
       i.e. Map 06 uses processed data that was created by scripts for
       Map 02, 03, 04, 12.  Therefore Map 06 is as up-to-date as the dates
       we have already calculated in this script for Map 02, 03, 04, 12
"""
# Author:      mgrue
#
# Created:     21/08/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, os, datetime, ConfigParser, time, sys

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Update_LAST_DATA_UPDATE'


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
    root_folder               = config.get('Paths_Local',   'Root_Folder')
    folder_with_original_csvs = config.get('Paths_Local',   'Folder_With_Original_CSVs')
    edit_SDE_conn_File        = config.get('Edit_SDE_Info', 'Edit_SDE_Conn_File')
    edit_SDE_prefix           = config.get('Edit_SDE_Info', 'Edit_SDE_Prefix')

    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder     = '{}\{}'.format(root_folder, 'Data')

    wkg_fgdb        = '{}\{}'.format(data_folder, '{}.gdb'.format(shorthand_name))


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])

    # Paths to SDE Feature Classes
    LAST_DATA_UPDATE = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_LAST_DATA_UPDATE')


    # Paths to Original CSV Extracts (Not the formatted extracts since the modified date for the formatted extracts does not contain
    # The date that the extract was deposited from Accela to the Original Extract Folder
    extract_map_02   = os.path.join(folder_with_original_csvs, 'Approved General Plan Amendments (2011 General Plan Forward) (Map 2).csv')
    extract_map_03   = os.path.join(folder_with_original_csvs, 'Existing Dwelling Units (2011 General Plan Forward) (Map 3 & Map 11).csv')
    extract_map_04   = os.path.join(folder_with_original_csvs, 'Dwelling Units - Discretionary Approved (2011 GP Forward) (Map 4).csv')
    extract_map_05   = os.path.join(folder_with_original_csvs, 'Dwelling Units - Land Development Grading In-Process (Map 5).csv')
    extract_map_07   = os.path.join(folder_with_original_csvs, 'Dwelling Units - Discretionary In-Process (Map 7).csv')
    extract_map_08_A = os.path.join(folder_with_original_csvs, 'In-Process Applicant General Plan Amendments (Map 8).csv')
    extract_map_08_B = os.path.join(folder_with_original_csvs, 'In-Process County General Plan Amendments (Map 8).csv')
    extract_map_11   = os.path.join(folder_with_original_csvs, 'Existing Dwelling Units (2011 General Plan Forward) (Map 3 & Map 11).csv')


    # Paths to SUCCESS/ERROR Files
    success_run_map_02   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Approved_GPA_Map_02.txt')
    success_run_map_03   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Existing_DU_Map_03.txt')
    success_run_map_04   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Approved_DU_Map_04.txt')
    success_run_map_05   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Grading_In_Process_Map_05.txt')
    success_run_map_06   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Curnt_Dev_Potentl_Map_06.txt')
    success_run_map_07   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_In_Process_DU_Map_07.txt')
    success_run_map_08_A = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_In_Process_GPA_Map_08_A.txt')
    success_run_map_08_B = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_In_Process_GPA_Map_08_B.txt')
    success_run_map_08_C = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_In_Process_GPA_Map_08_C.txt')
    success_run_map_09   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_GP_Delta_Map_09.txt')
    success_run_map_10   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Future_Dev_Potentl_Map_10.txt')
    success_run_map_11   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Cmpltd_Bld_Permits_Map_11.txt')
    success_run_map_12   = os.path.join(success_error_folder, 'SUCCESS_running_DEV_TRACKER_Process_Annex_Aquitns_Map_12.txt')


    # Field Names in LAST_DATA_UPDATE Table
    id_field        = 'MAP'
    field_to_update = 'LAST_DATA_UPDATE'


    # Misc variables
    success           = True  # Flag for sucessful run of script
    all_dates_updated = True  # Flag for sucessfuly updating all dates


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
                print 'Creating FGDB at:\n  {}\n'.format(wkg_fgdb)
                arcpy.CreateFileGDB_management(out_folder_path, out_name)

        except Exception as e:
            success = False
            print '\n*** ERROR with Creating FGDBs ***'
            print str(e)


    #---------------------------------------------------------------------------
    #        Copy SDE Table to FGDB (so we can edit the working FGDB Table)
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # Copy the SDE Table to the wkg_fgdb
            table_name = 'LAST_DATA_UPDATE_FGDB_copy'
            last_data_update_copy = os.path.join(wkg_fgdb, table_name)

            print '\n----------------------------------------------------------'
            print 'Copying SDE Table:\n  From:\n    {}'.format(LAST_DATA_UPDATE)
            print '  To:\n    {}\{}'.format(wkg_fgdb, table_name)

            arcpy.TableToTable_conversion(LAST_DATA_UPDATE, wkg_fgdb, table_name)

        except Exception as e:
            success = False
            print '\n*** ERROR with Copying Table to FGDB ***'
            print str(e)


    #---------------------------------------------------------------------------
    #                        Start Updating the Dates
    #---------------------------------------------------------------------------
    if success == True:
        print('\n-------------------------------------------------------------')
        print('Updating Table at:\n  {}'.format(last_data_update_copy))


        #-----------------------------------------------------------------------
        #                              Update Map 02
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 02'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('EXTRACT Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_02):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_02))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified = Get_Date_From_File(extract_map_02)

                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 03
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 03'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('EXTRACT Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_03):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_03))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified = Get_Date_From_File(extract_map_03)

                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 04
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 04'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('EXTRACT Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_04):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_04))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified = Get_Date_From_File(extract_map_04)

                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 05
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 05'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('EXTRACT Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_05):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_05))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified = Get_Date_From_File(extract_map_05)

                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 12
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 12'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('SCRIPT Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_12):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_12))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                # Get the date of the last SUCESSFULLY run of Map 12
                print('\n  Get the date of the SUCCESS file:')
                date_file_modified = Get_Date_From_File(success_run_map_12)

                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 06
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 06'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('MAP Dependent method')


            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_06):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_06))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                #                        Get info for Map 02

                # Get the date of the extract
                print('\n  Get the date of Map 02:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 02'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_02_date = row[1]
                del cursor

                print '    {}'.format(map_02_date)

                # Get a datetime object from the string
                dt_obj_map_02 = datetime.datetime.strptime(map_02_date, '%m/%d/%Y')


                #                        Get info for Map 03

                # Get the date of the extract
                print('\n  Get the date of Map 03:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 03'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_03_date = row[1]
                del cursor

                print '    {}'.format(map_03_date)

                # Get a datetime object from the string
                dt_obj_map_03 = datetime.datetime.strptime(map_03_date, '%m/%d/%Y')


                #                        Get info for Map 04

                # Get the date of the extract
                print('\n  Get the date of Map 04:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 04'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_04_date = row[1]
                del cursor

                print '    {}'.format(map_04_date)

                # Get a datetime object from the string
                dt_obj_map_04 = datetime.datetime.strptime(map_04_date, '%m/%d/%Y')


                #                        Get info for Map 12

                # Get the date of the extract
                print('\n  Get the date of Map 12:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 12'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_12_date = row[1]
                del cursor

                print '    {}'.format(map_12_date)

                # Get a datetime object from the string
                dt_obj_map_12 = datetime.datetime.strptime(map_12_date, '%m/%d/%Y')



                #              Decide which date to use (From Map 2, 3, 4, 12)

                # Get all the dt_obj into one list and sort the list (the first dt_obj is the one we want to use)
                dt_objects = []

                dt_objects.append(dt_obj_map_02)
                dt_objects.append(dt_obj_map_03)
                dt_objects.append(dt_obj_map_04)
                dt_objects.append(dt_obj_map_12)

                dt_objects.sort()

                map_date_to_use = (dt_objects[0]).strftime('%m/%d/%Y')


                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, map_date_to_use, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 07
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 07'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('EXTRACT Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_07):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_07))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified = Get_Date_From_File(extract_map_07)

                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 08
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 08'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('EXTRACT Dependent method')


            #       Confirm that all scripts Map 08 uses ran successfully

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_08_A):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_08_A))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            # Test to see if the SUCCESS file exists
            elif not os.path.exists(success_run_map_08_B):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_08_B))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            # Test to see if the SUCCESS file exists
            elif not os.path.exists(success_run_map_08_C):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_08_C))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')


            else:
                #                        Get info for Extract A

                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified_A = Get_Date_From_File(extract_map_08_A)

                # Get a datetime object from the string
                dt_obj_A = datetime.datetime.strptime(date_file_modified_A, '%m/%d/%Y')


                #                        Get into for Extract B

                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified_B = Get_Date_From_File(extract_map_08_B)

                # Get a datetime object from the string
                dt_obj_B = datetime.datetime.strptime(date_file_modified_B, '%m/%d/%Y')


                #                  Decide which date to use (from A or B)

                if dt_obj_A > dt_obj_B:  # Then B is the 'older' file and should be used
                    date_file_modified = date_file_modified_B

                else:  # Then A is either 'older' or the same date and should be used
                    date_file_modified = date_file_modified_A


                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 09
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 09'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('MAP Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_09):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_09))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                #                        Get info for Map 04

                # Get the date of the extract
                print('\n  Get the date of Map 04:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 04'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_04_date = row[1]
                del cursor

                print '    {}'.format(map_04_date)

                # Get a datetime object from the string
                dt_obj_map_04 = datetime.datetime.strptime(map_04_date, '%m/%d/%Y')


                #                        Get info for Map 07

                # Get the date of the extract
                print('\n  Get the date of Map 07:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 07'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_07_date = row[1]
                del cursor

                print '    {}'.format(map_07_date)

                # Get a datetime object from the string
                dt_obj_map_07 = datetime.datetime.strptime(map_07_date, '%m/%d/%Y')


                #              Decide which date to use (from 04 or 07)

                if dt_obj_map_04 > dt_obj_map_07:  # Then 07 is the 'older' file and should be used
                    map_date_to_use = map_07_date

                else:  # Then A is either 'older' or the same date and should be used
                    map_date_to_use = map_04_date


                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, map_date_to_use, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 10
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 10'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('MAP Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_10):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_10))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                #                        Get info for Map 06

                # Get the date of the extract
                print('\n  Get the date of Map 06:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 06'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_06_date = row[1]
                del cursor

                print '    {}'.format(map_06_date)

                # Get a datetime object from the string
                dt_obj_map_06 = datetime.datetime.strptime(map_06_date, '%m/%d/%Y')


                #                        Get info for Map 07

                # Get the date of the extract
                print('\n  Get the date of Map 07:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 07'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_07_date = row[1]
                del cursor

                print '    {}'.format(map_07_date)

                # Get a datetime object from the string
                dt_obj_map_07 = datetime.datetime.strptime(map_07_date, '%m/%d/%Y')


                #                        Get info for Map 08

                # Get the date of the extract
                print('\n  Get the date of Map 08:')
                fields = [id_field, field_to_update]
                where_clause = "{} = 'Map 08'".format(id_field)
                with arcpy.da.SearchCursor(last_data_update_copy, fields, where_clause) as cursor:
                    row = next(cursor)
                    map_08_date = row[1]
                del cursor

                print '    {}'.format(map_08_date)

                # Get a datetime object from the string
                dt_obj_map_08 = datetime.datetime.strptime(map_08_date, '%m/%d/%Y')


                #              Decide which date to use (From Map 6, 7, 8)

                # Get all the dt_obj into one list and sort the list (the first dt_obj is the one we want to use)
                dt_objects = []

                dt_objects.append(dt_obj_map_06)
                dt_objects.append(dt_obj_map_07)
                dt_objects.append(dt_obj_map_08)

                dt_objects.sort()

                map_date_to_use = (dt_objects[0]).strftime('%m/%d/%Y')


                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, map_date_to_use, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


        #-----------------------------------------------------------------------
        #                              Update Map 11
        #-----------------------------------------------------------------------
        try:
            print('\n\n-------------------------------------------------------')
            map_to_update = 'Map 11'
            print 'Update [{}] for: {}'.format(field_to_update, map_to_update)
            print('EXTRACT Dependent method')

            # Test to see if the SUCCESS file exists
            if not os.path.exists(success_run_map_11):
                all_dates_updated = False
                print('*** WARNING! ***')
                print('  The SUCCESS file does not exist at:\n    {}'.format(success_run_map_11))
                print('  This means the date should not be updated for this map')
                print('  Please investigate if the script that should have created the SUCCESS file failed')

            else:
                # Get the date of the extract
                print('\n  Get the date of the extract:')
                date_file_modified = Get_Date_From_File(extract_map_11)

                # Update
                print('\n  Set date into Table:')
                where_clause = "{} = '{}'".format(id_field, map_to_update)
                Update_Cursor(last_data_update_copy, id_field, field_to_update, date_file_modified, where_clause)

        except Exception as e:
            success = False
            print '\n*** ERROR with Updating Date for {} ***'.format(map_to_update)
            print str(e)


    #---------------------------------------------------------------------------
    #         Delete the prod data and append the working data to prod
    if success == True:
        try:
            print('\n\n-------------------------------------------------------')
            print('-------------------------------------------------------')
            print 'Get working data to prod:'

            print '\n  Deleting features at:\n    {}'.format(LAST_DATA_UPDATE)
            arcpy.DeleteRows_management(LAST_DATA_UPDATE)

            print '\n  Append features from:\n    {}\n  To:\n    {}'.format(last_data_update_copy, LAST_DATA_UPDATE)
            arcpy.Append_management(last_data_update_copy, LAST_DATA_UPDATE)

        except Exception as e:
            success = False
            print '\n*** ERROR with getting working data into prod'
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
    print('All Dates were updated  = {}'.format(all_dates_updated))
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
#                           FUNCTION Get_Date_From_File
def Get_Date_From_File(path_to_file):
    """
    PARAMETERS:
      path_to_file (str): Full path to a file

    FUNCTION:
      Get the date that a file was last modified

    RETURN:
      formatted_dt_obj (str): String representation of the date that a file
        was last modified
    """

    ##print 'Starting Get_Date_From_File()'

    # Set the format you want the date to be returned as a string
    # https://www.tutorialspoint.com/python/time_strftime.htm
    str_format = '%m/%d/%Y'


    # Get the timestamp that the file was last modified
    timestamp = os.path.getmtime(path_to_file)


    # Get that timestamp as a datetime object
    dt_obj = datetime.datetime.fromtimestamp(timestamp)


    # Format the datetime object into a specific format
    formatted_dt_obj = dt_obj.strftime(str_format)

    print '    File:\n      {}\n    Was last modified on:\n      {}'.format(path_to_file, formatted_dt_obj)

    ##print 'Finished Get_Date_From_File()'
    return formatted_dt_obj


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Update_Cursor(obj_to_update, id_field, field_to_update, value_to_update, where_clause):
    """
    To update a FC or Table using the id_field and the where_clause to get the row(s) to update
    and then updating the field_to_update with the value in value_to_update
    """

    print('    Updating:  [{}]\n    Where:  "{}"'.format(field_to_update, where_clause))
    print('    With value:  {}\n'.format(value_to_update))

    # Create cursor to loop through all rows that satisfy the where_clause
    fields = [id_field, field_to_update]
    with arcpy.da.UpdateCursor(obj_to_update, fields, where_clause) as cursor:
        for row in cursor:
            print '    Updating: {}'.format(row[0])
            print '    Current Value: {}'.format(row[1])

            row[1] = value_to_update # Set the value into the field_to_update

            cursor.updateRow(row) # Update the row

            print '    Updated Value: {}'.format(row[1])

    del cursor
    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
