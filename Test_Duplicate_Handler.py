#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     01/05/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy

def main():

    target_table = r'X:\month\test.gdb\Field_Data_orig_1'

    Duplicate_Handler(target_table)


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION Duplicate Handler

def Duplicate_Handler(target_table):
    """
    This function does X sub tasks:
      1) Get a list of all the SampleEventIDs that occur more than once in the
           target_table (considered 'Duplicates').
           Function stopped if there are no duplicates.
      2) Sort the duplicates into one duplicate category:
            A. Type 1 or Type 2
            B. Type 3
      3) Handle the Type 1 or Type 2 duplicates by deleting all of the
           duplicates except for the youngest duplicate (per duplication).
           This means that only the youngest duplicate remains in the dataset.
           Google 'Last one to sync wins'.  This is a common method for
           handling conflicting data.
      4) Handle the Type 3 duplicates by renaming the SampleEventID for all
           Type 3 duplicates so that it is obvious that there was a duplicate.

    Types of duplicates:
      Type 1:

      Type 2:


      Type 3:
    """
    print '--------------------------------------------------------------------'
    print 'Starting Duplicate_Handler()'

    dup_type_1_2_flag = -99 # TODO: change this to 'Duplicate_Delete_Me' if [SampleEventID] is a text field


    #---------------------------------------------------------------------------
    #                 Get list of all duplicate SampleEventIDs

    unique_list   = []
    dup_list      = []
    with arcpy.da.SearchCursor(target_table, ['SampleEventID']) as cursor:
        for row in cursor:

            # Only add duplicate if it is the first instance of a duplication
            if row[0] in unique_list and row[0] not in dup_list:
                dup_list.append(row[0])

            else:
                # This SampleEventID is unique
                unique_list.append(row[0])

    #---------------------------------------------------------------------------
    #                 Stop function if there are no duplicates

    if (len(dup_list) == 0):
        print '  There are no duplicates in: {}'.format(target_table)
        print 'Finished Duplicate_Handler()'
        return

    #---------------------------------------------------------------------------
    #                        There were duplicates,
    #         sort the duplicates into (Type 1, 2)  and (Type 3)

    dup_typ_1_2 = []
    dup_typ_3   = []

    dup_list.sort()

    print '  There is/are: {} duplicate(s) to categorize:'.format(str(len(dup_list)))

    for dup in dup_list:
        where_clause = "SampleEventID = {}".format(dup)
        with arcpy.da.SearchCursor(target_table, ['SampleEventID', 'Creator'], where_clause) as cursor:
            unique_creators = []
            for row in cursor:
                # Get the number of unique creators for this SampleEventID
                if row[1] in unique_creators:
                    pass
                else:
                    unique_creators.append(row[1])

            # Use the # of unique creators to dictate if we have a Type 1/2 or Type 3 duplicate
            if len(unique_creators) == 1:  # Then we have a Type 1 or Type 2 duplicate
                print '    SampleEventID: {} = Type 1 or 2 dup'.format(row[0])
                dup_typ_1_2.append(row[0])

            elif len(unique_creators) > 1: # Then we have a Type 3 duplicate
                print '    SampleEventID: {} = Type 3 dup'.format(row[0])
                dup_typ_3.append(row[0])

            else:
                print '***ERROR, there should be at least one Creator***'

    #---------------------------------------------------------------------------
    #                   Handle Type 1 and Type 2 duplicates
    # Handle the Type 1 and 2 duplicates by changing the SampleEventID to
    # 'Duplicate_Delete_Me' for all duplicates except for the youngest duplicate
    # We want to keep the youngest Type 1 or 2 duplicate.
    print '\n  There are "{}" Type 1 and 2 duplicates:'.format(str(len(dup_typ_1_2)))

    if len(dup_typ_1_2) == 0:
        print '    Nothing to change'

    # If there are Type 1 / 2 duplicates...
    if len(dup_typ_1_2) > 0:
        for dup in dup_typ_1_2:

            where_clause = "SampleEventID = {}".format(dup)
            sql_clause   = (None, 'ORDER BY OBJECTID DESC') # This will order the cursor to grab the youngest duplicate first

            with arcpy.da.UpdateCursor(target_table, ['SampleEventID', 'OBJECTID'], where_clause, '', '', sql_clause) as cursor:
                i = 0
                for row in cursor:
                    if i == 0:
                        print '\n    Not changing youngest SampleEventID duplicate: {}'.format(str(row[0]))

                    if i > 0:  # Only update the SampleEventID for the older duplicates (i.e. NOT the first duplicate in this cursor)
                        print '    Changing older duplicate SampleEventID from: {} to {}'.format(str(row[0]), str(dup_type_1_2_flag))
                        row[0] = dup_type_1_2_flag
                        cursor.updateRow(row)

                    i += 1

        # Select the older Type 1 and Type 2 duplicates that were flagged for deletion
        arcpy.MakeTableView_management(target_table, 'target_table_view')

        where_clause = "SampleEventID = {}".format(str(dup_type_1_2_flag)) # TODO: add single quotes around the bracket: '{}' if SampleEventID is made into a string
        arcpy.SelectLayerByAttribute_management('target_table_view', 'NEW_SELECTION', where_clause)

        # Test to see how many records were selected
        result = arcpy.GetCount_management('target_table_view')
        count_selected = int(result.getOutput(0))

        if count_selected > 0:  # Only perform deletion if there are selected rows

            print '\n  Deleting {} Type 1 and Type 2 duplicates'.format(count_selected)

            # Delete the older Type 1 and Type 2 duplicates that were flagged for deletion
            arcpy.DeleteRows_management('target_table_view')

    #---------------------------------------------------------------------------
    #                          Handle Type 3 Duplicates
    print '\n  There is/are "{}" Type 3 duplicate(s):'.format(str(len(dup_typ_3)))

    if len(dup_typ_3) == 0:
        print '    Nothing to change'

    # If there are Type 3 duplicates...
    if len(dup_typ_3) > 0:

        for dup in dup_typ_3:

            num_to_append = 1
            where_clause = "SampleEventID = {}".format(dup)  # Update all of the Type 3 duplicates

            with arcpy.da.UpdateCursor(target_table, ['SampleEventID'], where_clause) as cursor:
                for row in cursor:
                    new_sampID = float(str(row[0]) + str(num_to_append)) # TODO: Change this to a string friendly format if SampleEventID becomes a string
                    print '    Changing SampleEventID: {} to {}'.format(str(row[0]), str(new_sampID))
                    row[0] = new_sampID
                    cursor.updateRow(row)
                    num_to_append += 1

    print '\n\nFinished Duplicate_Handler()'

if __name__ == '__main__':
    main()
