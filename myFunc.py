import os, arcpy, datetime
##arcpy.env.overwriteOutput = True

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Copy_FC()
def Copy_FC(in_features, out_feature_class):
    """
    PARAMETERS:
      in_features (str): Full path to a Feature Class.
      out_feature_class: Full path to another existing Feature Class.

    RETURNS:
      None

    FUNCTION:
      To copy Features from one FC to another existing FC.
    """

    print 'Starting Copy_FC()...'

    print '  Copying features from: "{}" to: "{}"'.format(in_features, out_feature_class)

    arcpy.CopyFeatures_management(in_features, out_feature_class)

    print 'Finished Copy_FC()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Copy_Rows()
def Copy_Rows(in_table, out_table):
    """
    PARAMETERS:
      in_table (str): Full path to an input table.
      out_table (str): Full path to an existing output table.

    RETURNS:
      None

    FUNCTION:
      To copy the rows from one table to another table.
    """

    print 'Starting Copy_Rows()...'

    print '  Copying Rows from: "{}"'.format(in_table)
    print '                 To: "{}"'.format(out_table)

    arcpy.CopyRows_management(in_table, out_table)

    print 'Finished Copy_Rows()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                           FUNCTION Create_FGDB()
def Create_FGDB(path_name_FGDB, overwrite_if_exists=False):
    """
    PARAMETERS:

    RETURNS:

    FUNCTION:
    """

    print 'Starting Create_FGDB()...'

    path, name = os.path.split(path_name_FGDB)

    #---------------------------------------------------------------------------
    #          Set create_fgdb variable to control if process is run

    # If FGDB doesn't exist, create it
    if not os.path.exists(path_name_FGDB + '.gdb'):
        create_fgdb = True

    # If FGDB does exist...
    else:
        # ... and overwrite_if_exists == True, create it
        if overwrite_if_exists == True:
            create_fgdb = True

        # ... and overwrite_if_exists == False, do not create FGDB
        else:
            create_fgdb = False

    #---------------------------------------------------------------------------
    # Run process if create_fgdb == True
    if create_fgdb == True:
        print '  Creating FGDB: "{}" at: "{}"'.format(name, path)
        arcpy.CreateFileGDB_management(path, name, 'CURRENT')

    else:
        print '  FGDB not created.  Set "overwrite_if_exists" to "True"'

    print 'Finished Create_FGDB()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                                 FUNCTION Delete_Rows()
def Delete_Rows(in_table):
    """
    PARAMETERS:
      in_table (str): Full path to a table.

    RETURNS:
      None

    FUNCTION:
      To delete the rows from one table.
    """

    print 'Starting Delete_Rows()...'

    print '  Deleting Rows from: "{}"'.format(in_table)

    arcpy.DeleteRows_management(in_table, out_table)

    print 'Finished Delete_Rows()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Excel_To_Table()
def Excel_To_Table(input_excel_file, out_table, sheet):
    """
    PARAMETERS:
        input_excel_file (str): The full path to the Excel file to import.

        out_table (str): The full path to the FGDB and NAME of the table in the FGDB.

        sheet (str): The name of the sheet to import.

    RETURNS:
        none

    FUNCTION:
        To import an Excel sheet into a FGDB.
    """

    print 'Starting Excel_To_Table()...'

    print '  Importing Excel file: {}\{}\n  To: {}'.format(input_excel_file, sheet, out_table)

    # Perform conversion
    arcpy.ExcelToTable_conversion(input_excel_file, out_table, sheet)

    print 'Finished Excel_To_Table()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                        FUNCTION Get_Count_Selected()
