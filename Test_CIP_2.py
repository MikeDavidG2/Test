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

# TODO: get the myFunc into this script so it can stand alone

import arcpy, myFunc, os
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
    sdw_field_ls =   ['PROJECT_ID', 'NAME', 'TYPE', 'PROJECT_STATUS',
                      'DETAIL_WK_PROG', 'FIVE_YR_PLAN', 'EST_START', 'EST_COMPLT',
                      'EST_PR_CST', 'FUNDING_STATUS', 'FUNDING', 'LENGTH',
                      'PLANNING_GROUP', 'SUPERVISOR_DISTRICT', 'THOMAS_BROTHERS',
                      'PROJECT_MANAGER', 'PM_EMAIL', 'PM_PHONE', 'ORACLE_NUMBER',
                      'DESCRIPTION']


    #---------------------------------------------------------------------------
    #                       Start calling FUNCTIONS

    # Get DateTime to append to the imported Excel table
    dt_to_append = myFunc.Get_DT_To_Append()

    # Import Excel to FGDB Table
    imported_table = os.path.join(FGDB_path, sheet_to_import + '_' + dt_to_append)
    myFunc.Excel_To_Table(excel_file, imported_table, sheet_to_import)

    # Validate the imported table data (make sure it has the correct fields
    valid_table = Validate_Table(sdw_field_ls, imported_table, sdw_cip_fc_path)

    # Process table
    ##Process_Table()

    # Join processed table to SDW CIP Feature Class
    ##joined_fc = myFunc.Join_2_Objects(sdw_cip_fc_path, join_field, imported_table, join_field)

    # Update fields from imported table to SDW Feature Class
    ##Update_Fields(joined_fc, sdw_cip_fc_name, imported_table, sdw_field_ls)

    # Let user know that they need to review the data and update the LUEG_UPDATES table
    # in order for Blue SDE can be updated
    # TODO: Uncomment the below print statements / raw_input
##    print 'Updated the data in BLUE SDW, but you are NOT DONE YET! To update BLUE SDE please:'
##    print '  1) Review the updated Feature Class at: "{}"'.format(sdw_cip_fc_path)
##    print '  2) Then, update the date for: "{}", in: "{}"'.format( sdw_cip_fc_name, sdw_lueg_updates_path)
##    print '  3) In a few days, check to confirm that the changes from BLUE SDE have replicated to County SDEP'
##
##    raw_input('Press ENTER to finish.')


#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#                          Start defining FUNCTIONS
#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------

#                          FUNCTION: Validate_Table()
def Validate_Table(sdw_field_ls, imported_table, sdw_cip_fc_path):
    """
    """

    print 'Validating Table...'

    valid_table = True

    # Get a list of the names of the fields in the imported table
    imported_fields = arcpy.ListFields(imported_table)
    imported_field_names = []
    for field in imported_fields:
        imported_field_names.append(field.name)

    #---------------------------------------------------------------------------
    #       Validate that the fields we need in SDW are in the import table

    print '  Validating the field names in import table'

    # For each SDW field in the sdw_field_ls, make sure the imported table has the same field
    for sdw_field in sdw_field_ls:
        if sdw_field in imported_field_names:
            ##print '    sdw_field: "{}" is in imported_field_names.'.format(sdw_field)
            pass

    # If there is a field in our sdw_field_ls that is NOT in the imported table,
    # Stop the function and return 'valid_table = False' so we do not copy incomplete data
        else:
            print '\n    *** ERROR! Field: "{}" is NOT in imported_field_names. ***'.format(sdw_field)
            print '      Please see why the field is not in the import table.\n      Script stopped.'
            valid_table = False
            return valid_table
    print '  Done validating the field names in import table'

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #               Validate that PROJECT_ID's exist in both datasets

    print '  Validating PROJECT_ID\'s exist in both SDW FC and import table'

    # Get list of PROJECT_ID's in SDW FC
    sdw_project_ids = []
    with arcpy.da.UpdateCursor(sdw_cip_fc_path, ['PROJECT_ID']) as cursor:
        for row in cursor:
            sdw_project_ids.append(row[0])

    # Get lists of PROJECT_ID's in imported table
    imprt_tbl_project_ids = []
    with arcpy.da.UpdateCursor(imported_table, ['PROJECT_ID']) as cursor:
        for row in cursor:
            imprt_tbl_project_ids.append(row[0])

    # Sort the lists
    sdw_project_ids.sort()
    imprt_tbl_project_ids.sort()

    #---------------------------------------------------------------------------
    # If a PROJECT_ID exists in SDW that is not in the import table, warn user but do not stop script
    print '    Validating PROJECT_ID in SDW is also in import table'

    for project_id in sdw_project_ids:
        if project_id in imprt_tbl_project_ids:
            ##print '      PROJECT_ID: "{}" in both import table and SDW FC'.format(project_id)
            pass

        # There is a project that is in SDW but not in import table.  This could
        # happen if CIP deleted a project in their Excel file.
        else:
            print '      *** WARNING!  PROJECT_ID: "{}" is in SDW, but not in the import table'.format(project_id)
            print '      Any project in SDW should have a project in the import table.'
            print '      Please inform CIP that their "Excel sheet has missing data for this project,'
            print '      and that this project still exists in their database, but it will not be updated if it is not in the Excel sheet."'
            print '      Script NOT stopped however.'

    #---------------------------------------------------------------------------
    # Make sure that every PROJECT_ID in the import table also exists in SDW
    # Stop script if an import table PROJECT_ID exists, but not in SDW FC

    print '    Validating PROJECT_ID in import table is also in SDW'

    for project_id in imprt_tbl_project_ids:
        if project_id in sdw_project_ids:
            ##print '      PROJECT_ID: "{}" in both import table and SDW FC'.format(project_id)
            pass

        # There is a project that is in the import table but not SDW.  This could happen
        # if CIP added a project, but GIS has not added the project footprint in SDW.
        else:
            print '\n      *** ERROR! PROJECT_ID: "{}" in import table, but NOT in SDW FC.'.format(project_id)
            print '      This means there will be no polygon to update info for in SDW.  Contact CIP for project footprint.'
            print '      Please create a polygon in SDW with the above project number before continuing.  All other attributes in SDW can be <NULL>'

            valid_table = False
            return valid_table

    print '  Done Validating PROJECT_ID\'s\n'



    print 'Finished Validating Table\n'
    return valid_table

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION: Process_Table()

def Process_Table():
    """
    """

    print 'Processing Table...'



    print 'Finished Processing Table\n'

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
if __name__ == '__main__':
    main()
