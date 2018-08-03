#-------------------------------------------------------------------------------
# Name:        DEV_TRACKER_Process_Unit_Count_Pts.py
# Purpose:
"""
To take a point feature class and get:
    The number of points per CPASG (as a FGDB Table)
    The number of points per HEXBIN (as a Feature Class)
"""
# Author:      mgrue
#
# Created:     22/05/2018
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
    name_of_script = 'DEV_TRACKER_Process_Unit_Count_Pts.py'


    # Paths to folders and local FGDBs
    root_folder       = r'P:\20180510_development_tracker\DEV'

    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    data_folder       = '{}\{}'.format(root_folder, 'Data')

    points_fgdb     = '{}\{}'.format(data_folder, '3_Points.gdb')

    wkg_cpasg_fgdb  = '{}\{}'.format(data_folder, '4_wkg_CPASG.gdb')

    wkg_hexbin_fgdb = '{}\{}'.format(data_folder, '5_wkg_HEXBINS.gdb')

    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    create_pts_success_file = 'SUCCESS_running_DEV_TRACKER_Create_Unit_Count_Pts.txt'  # Hard Coded into variable here

    # Paths to SDE Feature Classes AND Tables
    CMTY_PLAN_CN       = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.CMTY_PLAN_CN'

    GRID_HEX_060_ACRES = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.GRID_HEX_060_ACRES'

    sde_database       = r'Database Connections\AD@ATLANTIC@SDW (ip addy).sde'

    dev_tracker_fds    = 'SDW.PDS.PDS_DEV_TRACKER'


    #Control Table (Used to pass variables to script.  i.e. The CSV names)
    control_table = '{}\SDW.PDS.PDS_DEV_TRACKER_CONTROL_TABLE'.format(sde_database)
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
    #             Make sure that the points were successfully created
    #                       before trying to process them.
    #---------------------------------------------------------------------------
    if success == True:

        if os.path.exists('{}\{}'.format(success_error_folder, create_pts_success_file)):
            print '\nDEV_TRACKER_Create_Unit_Count_Pts.py was run successfully, processing the points now\n'

        else:
            success = False
            print '\n*** ERROR! ***'
            print '  This script is designed to process points that was created by a previously run script: "DEV_TRACKER_Create_Unit_Count_Pts.py"'
            print '  If it was completed successfully, The "DEV_TRACKER_Create_Unit_Count_Pts.py" script should have written a file named:\n    {}'.format(create_pts_success_file)
            print '  At:\n    {}'.format(success_error_folder)
            print '\n  It appears that the above file does not exist, meaning that the Create Points script had an error.'
            print '  This script will not run if there was an error in "DEV_TRACKER_Create_Unit_Count_Pts.py"'
            print '  Please fix any problems with that script first. Then try again.'
            print '  You can find the log files at:\n    {}'.format(log_file_folder)


    #---------------------------------------------------------------------------
    #                      Create FGDBs if needed
    #---------------------------------------------------------------------------
    if success == True:

        # Create working CPASG FGDB if it does not exist
        if not arcpy.Exists(wkg_cpasg_fgdb):
            out_folder_path, out_name = os.path.split(wkg_cpasg_fgdb)
            print 'Creating FGDB: "{}" at:\n  {}'.format(out_name, out_folder_path)
            arcpy.CreateFileGDB_management(out_folder_path, out_name)

        # Create working Hexbin FGDB if it does not exist
        if not arcpy.Exists(wkg_hexbin_fgdb):
            out_folder_path, out_name = os.path.split(wkg_hexbin_fgdb)
            print 'Creating FGDB: "{}" at:\n  {}'.format(out_name, out_folder_path)
            arcpy.CreateFileGDB_management(out_folder_path, out_name)


    #---------------------------------------------------------------------------
    #                       Process Points
    #---------------------------------------------------------------------------
    if success == True:
        # Loop through each Row in the control_table (where PROCESS = True) and:
        #   Process the points
        fields = ['SHORTHAND_NAME', 'CPASG_TABLE_NAME_IN_SDE', 'HEXBIN_FC_NAME_IN_SDE', 'PROCESS_UNIT_COUNT']
        with arcpy.da.SearchCursor(control_table, fields, control_table_where_clause) as cursor:
            for row in cursor:

                # Get variables from control_table
                shorthand_name   = row[0]
                cpasg_table_name = row[1]
                hexbin_fc_name   = row[2]

                print '\n--------------------------------------------------------'
                print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
                print '--------------------------------------------------------'
                print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print 'Processing: "{}"'.format(shorthand_name)

                # Flag to control if the point FC is attempted to be processed
                process_point_fc = True

                # Set paths to Feature Classes / Tables
                points_fc       = '{}\{}_Pts'.format(points_fgdb, shorthand_name)
                sde_cpasg_table = '{}\{}'.format(sde_database, cpasg_table_name)
                sde_hexbin_fc   = '{}\{}\{}'.format(sde_database, dev_tracker_fds, hexbin_fc_name)

                # Test to make sure the paths exist
                if not arcpy.Exists(points_fc):
                    success = False
                    process_point_fc = False
                    print '*** ERROR, The below FC does not exist and "{}" cannot be processed.  Please check the path ***:\n  {}'.format(shorthand_name, points_fc)

                if not arcpy.Exists(sde_cpasg_table):
                    success = False
                    process_point_fc = False
                    print '*** ERROR, The below FC does not exist and "{}" cannot be processed.  Please check the path ***:\n  {}'.format(shorthand_name, sde_cpasg_table)

                if not arcpy.Exists(sde_hexbin_fc):
                    success = False
                    process_point_fc = False
                    print '*** ERROR, The below FC does not exist and "{}" cannot be processed.  Please check the path ***:\n  {}'.format(shorthand_name, sde_hexbin_fc)

                if process_point_fc == True:
                    try:
                        print '  Point FC is at:\n    {}\n'.format(points_fc)
                        print '  CPASG table is at:\n    {}\n'.format(sde_cpasg_table)
                        print '  Hexbin FC is at:\n    {}'.format(sde_hexbin_fc)


                        #-----------------------------------------------------------
                        #            Add and calculate a Quantity Field

                        # Set Field Name of the Quantity field that will be added
                        new_quantity_field_name = 'QTY_{}'.format(shorthand_name)

                        # Set the Field Name of the Quantity field that MAY already exist
                        # (i.e. if a quantity field is already in the extract it could be named 'HOUSING _UNITS)'
                        existing_quantity_field_name = 'HOUSING_UNITS'

                        Add_And_Calc_Quantity_Field(points_fc, new_quantity_field_name, existing_quantity_field_name)

                        #-----------------------------------------------------------
                        #                  Create the CPASG Table
                        Create_CPASG_Table(points_fc, shorthand_name, new_quantity_field_name, CMTY_PLAN_CN, wkg_cpasg_fgdb, sde_cpasg_table)

                        #-----------------------------------------------------------
                        #                  Create the Hexbin FC
                        Create_HEXBIN_FC(points_fc, shorthand_name, new_quantity_field_name, GRID_HEX_060_ACRES, wkg_hexbin_fgdb, sde_hexbin_fc)


                    except Exception as e:
                        success = False
                        print '*** ERROR! Unable to process: {} ***'.format(row[0])
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

    print '\n\nSuccess = {}'.format(success)


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
#                    FUNCTION: Add_And_Calc_Quantity_Field
def Add_And_Calc_Quantity_Field(points_fc, new_quantity_field_name, existing_quantity_field_name):
    """
    PARAMETERS:

    RETURNS:

    FUNCTION:
    """
    print '\n  ----------------------------------------------------------------'
    print '  Starting Add_And_Calc_Quantity_Field()\n'


    # Add Quantity field
    print '      Adding field: "{}" to FC:\n        {}\n'.format(new_quantity_field_name, points_fc)
    arcpy.AddField_management(points_fc, new_quantity_field_name, 'LONG')

    # Determine if there is a 'Quantity' field that already exists in the extracted data
    field_names = [f.name for f in arcpy.ListFields(points_fc)]

    if existing_quantity_field_name in field_names:

        # Calculate the newly added field to equal the value of the existing quantity field
        expression = '!{}!'.format(existing_quantity_field_name)

        print '      A quantity field already exists.  Calculating new quantity field to equal: "{}"\n'.format(expression)
        arcpy.CalculateField_management(points_fc, new_quantity_field_name, expression, 'PYTHON_9.3')

    else:
        # Calculate the newly added field to equal 1
        print '      No previously existing quantity field.  Calculating new quantity field to equal: "{}"\n'.format(1)
        arcpy.CalculateField_management(points_fc, new_quantity_field_name, 1)

    print '  Finished Add_And_Calc_Quantity_Field()'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                    FUNCTION: Create_CPASG_Table
