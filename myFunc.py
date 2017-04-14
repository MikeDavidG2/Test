import os, arcpy
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