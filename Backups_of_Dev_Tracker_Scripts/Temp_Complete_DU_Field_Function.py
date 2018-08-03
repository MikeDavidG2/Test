#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     03/08/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
def main():
    csv_table_complete_du = r'P:\20180510_development_tracker\DEV\Data\1_Imported_CSVs.gdb\Test_Input_DU_numbers'
    record_id_fld     = 'RECORD_ID'
    du_fld            = 'DWELLING_UNITS'
##    csv_table_complete_du = r'P:\20180510_development_tracker\DEV\Data\1_Imported_CSVs.gdb\Test_Input_DU_numbers_edited'

    Complete_DU_Field(csv_table_complete_du, record_id_fld, du_fld)



#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Complete_DU_Field(csv_table_complete_du, record_id_fld, du_fld):
    """
    """

    print '\n------------------------------------------------------------------'
    print 'Starting Complete_DU_Field()'


    #---------------------------------------------------------------------------
    #                  Get a list of unique RECORD_IDs
    print '  Getting list of all RECORD_IDs:'
    record_ids = []
    with arcpy.da.SearchCursor(csv_table_complete_du, [record_id_fld]) as cursor:
        for row in cursor:
            record_ids.append(row[0])
    del cursor

    # Get a list of all the UNIQUE ID's
    # set() returns a list of only unique values
    unique_record_ids = sorted(set(record_ids))
    print '    There are "{}" unique Record IDs\n'.format(len(unique_record_ids))


    # For each record_id, find a value for the du_fld
    print '  For each Record ID (project), find the projects DU value, and add'
    print '  that value to any rows for that project that do not have a DU value'
    for record_id in unique_record_ids:
        fields = [record_id_fld, du_fld]

        # Set the where_clause (for records that have a du_value)
        has_du_value = "{} = '{}' AND {} IS NOT NULL".format(record_id_fld, record_id, du_fld)
        with arcpy.da.SearchCursor(csv_table_complete_du, fields, has_du_value) as cursor:
            for row in cursor:
                du_value  = row[1]  # This is the value for the du_fld to be added

                ##print 'Record ID: {}'.format(record_id)  # For testing
                ##print '  DU Value: {}'.format(du_value)  # For testing

                # Now, set the du_value into all of the same record_id that does not have a value in the du_fld
                no_du_value = "{} = '{}' AND {} IS NULL".format(record_id_fld, record_id, du_fld)
                with arcpy.da.UpdateCursor(csv_table_complete_du, fields, no_du_value) as updt_cursor:
                    for updt_row in updt_cursor:
                        updt_row[1] = du_value
                        updt_cursor.updateRow(updt_row)

    print '\nFinished Complete_DU_Field()'

if __name__ == '__main__':
    main()
