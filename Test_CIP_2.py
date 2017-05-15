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
    excel_file      = r'P:\CIP\20170403_CIP_to_App\Working\Test\CIP_5YEAR_POLY_testing.xlsx'
    sheet_to_import = 'CIP_5YEAR_POLY'
    join_field      = 'PROJECT_ID'

    # SDW connection
    sdw_connection  = r'P:\CIP\20170403_CIP_to_App\Data\Fake_SDW.gdb'
    sdw_cip_fc_name = 'CIP_5YEAR_POLY'
    sdw_cip_fc_path      = os.path.join(sdw_connection, sdw_cip_fc_name)

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
    Validate_Data()

    # Process table
    Process_Table()

    # Join processed table to SDW CIP Feature Class
    joined_fc = myFunc.Join_2_Objects(sdw_cip_fc_path, join_field, imported_table, join_field)

    # Update fields from imported table to SDW Feature Class
    Update_Fields(joined_fc, sdw_cip_fc_name, imported_table, sdw_field_ls)


#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#                          Start defining FUNCTIONS
#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#                          FUNCTION: Validate_Data()
def Validate_Data():
    """
    """

    print 'Validating Data...'



    print 'Finished Validating Data\n'

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
