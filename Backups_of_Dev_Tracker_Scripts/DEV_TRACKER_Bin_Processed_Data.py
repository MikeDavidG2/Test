#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      mgrue
#
# Created:     24/07/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy, os, math, ConfigParser, time, sys
arcpy.env.overwriteOutput = True

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Name of this script
    name_of_script = 'DEV_TRACKER_Bin_Processed_Data.py'


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

    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder     = '{}\{}'.format(root_folder, 'Data')

    wkg_fgdb        = '{}\{}'.format(data_folder, 'Bin_Processed_Data.gdb')


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Paths to SDE Feature Classes
    BINNING_CONTROL_TABLE      = os.path.join(edit_SDE_conn_File, edit_SDE_prefix + 'PDS_DEV_TRACKER_BINNING_CONTROL_TABLE')
    GRID_HEX_060_ACRES = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + 'GRID_HEX_060_ACRES')
    CMTY_PLAN_CN_2011       = os.path.join(prod_SDE_conn_file, prod_SDE_prefix + 'CMTY_PLAN_CN_2011')


    # Set Field names
    density_fld    = 'DENSITY'
    unit_count_fld = 'UNIT_COUNT'


    # Misc variables
    success = True


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
    #                 Bin / CPASG all FC's in BINNING_CONTROL_TABLE
    #                   And deliver to correct FC in Edit SDE
    #---------------------------------------------------------------------------
    if success == True:
        try:
            #-------------------------------------------------------------------
            #                 Get Variables for each FC to Bin
            #-------------------------------------------------------------------
            print '------------------------------------------------------------'
            print '------------------------------------------------------------'
            print 'Get Variables for each FC to Bin from BINNING_CONTROL_TABLE at:\n  {}'.format(BINNING_CONTROL_TABLE)
            fields = ['PROCESS', 'PATH_TO_FC_TO_PROCESS', 'SHORTHAND_NAME', 'PROD_BINNED_FC', 'PROD_CPASG_TBL']
            with arcpy.da.SearchCursor(BINNING_CONTROL_TABLE, fields) as cursor:
                for row in cursor:
                    process        = (row[0]).capitalize()  # Make sure the value is capitalized for test later
                    fc_to_process  = row[1]
                    shorthand_name = row[2]
                    prod_binned_fc = row[3]
                    prod_cpasg_tbl = row[4]


                    print '\n\n------------------------------------------------'
                    print '------------------------------------------------'
                    print 'Processing: "{}"'.format(os.path.basename(fc_to_process))
                    print '\nPath to FC to Bin:\n  {}'.format(fc_to_process)

                    if not arcpy.Exists(fc_to_process):
                        success = False
                        print '\nERROR! That FC does not exist\n'

                    elif process != 'Yes':
                        print('\nINFO.  Not processing FC because the BINNING_CONTROL_TABLE has [PROCESS] = "{}".'.format(process))
                        print('  Change this FCs value to "Yes" to process this FC')

                    else:
                        # Find if the fc_to_process is a 'Polygon' or a 'Point'
                        desc = arcpy.Describe(fc_to_process)
                        shape_type = desc.shapeType
                        print '\nShape type = "{}"\n'.format(shape_type)


                        #-------------------------------------------------------
                        #-------------------------------------------------------
                        #                       Process if Polygon
                        #-------------------------------------------------------
                        # If it is a 'Polygon' make sure that it has the density_fld field
                        if shape_type == 'Polygon':
                            print 'Confirming Polygon has field: [{}]'.format(density_fld)

                            field_names = [f.name for f in arcpy.ListFields(fc_to_process)]

                            if density_fld in field_names:
                                valid_polygon = True
                                print '  OK! Polygon has required field\n'
                            else:
                                valid_polygon = False
                                success = False
                                print '  ERROR!  This FC is a "{}", but it does not have the field: "{}'.format(shape_type, density_fld)
                                print '  It cannot--therefore--be processed\n'


                            #---------------------------------------------------
                            # Process valid Polygons
                            if valid_polygon == True:
                                #-----------------------------------------------
                                #                Bin Polygons with a Density Field
                                #-----------------------------------------------
                                if prod_binned_fc.upper() == 'N/A':  # Don't try to bin if there is "N/A" in the BINNING_CONTROL_TABLE
                                    print 'INFO. Not Binning this FC because the value in the BINNING_CONTROL_TABLE is "N/A"'

                                else:
                                    try:
                                        Bin_Polys_w_Density(wkg_fgdb, fc_to_process, prod_binned_fc, GRID_HEX_060_ACRES, shorthand_name, density_fld)
                                        pass

                                    except Exception as e:
                                        success = False
                                        print '\n*** ERROR with Bin_Polys_w_Density() ***'
                                        print str(e)


                                #-----------------------------------------------
                                #       Create CPASG table for Polygons with a Density Field
                                #-----------------------------------------------
                                if prod_cpasg_tbl.upper() == 'N/A':  # Don't try to bin if there is "N/A" in the BINNING_CONTROL_TABLE
                                    print 'INFO. Not CPASGing this FC because the value in the BINNING_CONTROL_TABLE is "N/A"'

                                else:
                                    try:
                                        CPASG_Polys_w_Density(wkg_fgdb, fc_to_process, prod_cpasg_tbl, CMTY_PLAN_CN_2011, shorthand_name, density_fld)

                                    except Exception as e:
                                        success = False
                                        print '\n*** ERROR with CPASG_Polys_w_Density() ***'
                                        print str(e)


                        #-------------------------------------------------------
                        #-------------------------------------------------------
                        #                        Process if Point
                        #-------------------------------------------------------
                        # If it is a 'Point' make sure that it has the unit_count_fld field
                        if shape_type == 'Point':
                            print 'Confirming Point has field: [{}]'.format(unit_count_fld)

                            field_names = [f.name for f in arcpy.ListFields(fc_to_process)]

                            if unit_count_fld in field_names:
                                valid_point = True
                                print '  OK! Point has required field\n'
                            else:
                                valid_point = False
                                success = False
                                print '  ERROR!  This FC is a "{}", but it does not have the field: "{}"'.format(shape_type, unit_count_fld)
                                print '  It cannot--therefore--be processed\n'


                            #---------------------------------------------------
                            # Process valid Points
                            if valid_point == True:
                                #-----------------------------------------------
                                #                Bin Points with a Unit Count Field
                                #-----------------------------------------------
                                if prod_binned_fc.upper() == 'N/A':  # Don't try to bin if there is "N/A" in the BINNING_CONTROL_TABLE
                                    print 'INFO. Not Binning this FC because the value in the BINNING_CONTROL_TABLE is "N/A"'

                                else:
                                    try:
                                        Bin_Points_w_UnitCount(wkg_fgdb, fc_to_process, prod_binned_fc, GRID_HEX_060_ACRES, shorthand_name, unit_count_fld)

                                    except Exception as e:
                                        success = False
                                        print '\n*** ERROR with Bin_Points_w_UnitCount() ***'
                                        print str(e)


                                #-----------------------------------------------
                                #    Create CPASG table for Points with a Unit Count Field
                                #-----------------------------------------------
                                if prod_cpasg_tbl.upper() == 'N/A':  # Don't try to bin if there is "N/A" in the BINNING_CONTROL_TABLE
                                    print 'INFO. Not CPASGing this FC because the value in the BINNING_CONTROL_TABLE is "N/A"'

                                else:
                                    try:
                                        CPASG_Points_w_UnitCount(wkg_fgdb, fc_to_process, prod_cpasg_tbl, CMTY_PLAN_CN_2011, shorthand_name, unit_count_fld)

                                    except Exception as e:
                                        success = False
                                        print '\n*** ERROR with CPASG_Points_w_UnitCount() ***'
                                        print str(e)


        except Exception as e:
            success = False
            print '\n*** ERROR in main() ***'
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
def Bin_Polys_w_Density(wkg_fgdb, fc_to_bin, prod_binned_fc, GRID_HEX_060_ACRES, shorthand_name, density_fld):
    """
    To take unique single-part (not multipart) polygons with a density field
    and to create a Hexbin FC with a VALUE field
    """

    print '\n------------------------------------------------------------------'
    print 'Starting Bin_Polys_w_Density()'

    # Set variables
    hex_id_fld       = 'HEXAGONID'
    row_acres_fld    = 'Row_Acres'
    value_temp_fld   = 'VALUE_Temp'
    value_final_fld  = 'VALUE_{}'.format(shorthand_name)
    expression_type  = 'PYTHON_9.3'


    print '\n  Binning processed data found at:\n    {}\n'.format(fc_to_bin)

    #---------------------------------------------------------------------------
    #                 Intersect FC to bin with Hexbin FC

    in_features = [fc_to_bin, GRID_HEX_060_ACRES]
    intersect_fc = os.path.join(wkg_fgdb, '{}_Hex_int'.format(shorthand_name))
    print '\n  Intersecting:'
    for fc in in_features:
        print '    {}'.format(fc)
    print '  To create FC:\n    {}\n\n'.format(intersect_fc)
    arcpy.Intersect_analysis(in_features, intersect_fc)


    #---------------------------------------------------------------------------
    #                    Clean up the intersected data

    print '  Clean up the intersected data before performing area calculations:\n'

    # Repair the geometry
    print '    Repairing geometry at:\n      {}\n'.format(intersect_fc)
    arcpy.RepairGeometry_management(intersect_fc)

    # Explode multipart to singlepart
    int_single_part_fc = '{}_expld'.format(intersect_fc)
    print '    Exploding multipart to single part from:\n      {}\n    To:\n      {}\n'.format(intersect_fc, int_single_part_fc)
    arcpy.MultipartToSinglepart_management(intersect_fc, int_single_part_fc)

    # Repair the geometry
    print '    Repairing geometry at:\n      {}\n'.format(int_single_part_fc)
    arcpy.RepairGeometry_management(int_single_part_fc)


    #---------------------------------------------------------------------------
    #              Add Acreage field and calc each rows acreage

    print '\n  Add and calculate fields to FC:\n    {}'.format(int_single_part_fc)

    # Add field to hold Acreage
    print '\n    Adding field:'
    field_name = row_acres_fld
    field_type = 'DOUBLE'
    print '      [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(int_single_part_fc, field_name, field_type)

    # Calculate acres for each row
    expression      = '!shape.area@acres!'
    print '\n    Calculating field:\n      {} = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management(int_single_part_fc, field_name, expression, expression_type)


    #---------------------------------------------------------------------------
    #         Add VALUE field and calc = to Density * Acreage

    # Add field to hold VALUE temporarily
    print '\n    Adding field:'
    field_name = value_temp_fld
    field_type = 'DOUBLE'
    print '      [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(int_single_part_fc, field_name, field_type)

    # Calculate VALUE for each row
    expression      = '!{}!*!{}!'.format(density_fld, row_acres_fld)
    print '\n    Calculating field:\n      {} = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management(int_single_part_fc, field_name, expression, expression_type)


    #---------------------------------------------------------------------------
    #       Perform Frequency on Hexagon ID, while summing the VALUE field

    freq_analysis_tbl = '{}_freq'.format(int_single_part_fc)
    freq_fields = [hex_id_fld]
    sum_fields  = [value_temp_fld]

    print '\n  Performing Frequency Analysis on FC:\n    {}'.format(int_single_part_fc)
    print '  Frequency Fields:'
    for f in freq_fields:
        print '    {}'.format(f)
    print '  Sum fields:'
    for f in sum_fields:
        print '    {}'.format(f)
    print '  To create FC at:\n    {}'.format(freq_analysis_tbl)
    arcpy.Frequency_analysis(int_single_part_fc, freq_analysis_tbl, freq_fields, sum_fields)


    #---------------------------------------------------------------------------
    #             Copy the SDE Hexagon grid to a local FGDB

    # Set the path to copy the SDE Hexagon grid to
    FINAL_hex_fc = '{}_BINNED'.format(freq_analysis_tbl)

    # Get the parameters the copy tool needs and copy
    out_path, out_name = os.path.split(FINAL_hex_fc)
    print '\n  Copying FC:\n    {}\n  To:\n    {}\{}'.format(GRID_HEX_060_ACRES, out_path, out_name)
    arcpy.FeatureClassToFeatureClass_conversion(GRID_HEX_060_ACRES, out_path, out_name)


    #---------------------------------------------------------------------------
    # Add VALUE field to newly copied SDE Hexagon grid and calc it to equal the
    # summed VALUE field by joining the copied Hexagon grid to the intersected data

    # Add field to hold VALUE
    print '\n  Adding field:'
    field_name = value_final_fld
    field_type = 'DOUBLE'
    print '    [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(FINAL_hex_fc, field_name, field_type)


    # Join the copied Hex FC with the Frequency Table
    join_lyr = Join_2_Objects_By_Attr(FINAL_hex_fc, hex_id_fld, freq_analysis_tbl, hex_id_fld, 'KEEP_ALL')


    # Calculate the VALUE field in the Hex FC from the Frequency Table
    table_name      = os.path.basename(freq_analysis_tbl)
    expression      = '!{}.{}!'.format(table_name, value_temp_fld)
    print '\n  Calculating field:\n    {} = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management(join_lyr, value_final_fld, expression, expression_type)
    arcpy.Delete_management(join_lyr)  # Need to delete this join so it does not conflict with other joins

    #---------------------------------------------------------------------------
    #             Calc any <Null> values in VALUE field to 0

    print '\n  Calculating any <Null> values in VALUE field to 0:'

    # Make a layer that only has <Null> values in the VALUE field
    where_clause = "{} IS NULL".format(value_final_fld)
    arcpy.MakeFeatureLayer_management(FINAL_hex_fc, 'null_values', where_clause)

    # Calculate the layer
    field_name = value_final_fld
    expression = '0'
    print '    Calculating field:\n      [{}] = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management('null_values', field_name, expression, expression_type)
    arcpy.Delete_management('null_values')

    #---------------------------------------------------------------------------
    #         Delete the prod data and append the working data to prod

    print '\n  Get working data to prod:'

    print '\n    Deleting features at:\n      {}'.format(prod_binned_fc)
    arcpy.DeleteFeatures_management(prod_binned_fc)

    print '\n    Append features from:\n      {}\n    To:\n      {}'.format(FINAL_hex_fc, prod_binned_fc)
    arcpy.Append_management(FINAL_hex_fc, prod_binned_fc)


    #---------------------------------------------------------------------------
    print '\nFinished Bin_Polys_w_Density()'
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def CPASG_Polys_w_Density(wkg_fgdb, fc_to_make_cpasg_tbl, prod_cpasg_tbl, CMTY_PLAN_CN_2011, shorthand_name, density_fld):
    """
    To take unique single-part (not multipart) polygons with a density field
    and to create a CPASG table with a VALUE field
    """

    print '\n------------------------------------------------------------------'
    print 'Starting CPASG_Polys_w_Density()'

    # Set variables
    cpasg_label_exist_fld = 'CPASG_LABEL'  # The name of the existing field in CMTY_PLAN_CN_2011
    cpasg_label_new_fld   = 'CPASG_NAME'  # The new field name to give the CPASG_LABEL
    cpasg_fld             = 'CPASG'
    row_acres_fld         = 'Row_Acres'
    value_final_fld       = 'VALUE_{}'.format(shorthand_name)
    expression_type       = 'PYTHON_9.3'


    print '\n  Creating CPASG table from processed data found at:\n    {}\n'.format(fc_to_make_cpasg_tbl)

    #---------------------------------------------------------------------------
    #                 Union 'FC to make CPASG table' with CMTY_PLAN_CN_2011

    in_features = [fc_to_make_cpasg_tbl, CMTY_PLAN_CN_2011]
    union_fc = os.path.join(wkg_fgdb, '{}_CPASG_union'.format(shorthand_name))
    print '\n  Unioning:'
    for fc in in_features:
        print '    {}'.format(fc)
    print '  To create FC:\n    {}\n\n'.format(union_fc)
    arcpy.Union_analysis(in_features, union_fc)


    #---------------------------------------------------------------------------
    #                    Clean up the unioned data

    print '\n  Clean up the unioned data before performing area calculations:\n'

    # Repair the geometry
    print '    Repairing geometry at:\n      {}\n'.format(union_fc)
    arcpy.RepairGeometry_management(union_fc)

    # Explode multipart to singlepart
    union_single_part_fc = '{}_expld'.format(union_fc)
    print '    Exploding multipart to single part from:\n      {}\n    To:\n      {}\n'.format(union_fc, union_single_part_fc)
    arcpy.MultipartToSinglepart_management(union_fc, union_single_part_fc)

    # Repair the geometry
    print '    Repairing geometry at:\n      {}\n'.format(union_single_part_fc)
    arcpy.RepairGeometry_management(union_single_part_fc)


    #---------------------------------------------------------------------------
    #              Add Acreage field and calc each rows acreage

    print '\n  Add and calculate fields to FC:\n    {}'.format(union_single_part_fc)

    # Add field to hold Acreage
    print '\n    Adding field:'
    field_name = row_acres_fld
    field_type = 'DOUBLE'
    print '      [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(union_single_part_fc, field_name, field_type)

    # Calculate acres for each row
    expression      = '!shape.area@acres!'
    print '\n    Calculating field:\n      [{}] = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management(union_single_part_fc, field_name, expression, expression_type)


    #---------------------------------------------------------------------------
    #         Add VALUE field and calc = to Density * Acreage

    # Add field to hold VALUE
    print '\n    Adding field:'
    field_name = value_final_fld
    field_type = 'DOUBLE'
    print '      [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(union_single_part_fc, field_name, field_type)

    # Calculate VALUE for each row
    expression      = '!{}!*!{}!'.format(density_fld, row_acres_fld)
    print '\n    Calculating field:\n      [{}] = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management(union_single_part_fc, field_name, expression, expression_type)


    #---------------------------------------------------------------------------
    #       Perform Frequency on CPASG_LABEL & CPASG, while summing the VALUE field

    freq_analysis_tbl = '{}_freq_CPASG_FINAL'.format(union_single_part_fc)
    freq_fields = [cpasg_label_exist_fld, cpasg_fld]
    sum_fields  = [value_final_fld]

    print '\n  Performing Frequency Analysis on FC:\n    {}'.format(union_single_part_fc)
    print '  Frequency Fields:'
    for f in freq_fields:
        print '    {}'.format(f)
    print '  Sum fields:'
    for f in sum_fields:
        print '    {}'.format(f)
    print '  To create FC at:\n    {}'.format(freq_analysis_tbl)
    arcpy.Frequency_analysis(union_single_part_fc, freq_analysis_tbl, freq_fields, sum_fields)


    #---------------------------------------------------------------------------
    #                    Clean up the Frequency Analysis Table

    print '\n  Cleaning up the Frequency Analysis Table:'

    # Delete the [FREQUENCY] field created by the Frequency Analysis (for clarity)
    print '\n    Delete the field: [FREQUENCY] created by the Frequency Analysis b/c it is not needed'
    arcpy.DeleteField_management(freq_analysis_tbl, 'FREQUENCY')


    # Change the field name [CPASG_LABEL] to [CPASG_NAME] (for clarity)
    existing_field_name = cpasg_label_exist_fld
    new_field_name      = cpasg_label_new_fld
    print '\n    Changing field name from: [{}] to: [{}] for FC:\n      {}'.format(existing_field_name, new_field_name, freq_analysis_tbl)
    arcpy.AlterField_management(freq_analysis_tbl, existing_field_name, new_field_name)


    # Delete rows that don't have a value for the CPASG Name
    fields = [cpasg_label_new_fld]
    where_clause = "{0} = '' or {0} IS NULL".format(cpasg_label_new_fld)
    print '\n    Deleting any rows in Frequency Analysis table where: "{}"\n'.format(where_clause)
    with arcpy.da.UpdateCursor(freq_analysis_tbl, fields, where_clause) as cursor:
        for row in cursor:
            cursor.deleteRow()
    del cursor


    #---------------------------------------------------------------------------
    #                 Create a row to hold 'Countywide' and
    #                calc it as a sum of the VALUE field

    print '\n  Adding "Countywide" feature in Table:\n    {}'.format(freq_analysis_tbl)

    # Find the sum of the VALUE field
    # (to input for the 'Countywide' feature created below)
    print '\n    Finding sum of field [{}]:'.format(value_final_fld)
    sum_of_quantity = 0
    with arcpy.da.SearchCursor(freq_analysis_tbl, [value_final_fld]) as cursor:
        for row in cursor:
            sum_of_quantity = sum_of_quantity + row[0]
    del cursor
    print '      {}'.format(sum_of_quantity)

    # Add the 'Countywide' feature and calc the quantity to equal the sum of all quantities
    print '\n    Adding feature "Countywide"\n'
    fields = [cpasg_label_new_fld, cpasg_fld, value_final_fld]
    with arcpy.da.InsertCursor(freq_analysis_tbl, fields) as cursor:
        cursor.insertRow(('Countywide', 190000, sum_of_quantity))
    del cursor


    #---------------------------------------------------------------------------
    #                     Round the value field
    """
    We are rounding here in order to get a whole number (1.49 = 1 while 1.5 = 2)
    We are no longer truncating because a value of 0.999999999 gets truncated
    to 0 when it should clearly be 1.
    """

    # Round the VALUE field
    field_name = value_final_fld
    expression = 'round(!{}!)'.format(value_final_fld)
    print '\n  Rounding field:\n    [{}] = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management(freq_analysis_tbl, field_name, expression, expression_type)


    #---------------------------------------------------------------------------
    #         Delete the prod data and append the working data to prod

    print '\n  Get working data to prod:'

    print '\n    Deleting rows at:\n      {}'.format(prod_cpasg_tbl)
    arcpy.DeleteRows_management(prod_cpasg_tbl)

    print '\n    Append rows from:\n      {}\n    To:\n      {}'.format(freq_analysis_tbl, prod_cpasg_tbl)
    arcpy.Append_management(freq_analysis_tbl, prod_cpasg_tbl)


    print '\nFinished CPASG_Polys_w_Density()'
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Bin_Points_w_UnitCount(wkg_fgdb, fc_to_bin, prod_binned_fc, GRID_HEX_060_ACRES, shorthand_name, unit_count_fld):
    """
    """
    print '\nStarting Bin_Points_w_UnitCount():\n'

    # Set variables
    hex_id_fld       = 'HEXAGONID'
    value_final_fld  = 'VALUE_{}'.format(shorthand_name)
    expression_type  = 'PYTHON_9.3'

    print '\n  Creating Hexbin FC from processed data found at:\n    {}\n'.format(fc_to_bin)

    #---------------------------------------------------------------------------
    #                              Spatial Join

    # Spatial Join Points with GRID_HEX_060_ACRES
    points_GRID_HEX_join = os.path.join(wkg_fgdb, '{}_HEX_join'.format(shorthand_name))
    print '  Spatially Joining:\n    {}\n  And:\n    {}\n  To create Feature Class:\n    {}\n'.format(fc_to_bin, GRID_HEX_060_ACRES, points_GRID_HEX_join)
    arcpy.SpatialJoin_analysis(fc_to_bin, GRID_HEX_060_ACRES, points_GRID_HEX_join)


    #---------------------------------------------------------------------------
    #                            Frequency Analysis

    # Get the frequency of how many points (using the unit count field) are in each HEXBIN
    freq_analysis_tbl = points_GRID_HEX_join + '_freq'
    frequency_fields = [hex_id_fld]
    summary_fields = [unit_count_fld]
    print '  Performing Frequency analysis on FC:\n    {}\n  To create Table:\n    {}'.format(points_GRID_HEX_join, freq_analysis_tbl)
    print '  Frequency Fields:'
    for freq_field in frequency_fields:
        print '    {}'.format(freq_field)
    print '  Summary Fields:'
    for summary_field in summary_fields:
        print '    {}'.format(summary_field)
    arcpy.Frequency_analysis(points_GRID_HEX_join, freq_analysis_tbl, frequency_fields, summary_fields)


    #---------------------------------------------------------------------------
    #             Copy the SDE Hexagon grid to a local FGDB

    # Set the path to copy the SDE Hexagon grid to
    # TODO: Get below string more 'flexible' so that I don't have to use shorthand_name
    FINAL_hex_fc = os.path.join(wkg_fgdb, '{}_HEX_join_freq_BINNED'.format(shorthand_name))

    # Get the parameters the copy tool needs and copy
    out_path, out_name = os.path.split(FINAL_hex_fc)
    print '\n  Copying FC:\n    {}\n  To:\n    {}\{}\n'.format(GRID_HEX_060_ACRES, out_path, out_name)
    arcpy.FeatureClassToFeatureClass_conversion(GRID_HEX_060_ACRES, out_path, out_name)


    #---------------------------------------------------------------------------
    # Add VALUE field to newly copied SDE Hexagon grid and calc it to equal the
    # summed VALUE field by joining the copied Hexagon grid to the intersected data

    print '  Add field to copied Hex FC, and calculate it from the Frequency analysis FC'

    # Add field to hold VALUE
    print '    Adding field:'
    field_name = value_final_fld
    field_type = 'DOUBLE'
    print '      [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(FINAL_hex_fc, field_name, field_type)


    # Join the copied Hex FC with the Frequency Table
    join_lyr = Join_2_Objects_By_Attr(FINAL_hex_fc, hex_id_fld, freq_analysis_tbl, hex_id_fld, 'KEEP_ALL')


    # Calculate the VALUE field in the Hex FC from the Frequency Table
    table_name      = os.path.basename(freq_analysis_tbl)
    expression      = '!{}.{}!'.format(table_name, unit_count_fld)
    print '\n    Calculating field:\n      [{}] = {}'.format(field_name, expression)
    arcpy.CalculateField_management(join_lyr, value_final_fld, expression, expression_type)
    arcpy.Delete_management(join_lyr)  # Need to delete this join so it does not conflict with other joins

    #---------------------------------------------------------------------------
    #             Calc any <Null> values in VALUE field to 0

    print '\n  Calculating any <Null> values in VALUE field to 0:'

    # Make a layer that only has <Null> values in the VALUE field
    where_clause = "{} IS NULL".format(value_final_fld)
    arcpy.MakeFeatureLayer_management(FINAL_hex_fc, 'null_values', where_clause)

    # Calculate the layer
    field_name = value_final_fld
    expression = '0'
    ##print '\n  Where: "{}":'.format(where_clause)  # For testing
    print '    Calculating field:\n      [{}] = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management('null_values', field_name, expression, expression_type)
    arcpy.Delete_management('null_values')

    #---------------------------------------------------------------------------
    #         Delete the prod data and append the working data to prod

    print '  Get working data to prod:'
    print '    Deleting features at:\n      {}'.format(prod_binned_fc)
    arcpy.DeleteFeatures_management(prod_binned_fc)

    print '\n    Append features from:\n      {}\n    To:\n      {}'.format(FINAL_hex_fc, prod_binned_fc)
    arcpy.Append_management(FINAL_hex_fc, prod_binned_fc)

    print '\nFinished Bin_Points_w_UnitCount()'
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def CPASG_Points_w_UnitCount(wkg_fgdb, fc_to_make_cpasg_tbl, prod_cpasg_tbl, CMTY_PLAN_CN_2011, shorthand_name, unit_count_fld):
    """
    """
    print '\nStarting CPASG_Points_w_UnitCount():'

    # Set variables
    cpasg_label_exist_fld = 'CPASG_LABEL'  # The name of the existing field in CMTY_PLAN_CN_2011
    cpasg_label_new_fld   = 'CPASG_NAME'  # The new field name to give the CPASG_LABEL
    cpasg_fld             = 'CPASG'
    value_final_fld       = 'VALUE_{}'.format(shorthand_name)
    expression_type       = 'PYTHON_9.3'


    print '\n  Creating CPASG table from processed data found at:\n    {}'.format(fc_to_make_cpasg_tbl)


    #---------------------------------------------------------------------------
    #      Get the CMTY_PLAN_CN_2011 FC into a frequency table (with all CPASGs)
    # This will be the table that will become the FINAL CPASG table
    final_CPASG_tbl = os.path.join(wkg_fgdb, '{}_CPASG_FINAL'.format(shorthand_name))
    freq_fields = [cpasg_label_exist_fld, cpasg_fld]

    print '\n  Performing Frequency Analysis on FC:\n    {}'.format(CMTY_PLAN_CN_2011)
    print '  Frequency Fields:'
    for f in freq_fields:
        print '    {}'.format(f)
    print '  To create table:\n    {}'.format(final_CPASG_tbl)
    arcpy.Frequency_analysis(CMTY_PLAN_CN_2011, final_CPASG_tbl, freq_fields)


    #---------------------------------------------------------------------------
    #              Clean up the FINAL Frequency Analysis Table

    print '\n  Cleaning up the CPASG Table at:\n    {}'.format(final_CPASG_tbl)

    # Delete the [FREQUENCY] field created by the Frequency Analysis (for clarity)
    print '\n    Delete the field: [FREQUENCY] created by the Frequency Analysis b/c it is not needed'
    arcpy.DeleteField_management(final_CPASG_tbl, 'FREQUENCY')


    # Change the field name [CPASG_LABEL] to [CPASG_NAME] (for clarity)
    existing_field_name = cpasg_label_exist_fld
    new_field_name      = cpasg_label_new_fld
    print '\n    Changing field name from: "{}" to: "{}"'.format(existing_field_name, new_field_name)
    arcpy.AlterField_management(final_CPASG_tbl, existing_field_name, new_field_name)


    # Add VALUE field
    print '\n    Adding field:'
    field_name = value_final_fld
    field_type = 'DOUBLE'
    print '      [{}] as a:  {}'.format(field_name, field_type)
    arcpy.AddField_management(final_CPASG_tbl, field_name, field_type)


    # Add the 'Countywide' feature
    print '\n    Adding "Countywide" feature'
    fields = [cpasg_label_new_fld, cpasg_fld]
    with arcpy.da.InsertCursor(final_CPASG_tbl, fields) as cursor:
        cursor.insertRow(('Countywide', 190000))
    del cursor


    #---------------------------------------------------------------------------
    #           Intersect 'FC to make CPASG table' with CMTY_PLAN_CN_2011

    in_features = [fc_to_make_cpasg_tbl, CMTY_PLAN_CN_2011]
    int_fc = os.path.join(wkg_fgdb, '{}_CPASG_int'.format(shorthand_name))
    print '\n  Intersecting:'
    for fc in in_features:
        print '    {}'.format(fc)
    print '  To create FC:\n    {}'.format(int_fc)
    arcpy.Intersect_analysis(in_features, int_fc)


    #---------------------------------------------------------------------------
    # Perform Frequency on Intersected FC, while summing the Unit Count field
    # This will be the table that will be used to find the sum of the VALUE field

    freq_analysis_tbl = os.path.join(wkg_fgdb, '{}_CPASG_int_freq'.format(shorthand_name))
    freq_fields = [cpasg_label_exist_fld, cpasg_fld]
    sum_fields  = [unit_count_fld]

    print '\n  Performing Frequency Analysis on FC:\n    {}'.format(int_fc)
    print '  Frequency Fields:'
    for f in freq_fields:
        print '    {}'.format(f)
    print '  Sum fields:'
    for f in sum_fields:
        print '    {}'.format(f)
    print '  To create TEMP Table:\n    {}'.format(freq_analysis_tbl)
    arcpy.Frequency_analysis(int_fc, freq_analysis_tbl, freq_fields, sum_fields)


    #---------------------------------------------------------------------------
    # For Freq Table from Intersected FC, Create a row to hold 'Countywide' and
    #                calc it as a sum of the VALUE field


    # Find the sum of the VALUE field
    # (to input for the 'Countywide' feature created below)
    print '\n  In TEMP Table, finding sum of the field: "{}":'.format(unit_count_fld)
    sum_of_quantity = 0
    with arcpy.da.SearchCursor(freq_analysis_tbl, [unit_count_fld]) as cursor:
        for row in cursor:
            sum_of_quantity = sum_of_quantity + row[0]
    del cursor


    # Add the 'Countywide' feature and calc the quantity to equal the sum of all quantities
    print '\n  Adding "Countywide" feature in TEMP Table:'
    print '    Calculating the VALUE of "Countywide" feature to equal "{}"\n'.format(sum_of_quantity)
    fields = [cpasg_label_exist_fld, cpasg_fld, unit_count_fld]
    with arcpy.da.InsertCursor(freq_analysis_tbl, fields) as cursor:
        cursor.insertRow(('Countywide', 190000, sum_of_quantity))
    del cursor


    #---------------------------------------------------------------------------
    #           Join the FINAL freq table and the Intersected freq table
    #                         and calc the VALUE field

    # Join the Final Frequency Table with the Intersected Frequency Table
    print '\n  Join the CPASG FINAL table with the TEMP Frequency Analysis tbl to calc the VALUE field'
    join_lyr = Join_2_Objects_By_Attr(final_CPASG_tbl, cpasg_fld, freq_analysis_tbl, cpasg_fld, 'KEEP_ALL')


    # Calculate the VALUE field in the FINAL Frequency Table
    table_name      = os.path.basename(freq_analysis_tbl)
    expression      = '!{}.{}!'.format(table_name, unit_count_fld)
    print '\n  Calculating field:\n    {} = {}\n'.format(value_final_fld, expression)
    arcpy.CalculateField_management(join_lyr, value_final_fld, expression, expression_type)
    arcpy.Delete_management(join_lyr)  # Need to delete this join so it does not conflict with other joins

    #---------------------------------------------------------------------------
    #             Calc any <Null> values in VALUE field to 0

    print '\n  In FINAL table, calculating any <Null> values in VALUE field to 0:'

    # Make a layer that only has <Null> values in the VALUE field
    where_clause = "{} IS NULL".format(value_final_fld)
    arcpy.MakeTableView_management(final_CPASG_tbl, 'null_values', where_clause)

    # Calculate the layer
    field_name = value_final_fld
    expression = "0"
    print '\n  Where: "{}":'.format(where_clause)  # For testing
    print '    Calculating field:\n      [{}] = {}\n'.format(field_name, expression)
    arcpy.CalculateField_management('null_values', field_name, expression, expression_type)
    arcpy.Delete_management('null_values')

    #---------------------------------------------------------------------------
    #         Delete the prod data and append the working data to prod

    print '  Get working data into prod:'
    print '    Deleting features at:\n      {}'.format(prod_cpasg_tbl)
    arcpy.DeleteRows_management(prod_cpasg_tbl)

    print '\n    Append features from:\n      {}\n    To:\n      {}'.format(final_CPASG_tbl, prod_cpasg_tbl)
    arcpy.Append_management(final_CPASG_tbl, prod_cpasg_tbl)


    print '\nFinished CPASG_Points_w_UnitCount()'
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

    # Print the fields (only really needed during testing)
    ##fields = arcpy.ListFields('target_obj')
    ##print '  Fields in joined layer:'
    ##for field in fields:
    ##    print '    ' + field.name

    print '    Finished Join_2_Objects_By_Attr()'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
