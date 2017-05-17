#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     12/05/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import arcpy, os
arcpy.env.overwriteOutput = True

def main():
    #                              Set variables
    # FGDB to import the Excel table info
    FGDB_path = r'P:\CIP\20170403_CIP_to_App\Data\CIP_Imported_Excel.gdb'

    # Update Excel file info
    excel_file        = r'P:\CIP\20170403_CIP_to_App\Working\Test\CIP_5YEAR_POLY_testing.xlsx'
    sheet_to_import   = 'CIP_5YEAR_POLY'
    join_field        = 'PROJECT_ID'

    # SDW connection info
    sdw_connection        = r'P:\CIP\20170403_CIP_to_App\Data\Fake_SDW.gdb'
    sdw_cip_fc_name       = 'CIP_5YEAR_POLY'
    sdw_cip_fc_path       = os.path.join(sdw_connection, sdw_cip_fc_name)
    sdw_lueg_updates_path = os.path.join(sdw_connection, 'SDW.PDS.LUEG_UPDATES')

    # List of Fields to update in SDW/SDE Feature Class
    # 'PROJECT_ID' not in below list since that is the field used to join
    sdw_field_ls =   ['NAME', 'TYPE', 'PROJECT_STATUS',
                      'DETAIL_WK_PROG', 'FIVE_YR_PLAN', 'EST_START', 'EST_COMPLT',
                      'EST_PR_CST', 'FUNDING_STATUS', 'FUNDING', 'LENGTH',
                      'PLANNING_GROUP', 'SUPERVISOR_DISTRICT', 'THOMAS_BROTHERS',
                      'PROJECT_MANAGER', 'PM_EMAIL', 'PM_PHONE', 'ORACLE_NUMBER',
                      'DESCRIPTION']

    # Dictionary of [TYPE] domains.
    #The left side is the text : The right side is the numerical value the [TYPE] field expects in SDW
    type_dict = {
    'Road Reconstruction':'1',
    'Community Development Block Grant':'2',
    'Bike Lanes/Pathways':'3',
    'Traffic Signals':'4',
    'Intersection Improvements':'5',
    'Sidewalks':'6',
    'Drainage Improvements':'7',
    'Bridge':'8',
    'Wastewater':'9.1',
    'Airports':'9.2',
    'Utility Undergrounding Districts':'9.3',
    'Watersheds':'9.4'
    }


    #---------------------------------------------------------------------------
    #                       Start calling FUNCTIONS

    # Get DateTime to append to the imported Excel table
    dt_to_append = Get_DT_To_Append()

    # Import Excel to FGDB Table
    imported_table = os.path.join(FGDB_path, sheet_to_import + '_' + dt_to_append)
    Excel_To_Table(excel_file, imported_table, sheet_to_import)

    # Validate the imported table data (make sure it has the correct fields
    valid_table = Validate_Table(sdw_field_ls, imported_table, sdw_cip_fc_path)

    # If import table was valid, Process table
    if valid_table:
        Process_Table(imported_table, type_dict)

    # Join processed table to SDW CIP Feature Class
    if valid_table:
        joined_fc = Join_2_Objects(sdw_cip_fc_path, join_field, imported_table, join_field)

    # Update fields from imported table to SDW Feature Class
    if valid_table:
        Update_Fields(joined_fc, sdw_cip_fc_name, imported_table, sdw_field_ls)

    # Let user know that they need to review the data and update the LUEG_UPDATES table
    # in order for Blue SDE can be updated
    # TODO: Uncomment the below print statements / raw_input
    if valid_table:
        print '***Updated the data in BLUE SDW, but you are NOT DONE YET! To update BLUE SDE please:***'
        print '  1) Review the updated Feature Class at: "{}"'.format(sdw_cip_fc_path)
        print '  2) Then, update the date for: "{}", in: "{}"'.format( sdw_cip_fc_name, sdw_lueg_updates_path)
        print '  3) In a few days, check to confirm that the changes from BLUE SDE have replicated to County SDEP'

##    raw_input('Press ENTER to finish.')


