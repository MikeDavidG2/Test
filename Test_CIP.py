#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
"""

"""
# Author:      mgrue
#
# Created:     14/04/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, myFunc, os
arcpy.env.overwriteOutput = True

def main():

    #                              Set variables

    # FGDB to create variables
    FGDB_name = 'Testing_FGDB.gdb'
    FGDB_path = r'P:\CIP\20170403_CIP_to_App\Working\Test'
    path_name_FGDB = os.path.join(FGDB_path, FGDB_name)

    # FC to copy path
    fc_to_copy = r'P:\CIP\20170403_CIP_to_App\CIP.gdb\CIP_5YEAR_POLYD'

    # Tables to copy path
    table_to_copy = r'P:\CIP\20170403_CIP_to_App\CIP.gdb\CIP_PROJECT_TYPE'

    # Excel to import path
    excel_to_import = r'P:\CIP\20170403_CIP_to_App\Z WIP CIP 5 Year Dataset Sorted 170315 0826_test_PROTECTING.xlsx'
    sheet_to_import = 'projects_EDITED'

    #---------------------------------------------------------------------------
    #                        Start calling functions

    # 1) Create FGDB
    myFunc.Create_FGDB(path_name_FGDB, overwrite_if_exists=True)

    # 2) Copy Features
    # out_feature_class is the FGDB and the name of the Feature Class in fc_to_copy
    out_feature_class = path_name_FGDB + '\\' + os.path.basename(fc_to_copy)
    myFunc.Copy_FC(fc_to_copy, out_feature_class)

    # 3) Copy Budged Table
    # out_table is the FGDB and the name of the Table in table_to_copy
    out_table = path_name_FGDB + '\\' + os.path.basename(table_to_copy)
    myFunc.Copy_Rows(table_to_copy, out_table)

    # 4) Import Excel table
    out_table = path_name_FGDB + '\\' + sheet_to_import
    myFunc.Excel_To_Table(excel_to_import, out_table, sheet_to_import)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          Start defining FUNCTIONS



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
