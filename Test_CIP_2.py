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

    # Excel file info
    excel_file      = r'P:\CIP\20170403_CIP_to_App\Working\CIP_5YEAR_POLY.xlsx'
    sheet_to_import = 'CIP_5YEAR_POLY'
    join_field      = 'PROJECT_ID'

    # SDW connection
    sdw_connection  = r'P:\CIP\20170403_CIP_to_App\Data\Fake_SDW.gdb'
    sdw_cip_fc      = os.path.join(sdw_connection, 'CIP_5YEAR_POLY')

    #---------------------------------------------------------------------------
    #                       Start calling FUNCTIONS

    # Get DateTime to append to the imported Excel table
    dt_to_append = myFunc.Get_DT_To_Append()

    # Import Excel to FGDB Table
    imported_table = os.path.join(FGDB_path, sheet_to_import + '_' + dt_to_append)
    myFunc.Excel_To_Table(excel_file, imported_table, sheet_to_import)

    # Process table
    Process_Table()

    # Join processed table to SDW CIP Feature Class
    joined_obj = myFunc.Join_2_Objects(sdw_cip_fc, join_field, imported_table, join_field)

    #TODO: remove this print statement when complete with the script
    fields = arcpy.ListFields(joined_obj)
    for field in fields:
        print field.name


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          Start defining FUNCTIONS

def Process_Table():
    """
    """

    print 'Processing Table...'



    print 'Finished Processing Table\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