#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#                          Start defining FUNCTIONS
#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#                         FUNCTION: Get dt_to_append
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
#                          FUNCTION: Validate_Table()
def Validate_Table(sdw_field_ls, imported_table, sdw_cip_fc_path):
    """
    PARAMETERS:
      sdw_field_ls (list of str): The list of fields that we defined in main()
        that are in SDW FC that we want to update with the imported table.

      imported_table (str): The full path of the imported_table generated from
        Excel_To_Table()

      sdw_cip_fc_path (str): The full path of the SDW CIP Feature Class.

    RETURNS:
      valid_table (Boolean): A Boolean variable that is 'False' if there were ERRORS,
        but is 'True' if there were NO errors or if there were only WARNINGS.
        if valid_table = 'False' we can stop the script in main() so we do not
        copy over bad/incomplete data to SDW.

      proj_ids_not_in_imprt_tbl (list of str): Project ID's that are in SDW, but
        are not found in the import table.

      proj_ids_not_in_sdw (list of str): Project ID's that are in the import table,
        but are not found in SDW.

    FUNCTION:
        To validate the newly imported FGDB table from the Excel table.  This
        function:
          1) Checks for any "Blank Projects" and deletes them.
             Blank projects are not really CIP projects,
             they exist only because there are values embedded in the PROJECT_ID
             field to minimize the amount of editing GIS needs to do on
             CIP's Excel sheet.

          2) Validates that the fields that need to be updated in SDW are found
             in the import table.
             "valid_table = False" if not.

          3.1) Validates that all PROJECT_ID's in SDW are also in the import table,
               warns user of ID's in SDW, but not in import table.
               "valid_table = True" regardless of this validation result.

          3.2) Validates that all PROJECT_ID's in the import table are also in SDW,
               "valid_table = True" regardless of this validation result.

          4) Validates that every project has a PROJECT_ID and a NAME.
             "valid_table = False" if any project is missing one of these.
    """

    print 'Starting Validate_Table()...'

    valid_table = True

    #---------------------------------------------------------------------------
    #                    1) Delete any blank projects
    # 'Blank projects' have a PROJECT_ID from the Excel table, but they don't
    # have any other attributes.  The Excel sheet has preset PROJECT_ID's for
    # our workflow to reduce the amount of editing needed by GIS in the Excel sheet.

    print '  Checking for "Blank Projects"'
    lyr_w_selection = Select_Object(imported_table, 'NEW_SELECTION', "NAME = '' and TYPE = '' ")

    count = Get_Count_Selected(lyr_w_selection)

    print '    There are {} blank projects to delete'.format(count)

    if count != 0:
        print '    Deleting...'
        arcpy.DeleteRows_management(lyr_w_selection)

    print '  Done checking for "Blank Projects"\n'

    #---------------------------------------------------------------------------
    #       2) Validate that the fields we need in SDW are in the import table

    print '  Validating the field names in import table:'

    # Get a list of the names of the fields in the imported table
    imported_fields = arcpy.ListFields(imported_table)
    imported_field_names = []
    for field in imported_fields:
        imported_field_names.append(field.name)

    # list to contain any fields in sdw_field_ls that is not in the imported table
    fields_not_in_imprt_tbl = []

    # For each SDW field in the sdw_field_ls, pass if the imported table has the same named field
    for sdw_field in sdw_field_ls:
        if sdw_field in imported_field_names:
            pass

    # If there is a field in our sdw_field_ls that is NOT in the imported table,
    # Stop the function and return 'valid_table = False' so we do not copy incomplete data
        else:
            fields_not_in_imprt_tbl.append(sdw_field)

    # If there were any fields in sdw_field_ls, but not in import table
    if (len(fields_not_in_imprt_tbl) != 0):
        print '*** ERROR! The below field(s) is/are NOT in the imported table. ***'
        for field in fields_not_in_imprt_tbl:
            print '        "{}"'.format(field)
        print '      Please see why these fields are not in the import table.'
        print '      valid_table = False'
        valid_table = False

    print '  Done validating the field names in import table\n'

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    # 3)               Validate that PROJECT_ID's exist in both datasets

    # Get list of PROJECT_ID's in SDW FC
    sdw_project_ids = []
    with arcpy.da.SearchCursor(sdw_cip_fc_path, ['PROJECT_ID']) as cursor:
        for row in cursor:
            sdw_project_ids.append(row[0])

    # Get lists of PROJECT_ID's in imported table
    imprt_tbl_project_ids = []
    with arcpy.da.SearchCursor(imported_table, ['PROJECT_ID']) as cursor:
        for row in cursor:
            imprt_tbl_project_ids.append(row[0])

    # Sort the lists
    sdw_project_ids.sort()
    imprt_tbl_project_ids.sort()

    #---------------------------------------------------------------------------
    # 3.1) If a PROJECT_ID exists in SDW that is not in the import table,
    # warn user but do not change valid_table
    print '  Validating PROJECT_ID in SDW is also in import table:'

    # List to contain any PROJECT_ID'S that are in SDW but not in the import table
    proj_ids_not_in_imprt_tbl = []

    for project_id in sdw_project_ids:
        if project_id in imprt_tbl_project_ids:
            pass

        # There is a project that is in SDW but not in import table.  This could
        # happen if CIP deleted a project in their Excel file.
        else:
            proj_ids_not_in_imprt_tbl.append(project_id)

    # If there were any projects in SDW, but not in import table warn user
    if (len(proj_ids_not_in_imprt_tbl) != 0):
        print '*** WARNING!  The below PROJECT_ID(s) is/are in the SDW FC, but not in the import table: ***'
        for proj in proj_ids_not_in_imprt_tbl:
            print '        {}'.format(proj)
        print '    Any project in SDW should have a project in the import table.'
        print '    Please inform CIP that their "Excel sheet may be missing these projects,'
        print '    and that these project still exist in their database,'
        print '    but they will not be updated if they are not in the Excel sheet."'
        print '    Function NOT stopped however.'

    print '  Done validating PROJECT_ID in SDW\n'

    #---------------------------------------------------------------------------
    # 3.2) Make sure that every PROJECT_ID in the import table also exists in SDW
    # warn user but do not change valid_table

    print '  Validating PROJECT_ID in import table is also in SDW:'

    # list to contain any PROJECT_ID's that are in import table, but not in SDW
    proj_ids_not_in_sdw = []

    for project_id in imprt_tbl_project_ids:
        if project_id in sdw_project_ids:
            pass

        # There is a project that is in the import table but not SDW.  This could happen
        # if CIP added a project, but GIS has not added the project footprint in SDW.
        else:
            proj_ids_not_in_sdw.append(project_id)

    # If there were any projects in import table, but not SDW inform user and stop function:
    if (len(proj_ids_not_in_sdw) != 0):
        print '*** WARNING! The below PROJECT_ID(s) is/are in the import table, but NOT in the SDW FC: ***'
        for proj in proj_ids_not_in_sdw:
            print '        {}'.format(proj)
        print '    This means there will be no polygon in SDW to update.  Contact CIP for project footprint.'
        print '    Please create a polygon in SDW with the above project number to update this project with its attributes, all other attributes in SDW can be <NULL>'

    print '  Done validating PROJECT_IDs in import table\n'

    #---------------------------------------------------------------------------
    # 4) Make sure that every project has a PROJECT_ID and a NAME

    print '  Validating that every project has a PROJECT_ID and a NAME'

    # Where clause to select only the invalid
    where_clause = "PROJECT_ID IS NULL OR NAME = ''"
    with arcpy.da.SearchCursor(imported_table, ['PROJECT_ID', 'NAME'], where_clause) as cursor:
        for row in cursor:
            print '*** ERROR! The below project is missing either PROJECT_ID or NAME, both are needed for a valid table. ***'
            print '    PROJECT_ID: "{}"      NAME: "{}"'.format(row[0], row[1])
            valid_table = False

    print '  Done Validating PROJECT_ID and NAME'

    #---------------------------------------------------------------------------
    # Finish function notes

    if valid_table == False:
        print '*** ERROR! The update cannot be completed. ***'
        print '  Validate_Table function has found missing / incorrect info.  Please see above for error messages.'

    print 'Finished Validating Table\n'

    return valid_table, proj_ids_not_in_imprt_tbl, proj_ids_not_in_sdw

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION: Process_Table()

