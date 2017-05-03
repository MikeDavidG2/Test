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
    This function does 4 sub tasks:
      1) Get a list of all the SampleEventIDs that occur more than once in the
           target_table (considered 'Duplicates').
           Function stopped if there are no duplicates.
      2) Sort the duplicates into one of two duplicate categories:
            A. Type 1 or Type 2
            B. Type 3
      3) Handle the Type 1 or Type 2 duplicates by deleting all of the
           duplicates except for the youngest duplicate (per duplication).
           This means that only the youngest duplicate remains in the dataset.
           Google 'Last one to sync wins'.  This is a common method for
           handling conflicting data.
      4) Handle the Type 3 duplicates by renaming the SampleEventID for all
           Type 3 duplicates so that it is obvious that there was a duplicate.



    TYPES OF DUPLICATES:
      Type 1:  Can occur if a survey is sent late enough in the day that the
          survey arrives to the online database the next day (UTC time).  This
          means the data is retrieved by script the next morning when it is run,
          AND is grabbed again the following day because the script is looking
          for all data that arrived to the database the previous day.  These
          duplicates are IDENTICAL.

          Can be FIXED by deleting either duplication.


      Type 2:  Occurs when a user goes into 'Sent' folder on their device and
          opens up an already sent survey and resends the survey.  It may be an
          accident, or on purpose.  The survey may be DIFFERENT or IDENTICAL to
          the original, and there may be more than 2 of this type of duplicate.

          Can be FIXED by deleting all of these duplicates, except for the last
          submitted survey.  This is the 'youngest' survey and will act as the
          only true version.  This will allow the users to make corrections in
          the field.



      Type 3:  Occurs when two users start a survey within 1/10th of a second
          from each other on the same day.  Very rare (about once per decade if
          there are 3 monitors submitting 30 records M-F over 6 hours each day).
          These surveys will be completely DIFFERENT with the exception of the
          Sample Event ID.

          Can be FIXED by giving these duplicates a new SampleEventID that can
          still be easily converted back to the original SampleEventID.
          For example, appending a '_1' or '0.0000001' so that '20170502.123456'
          becomes '20170502.123456_1' or '20170502.1234561'
    """
    print '--------------------------------------------------------------------'
    print 'Starting Duplicate_Handler()'

    # This is what the script below will chaange SampleEventIDs of all
    # Type 1 and 2 duplicates to in order to 'flag' them for deletion later in
    # the script
    dup_type_1_2_flag = -99

    #---------------------------------------------------------------------------
    #                 Get list of all duplicate SampleEventIDs

    unique_list   = []
    dup_list      = []
    with arcpy.da.SearchCursor(target_table, ['SampleEventID']) as cursor:
        for row in cursor:

            # Only add duplicate if it is the first instance of a duplication
            if row[0] in unique_list and row[0] not in dup_list:
                print row[0]
                dup_list.append(Decimal(row[0]))

            # Add the SampleEventID to the unique list if it is not in there already
            if row[0] not in unique_list:
                print row[0]
                unique_list.append(row[0])

    #---------------------------------------------------------------------------
    #                 Stop function if there are no duplicates

    if (len(dup_list) == 0):
        print '  There are no duplicates in: {}'.format(target_table)
        print 'Finished Duplicate_Handler()'
        return

    #---------------------------------------------------------------------------
    #                        There were duplicates,
    #         categorize the duplicates into (Type 1, 2)  and (Type 3)

    dup_typ_1_2 = []  # List to hold the Type 1 and 2 duplicates
    dup_typ_3   = []  # List to hold the Type 3 duplicates

    dup_list.sort()

    # TODO: figure out the decimal, float, precision problem.  And how I can keep SampleEventID a nubmer and still have it work in this script...
    print '#######################'
    print dup_list[0]

    for dup in dup_list:
        print '{}'.format(dup)

    print '########################'
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

        # For each duplicated SampleEventID, go through each duplicate and leave
        # the youngest of them alone, but change all of the older ones to dup_typ_1_2_flag
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

        where_clause = "SampleEventID = {}".format(str(dup_type_1_2_flag))
        arcpy.SelectLayerByAttribute_management('target_table_view', 'NEW_SELECTION', where_clause)

        # Test to see how many records were selected
        result = arcpy.GetCount_management('target_table_view')
        count_selected = int(result.getOutput(0))

        # Only perform deletion if there are selected rows
        if count_selected > 0:

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

        # For each duplicated SampleEventID, append a 7th number to the SampleEventIDs to make them unique
        for dup in dup_typ_3:

            num_to_append = 0.0000001
            where_clause = "SampleEventID = {}".format(dup)

            with arcpy.da.UpdateCursor(target_table, ['SampleEventID'], where_clause) as cursor:
                for row in cursor:
                    ##new_sampID = float(str(row[0]) + str(num_to_append))
                    ##print '    Changing SampleEventID: {} to {}'.format(str(row[0]), str(new_sampID))

                    new_sampID = row[0] + num_to_append
                    print '    Changing SampleEventID: {} to {}'.format(str(row[0]), str(new_sampID))
                    row[0] = new_sampID
                    cursor.updateRow(row)
                    num_to_append += 0.0000001

    print '\n\nFinished Duplicate_Handler()'

if __name__ == '__main__':
    main()