def Get_Count_Selected(lyr):
    """
    PARAMETERS:
      lyr (lyr): The layer that should have a selection on it that we want to test.

    RETURNS:
      count_selected (int): The number of selected records in the lyr

    FUNCTION:
      To get the count of the number of selected records in the lyr.
    """

    print 'Starting Get_Count()...'

    # See if there are any selected records
    desc = arcpy.Describe(lyr)

    if desc.fidSet: # True if there are selected records
        result = arcpy.GetCount_management(lyr)
        count_selected = int(result.getOutput(0))

    # If there weren't any selected records
    else:
        count_selected = 0

    print '  Count of Selected: {}'.format(str(count_selected))

    print 'Finished Get_Count()\n'

    return count_selected

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Get_dt_to_append
def Get_DT_To_Append():
    """
    PARAMETERS:
      none

    RETURNS:
      dt_to_append (str): Which is in the format 'YYYY_M_D__H_M_S'

    FUNCTION:
      To get a formatted datetime string that can be used to append to files
      to keep them unique.
    """
    print 'Starting Get_DT_To_Append()...'

    start_time = datetime.datetime.now()

    date = '%s_%s_%s' % (start_time.year, start_time.month, start_time.day)
    time = '%s_%s_%s' % (start_time.hour, start_time.minute, start_time.second)

    dt_to_append = '%s__%s' % (date, time)

    print '  DateTime to append: {}'.format(dt_to_append)

    print 'Finished Get_DT_To_Append()\n'
    return dt_to_append

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Join 2 Objects
def Join_2_Objects(target_obj, target_join_field, to_join_obj, to_join_field, join_type):
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
        that match a record in the join table.
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
    """

    print 'Starting Join_2_Objects()...'

    # Create the layers or views using try/except
    try:
        arcpy.MakeFeatureLayer_management(target_obj, 'target_obj')
        print '  Made FEATURE LAYER for {}'.format(target_obj)
    except:
        arcpy.MakeTableView_management(target_obj, 'target_obj')
        print '  Made TABLE VIEW for {}'.format(target_obj)

    try:
        arcpy.MakeFeatureLayer_management(to_join_obj, 'to_join_obj')
        print '  Made FEATURE LAYER for {}'.format(to_join_obj)
    except:
        arcpy.MakeTableView_management(to_join_obj, 'to_join_obj')
        print '  Made TABLE VIEW for {}'.format(to_join_obj)

    # Join the layers
    print '  Joining layers'
    arcpy.AddJoin_management('target_obj', target_join_field, 'to_join_obj', to_join_field, join_type)

    # Print the fields
    fields = arcpy.ListFields('target_obj')
    print '  Fields in joined layer:'
    for field in fields:
        print '    ' + field.name

    print 'Finished Join_2_Objects()...\n'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Select_Object()
def Select_Object(path_to_obj, selection_type, where_clause):
    """
    PARAMETERS:
      path_to_obj (str): Full path to the object (Feature Layer or Table) that
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

    print 'Starting Select_Object()...'

    # Use try/except to handle either object type (Feature Layer / Table)
    try:
        arcpy.MakeFeatureLayer_management(path_to_obj, 'lyr')
    except:
        arcpy.MakeTableView_management(path_to_obj, 'lyr')

    print '  Selecting "lyr" with a selection type: {}, where: "{}"'.format(selection_type, where_clause)
    arcpy.SelectLayerByAttribute_management('lyr', selection_type, where_clause)

    print 'Finished Select_Object()\n'
    return 'lyr'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Test_Schema_Lock()
def Test_Schema_Lock(dataset):
    """
    PARAMETERS:
      dataset (str): Full path to a dataset to be tested if there is a schema lock

    RETURNS:
      no_schema_lock (Boolean): "True" or "False" if there is no schema lock

    FUNCTION:
      To perform a test on a dataset and return "True" if there is no schema
      lock, and "False" if a schema lock already exists.
    """

    print 'Starting Test_Schema_Lock()...'

    print '  Testing dataset: {}'.format(dataset)

    no_schema_lock = arcpy.TestSchemaLock(dataset)
    print '  Dataset available to have a schema lock applied to it = "{}"'.format(no_schema_lock)

    print 'Finished Test_Schema_Lock()\n'

    return no_schema_lock

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Write_Print_To_Log()
def Write_Print_To_Log(log_file):
    """
    PARAMETERS:
      log_file (str): Path to log file.  The part after the last "\" will be the
        name of the .log file after the date, time, and ".log" is appended to it.

    RETURNS:
      orig_stdout (os object): The original stdout is saved in this variable so
        that the script can access it and return stdout back to its orig settings.

    FUNCTION:
      To turn all the 'print' statements into a log-writing object.  A new log
        file will be created based on log_file with the date, time, ".log"
        appended to it.  And any print statements after the command
        "sys.stdout = write_to_log" will be written to this log.
      It is a good idea to use the returned orig_stdout variable to return sys.stdout
        back to its original setting.
      NOTE: This function needs the function Get_DT_To_Append() to run

    """
    print 'Starting Write_Print_To_Log()...'

    # Get the original sys.stdout so it can be returned to normal at the
    #    end of the script.
    orig_stdout = sys.stdout

    # Get DateTime to append
    dt_to_append = Get_DT_To_Append()

    # Create the log file with the datetime appended to the file name
    log_file_date = '{}_{}.log'.format(log_file,dt_to_append)
    write_to_log = open(log_file_date, 'w')

    # Make the 'print' statement write to the log file
    print '  Setting "print" command to write to a log file found at:\n  {}'.format(log_file_date)
    sys.stdout = write_to_log

    # Header for log file
    start_time = datetime.datetime.now()
    start_time_str = [start_time.strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                  {}'.format(start_time_str)
    print '             START Update_DPW_w_MasterData.py'
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'

    return orig_stdout

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------