def Process_Table(imported_table, type_dict):
    """
    PARAMETERS:
      imported_table: The path of the imported_table generated from Excel_To_Table().
        we will perform calculations on this table before joining to SDW FC.

      type_dict: The dictionary defined in main() that has the string and code
        values of all the types in the domain CIP_TYPE.

    RETURNS:
      none

    FUNCTION:
      To process any data in the imported_table before joining to the SDW FC.
      This function:
        1) Makes sure that all values in [NAME] are all uppercase.
        2) Changes the string values in the Excel sheet in [TYPE] to the
           corresponding numeric values that are used in the actual SDW FC.
    """

    print 'Processing Table...'

    #---------------------------------------------------------------------------
    # 1)  Calculate field [NAME] to have all upper case letters for consistency
    field_to_calc = 'NAME'
    expression    = '!NAME!.upper()'

    print '  Calculating field: "{}" to equal: "{}"'.format(field_to_calc, expression)
    arcpy.CalculateField_management(imported_table, field_to_calc, expression, 'PYTHON_9.3')

    #---------------------------------------------------------------------------
    # 2) Calculate the values in [TYPE] to equal the values in the domain CIP_TYPE
    # not the string values found in the Excel table
    print '\n  Calculating [TYPE] based off of CIP_TYPE domain:'
    for typ in type_dict:

        where_clause = "TYPE = '{}'".format(typ)
        # Perform a selection based on the where_clause
        lyr_w_selection = Select_Object(imported_table, 'NEW_SELECTION', where_clause)

        # Get the count of the number of selected rows
        count_selected = Get_Count_Selected(lyr_w_selection)

        # If there were selected rows, calculate those rows based on the dictionary value
        if count_selected != 0:
            domain_value = type_dict[typ]
            print '    Calculating field: "TYPE" to equal: {}\n'.format(domain_value)
            arcpy.CalculateField_management(lyr_w_selection, 'TYPE', domain_value)

        else:
            print '*** WARNING, no records selected.  Field not calculated. ***'

    print 'Finished Processing Table\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Join 2 Objects

