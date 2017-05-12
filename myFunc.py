import os, arcpy, datetime
##arcpy.env.overwriteOutput = True

#-------------------------------------------------------------------------------
#                         FUNCTION: Create_FGDB()

def Create_FGDB(path_name_FGDB, overwrite_if_exists=False):
    """
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
#                                 FUNCTION Copy_FC()
def Copy_FC(in_features, out_feature_class):
    """
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
    """

    print 'Starting Copy_Rows()...'

    print '  Copying Rows from: "{}" to: "{}"'.format(in_table, out_table)

    arcpy.CopyRows_management(in_table, out_table)

    print 'Finished Copy_Rows()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION Excel_To_Table()
def Excel_To_Table(input_excel_file, out_table, sheet):

    print 'Starting Excel_To_Table()...'

    print '  Importing Excel file: "{}\{}" to: {}'.format(input_excel_file, sheet, out_table)

    # Perform conversion
    arcpy.ExcelToTable_conversion(input_excel_file, out_table, sheet)

    print 'Finished Excel_To_Table()\n'
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                        FUNCTION Get_Count_Selected()
def Get_Count_Selected(lyr):

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
#                          FUNCTION Get dt_to_append

def Get_DT_To_Append():
    """
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

def Join_2_Objects(target_obj, target_join_field, to_join_obj, to_join_field):
    """
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
    arcpy.AddJoin_management('target_obj', target_join_field, 'to_join_obj', to_join_field)

    print 'Finished Join_2_Objects()...\n'

    # Return the layer/view of the joined object so it can be processed
    return 'target_obj'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