def Create_CPASG_Table(points_fc, shorthand_name, new_quantity_field_name, CMTY_PLAN_CN, wkg_cpasg_fgdb, sde_cpasg_table):
    """
    PARAMETERS:

    RETURNS:

    FUNCTION:
    """
    print '\n  ----------------------------------------------------------------'
    print '  Starting Create_CPASG_Table()\n'
    #---------------------------------------------------------------------------
    #             Create Frequency of Points per CPASG (TABLE)
    #---------------------------------------------------------------------------

    #---------------------------------------------------------------------------
    #                  Spatial Join the points with CMTY_PLAN_CN
    print '    Spatially Join the Points with the CMTY_PLAN_CN dataset to get CPASG info:'

    # Spatial Join Points with CMTY_PLAN_CN
    points_CMTY_PLAN_join = '{}\{}_Pts_CMTY_PLAN_join'.format(wkg_cpasg_fgdb, shorthand_name)
    print '      Spatially Joining:\n          {}\n        And:\n          {}\n        To create Feature Class:\n          {}\n'.format(points_fc, CMTY_PLAN_CN, points_CMTY_PLAN_join)
    arcpy.SpatialJoin_analysis(points_fc, CMTY_PLAN_CN, points_CMTY_PLAN_join)


    #---------------------------------------------------------------------------
    #            Change the Field Name of from the CPASG dataset
    print '    Change the Field Name of the CPASG so the Append will work:'

    # Rename the field [CPASG_LABE] to [CPASG_NAME]
    existing_field_name = 'CPASG_LABE'
    new_field_name      = 'CPASG_NAME'
    print '      Changing field name from: "{}" to: "{}" for FC:\n        {}\n'.format(existing_field_name, new_field_name, points_CMTY_PLAN_join)
    arcpy.AlterField_management(points_CMTY_PLAN_join, existing_field_name, new_field_name)


    #---------------------------------------------------------------------------
    #                            Frequency Analysis
    print '    Frequency Analysis the Joined CPASG Data:'

    # Get the frequency of how many points (using the quantity field) are in each CPASG
    points_CMTY_PLAN_join_freq = points_CMTY_PLAN_join + '_freq'
    frequency_fields = ['CPASG_NAME', 'CPASG']
    summary_fields = [new_quantity_field_name]
    print '      Performing Frequency analysis on FC:\n          {}\n        To create Table:\n          {}'.format(points_CMTY_PLAN_join, points_CMTY_PLAN_join_freq)
    print '      Frequency Fields:'
    for freq_field in frequency_fields:
        print '        {}'.format(freq_field)
    print '      Summary Fields:'
    for summary_field in summary_fields:
        print '        {}'.format(summary_field)
    arcpy.Frequency_analysis(points_CMTY_PLAN_join, points_CMTY_PLAN_join_freq, frequency_fields, summary_fields)
    print ''

    #---------------------------------------------------------------------------
    #         Add New Feature 'Countywide' and calculate its sum as the sum of quantity field

    # Find the sum of the Quantity field (to input for the 'Countywide' feature created below
    print '    Finding sum of the field: "{}":'.format(new_quantity_field_name)
    sum_of_quantity = 0
    with arcpy.da.SearchCursor(points_CMTY_PLAN_join_freq, [new_quantity_field_name]) as cursor:
        for row in cursor:
            sum_of_quantity = sum_of_quantity + row[0]
    del cursor
    print '      Quantity Sum = {}\n'.format(sum_of_quantity)

    # Add the 'Countywide' feature and calculate the quantity to equal the sum of all quantities
    print '    Adding "Countywide" feature in Table:\n      {}'.format(points_CMTY_PLAN_join_freq)
    print '    Calculating the Quantity of "Countywide" feature = "{}"\n'.format(sum_of_quantity)
    fields = ['CPASG', 'CPASG_NAME', new_quantity_field_name]
    with arcpy.da.InsertCursor(points_CMTY_PLAN_join_freq, fields) as cursor:
        cursor.insertRow((190000, 'Countywide', sum_of_quantity))
    del cursor


    #---------------------------------------------------------------------------
    #                   Append Working Data into Production
    print '    Append Working Frequency Table into Production:'

    # Delete rows in production
    print '      Deleting production rows at:\n        {}\n'.format(sde_cpasg_table)
    arcpy.DeleteRows_management(sde_cpasg_table)

    # Append working rows to production
    print '      Appending working rows from:\n          {}\n        To:\n          {}'.format(points_CMTY_PLAN_join_freq, sde_cpasg_table)
    arcpy.Append_management(points_CMTY_PLAN_join_freq, sde_cpasg_table, 'NO_TEST')

    print '\n  Finished Create_CPASG_Table()'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                    FUNCTION: Create_HEXBIN_FC