def Join_2_Objects(target_obj, target_join_field, to_join_obj, to_join_field):
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
    arcpy.AddJoin_management('target_obj', target_join_field, 'to_join_obj', to_join_field)

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
#                         FUNCTION: Update_Fields()

def Update_Fields(joined_fc, sdw_cip_fc_name, imported_table, sdw_field_ls):
    """
    PARAMETERS:
        joined_fc: The in-memory object from Join_2_Objects() that contains the
          SDW layer joined to the imported table.

        sdw_cip_fc_name: The name of the FC in SDW that we have joined to.
          Used in 'field_to_calc'.

        imported_table: Used to get the basename of the imported table.  Used in
          'expression'.

        sdw_field_ls: List of the fields that are in SDW (and imported table)
          that will be updated.  Used in a loop to run through all the fields
          to calculate.

    RETURNS:
        none

    FUNCTION:
        To calculate the fields in 'sdw_field_ls' list from the imported
        table to the SDW feature class.
    """

    print 'Updating Fields in Joined Feature Class...'

    # Get the basename of the imported table, i.e. "CIP_5YEAR_POLY_2017_5_15__9_38_50"
    # Will be used in 'expression' below
    import_table_name = os.path.basename(imported_table)

    for field in sdw_field_ls:

        field_to_calc = '{}.{}'.format(sdw_cip_fc_name, field)
        expression    = '!{}.{}!'.format(import_table_name, field)

        print '  In joined_fc, calculating field: "{}", to equal: "{}"'.format(field_to_calc, expression)
        arcpy.CalculateField_management(joined_fc, field_to_calc, expression, 'PYTHON_9.3')

    print 'Finished Updating Fields\n'

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

    print '    Starting Select_Object()...'

    # Use try/except to handle either object type (Feature Layer / Table)
    try:
        arcpy.MakeFeatureLayer_management(path_to_obj, 'lyr')
    except:
        arcpy.MakeTableView_management(path_to_obj, 'lyr')

    print '      Selecting "lyr" with a selection type: {}, where: "{}"'.format(selection_type, where_clause)
    arcpy.SelectLayerByAttribute_management('lyr', selection_type, where_clause)

    ##print '    Finished Select_Object()'
    return 'lyr'

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

    print '    Starting Get_Count()...'

    # See if there are any selected records
    desc = arcpy.Describe(lyr)

    if desc.fidSet: # True if there are selected records
        result = arcpy.GetCount_management(lyr)
        count_selected = int(result.getOutput(0))

    # If there weren't any selected records
    else:
        count_selected = 0

    print '      Count of Selected: {}'.format(str(count_selected))

    ##print '    Finished Get_Count()'

    return count_selected

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
