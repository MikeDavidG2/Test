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
    FGDB_path = r'P:\CIP\20170403_CIP_to_App\Working\Test'
    FGDB_name = 'Testing_FGDB.gdb'
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

    # 3) Copy Budget Table
    # out_table is the FGDB and the name of the Table in table_to_copy
    out_budget_table = path_name_FGDB + '\\' + os.path.basename(table_to_copy)
    myFunc.Copy_Rows(table_to_copy, out_budget_table)

    # 4) Import Excel CIP table
    wkg_CIP_table = path_name_FGDB + '\\' + sheet_to_import + '_wkg'
    myFunc.Excel_To_Table(excel_to_import, wkg_CIP_table, sheet_to_import)

    # 5) Process new FGDB CIP table so it is ready for joining to the FC
    continue_script = Process_CIP_Table(wkg_CIP_table, out_feature_class)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          Start defining FUNCTIONS

def Process_CIP_Table(wkg_CIP_table, out_feature_class):
    """Documentation here
    """

    print 'Starting Process_CIP_Table...'

    #                     Create views and layers to do processing
    # Create a table view for CIP table
    CIP_view = 'CIP_view'
    arcpy.MakeTableView_management(wkg_CIP_table, CIP_view)

    # Create a layer for the FC
    FC_view = 'FC_view'
    arcpy.MakeFeatureLayer_management(out_feature_class, FC_view)

    #---------------------------------------------------------------------------
    #                       Validate CIP table and FC
    # Find if there are any Projects that GIS hasn't added a PROJECT_ID, stop script if so
    # TODO: Change where clause so that it searches for any
    where_clause = "PROJECT_ID = 'New, GIS to add'"
    arcpy.SelectLayerByAttribute_management(CIP_view, 'NEW_SELECTION', where_clause)

    # Get the count of selected records, if any selected stop script
    count_selected = myFunc.Get_Count_Selected(CIP_view)

    if count_selected != 0:
        print '  WARNING!  There are projects in CIP table that need GIS to enter a PROJECT_ID.'
        print '  Script halted.  GIS needs to:\n    1) Unprotect sheet with password: "GIS"\n    2) Add a unique PROJECT_ID for all projects\n    3) Reprotect the sheet with the same password.\n    4) Rerun this script'

        continue_script = False
        return continue_script

    # Find if there are any projects that will not be able to join in CIP table and FC, stop script if so



    #---------------------------------------------------------------------------
    # CIP table and FC validated, continue processing CIP table




    # Select rows if PROJECT_ID = '' and NAME = ''


    # Delete selected rows



    print 'Finished Process_CIP_Table.\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