def Create_HEXBIN_FC(points_fc, shorthand_name, new_quantity_field_name, GRID_HEX_060_ACRES, wkg_hexbin_fgdb, sde_hexbin_fc):
    """
    PARAMETERS:

    RETURNS:

    FUNCTION:
    """
    print '\n  ----------------------------------------------------------------'
    print '  Starting Create_HEXBIN_FC()\n'

    #---------------------------------------------------------------------------
    #           Create Frequency of Points Per Hexbin (FEATURE CLASS)
    #---------------------------------------------------------------------------
    #                            Spatial Join
    print '    Spatially Join the Points with the GRID_HEX_060_ACRES dataset:'

    # Spatial Join Points with CMTY_PLAN_CN
    points_GRID_HEX_join = '{}\{}_Pts_GRID_HEX_join'.format(wkg_hexbin_fgdb, shorthand_name)
    print '      Spatially Joining:\n        {}\n      And:\n        {}\n      To create Feature Class:\n        {}\n'.format(points_fc, GRID_HEX_060_ACRES, points_GRID_HEX_join)
    arcpy.SpatialJoin_analysis(points_fc, GRID_HEX_060_ACRES, points_GRID_HEX_join)


    #---------------------------------------------------------------------------
    #                            Frequency Analysis
    print '    Frequency Analysis the Joined HEX Data:'

    # Get the frequency of how many points (using the quantity field) are in each HEXBIN
    points_GRID_HEX_join_freq = points_GRID_HEX_join + '_freq'
    frequency_fields = ['HEXAGONID']
    summary_fields = [new_quantity_field_name]
    print '      Performing Frequency analysis on FC:\n        {}\n      To create Table:\n        {}'.format(points_GRID_HEX_join, points_GRID_HEX_join_freq)
    print '      Frequency Fields:'
    for freq_field in frequency_fields:
        print '        {}'.format(freq_field)
    print '      Summary Fields:'
    for summary_field in summary_fields:
        print '        {}'.format(summary_field)
    arcpy.Frequency_analysis(points_GRID_HEX_join, points_GRID_HEX_join_freq, frequency_fields, summary_fields)
    print ''

    #---------------------------------------------------------------------------
    #          Make a copy of the Hexbin data from SDE to a working FGDB
    print '    Make a copy of the Hexbin data from SDE to a working FGDB:'
    hexbins_to_append = '{}_{}'.format(shorthand_name, 'Hexbins_to_append')
    print '      Copying the Hexbin FC from:\n        {}\n      To:\n        {}\n      Named:\n        {}\n'.format(GRID_HEX_060_ACRES, wkg_hexbin_fgdb, hexbins_to_append)
    arcpy.FeatureClassToFeatureClass_conversion(GRID_HEX_060_ACRES, wkg_hexbin_fgdb, hexbins_to_append)

    #---------------------------------------------------------------------------
    #                  Add Needed Field to the copied Hexbin FC

    # Add needed field: [<new_quantity_field_name>]
    print '    Add a quantity field to the copied Hexbin FC:'
    hexbins_to_append_path = '{}\{}'.format(wkg_hexbin_fgdb, hexbins_to_append)
    field_name = new_quantity_field_name
    field_type = 'DOUBLE'

    print '      Adding field: "{}"\n      With Field Type: {}\n      To FC:\n        {}\n'.format(field_name, field_type, hexbins_to_append_path)
    arcpy.AddField_management(hexbins_to_append_path, field_name, field_type)


    #---------------------------------------------------------------------------
    #                    Calculate the quantity field
    print '    Calculate the quantity field:'

    # Join Hexbin FC with frequency table
    print '      Join the Hexbin FC with the frequency table in order to calculate the quantity field in the Hexbin FC:'
    GRID_HEX_w_freq_lyr = Join_2_Objects_By_Attr(hexbins_to_append_path, 'HEXAGONID', points_GRID_HEX_join_freq, 'HEXAGONID', 'KEEP_ALL')

    # Calculate the quantity field in the copied Hexbin FC to equal the quantity field in the Hexbin frequency table
    print '      Now calculate the quantity field in the copied Hexbin FC to equal the quantity field in the Hexbin frequency table'
    expression = "!{}_GRID_HEX_join_freq.{}!".format(shorthand_name + '_Pts', new_quantity_field_name)
    ##print '      Expression = "{}"'.format(expression)  # For testing
    arcpy.CalculateField_management(GRID_HEX_w_freq_lyr, '{}.{}'.format(hexbins_to_append, new_quantity_field_name), expression, 'PYTHON_9.3')

    # Remove join
    print '      Removing join on Hexbin FC\n'
    arcpy.RemoveJoin_management(GRID_HEX_w_freq_lyr)


    #---------------------------------------------------------------------------
    #           Append the Hexbin FC data into the correct SDE FC
    print '    Update SDE with processed Hexbin features:'

    # Delete the existing features in SDE
    print '      Deleting features at:\n        {}'.format(sde_hexbin_fc)
    arcpy.DeleteFeatures_management(sde_hexbin_fc)


    # Append the newly processed features to SDE
    print '      Appending the newly processed features:\n        From:\n          {}\n        To:\n          {}'.format(hexbins_to_append_path, sde_hexbin_fc)
    arcpy.Append_management(hexbins_to_append_path, sde_hexbin_fc, 'NO_TEST')

    print '\n  Finished Create_HEXBIN_FC()'


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

    print '        Starting Join_2_Objects_By_Attr()...'

    # Create the layer or view for the target_obj using try/except
    try:
        arcpy.MakeFeatureLayer_management(target_obj, 'target_obj')
        print '          Made FEATURE LAYER for: {}'.format(target_obj)
    except:
        arcpy.MakeTableView_management(target_obj, 'target_obj')
        print '          Made TABLE VIEW for: {}'.format(target_obj)

    # Create the layer or view for the to_join_obj using try/except
    try:
        arcpy.MakeFeatureLayer_management(to_join_obj, 'to_join_obj')
        print '          Made FEATURE LAYER for: {}'.format(to_join_obj)
    except:
        arcpy.MakeTableView_management(to_join_obj, 'to_join_obj')
        print '          Made TABLE VIEW for: {}'.format(to_join_obj)

    # Join the layers
    print '          Joining "{}"\n             With "{}"\n               On "{}"\n             Type "{}"'.format(target_obj, to_join_obj, to_join_field, join_type)
    arcpy.AddJoin_management('target_obj', target_join_field, 'to_join_obj', to_join_field, join_type)

    # Print the fields (only really needed during testing)
    ##fields = arcpy.ListFields('target_obj')
    ##print '  Fields in joined layer:'
    ##for field in fields:
    ##    print '    ' + field.name

    print '        Finished Join_2_Objects_By_Attr()'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
