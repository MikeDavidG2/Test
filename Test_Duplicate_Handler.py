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

import arcpy, decimal

def main():

    target_table = r'X:\month\test.gdb\Field_Data_orig_1'

    ls_type_3_dups = Duplicate_Handler(target_table)

    for note in ls_type_3_dups:
        print note

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION Duplicate Handler

def Duplicate_Handler(target_table):
    """
    PARAMETERS: 'target_table'.  The table to search for the duplicates.

    RETURNS: 'ls_type_3_dups'.  A list of Type 3 duplicates (if any) that were
        found during this run of the script.

    This function does 4 sub tasks:
      A) Get a list of all the SampleEventIDs that occur more than once in the
           target_table (considered 'Duplicates').
           Function stopped if there are no duplicates.
      B) Sort the duplicates into one of two duplicate categories:
            a. Type 1 or Type 2
            b. Type 3
            * Types explained below
      C) Handle the Type 1 or Type 2 duplicates by deleting all of the
           duplicates except for the youngest duplicate (per duplication).
           This means that only the youngest duplicate remains in the dataset.
           (Google 'Last one to sync wins'.  This is a common method for
           handling conflicting data.)
      D) Handle the Type 3 duplicates by renaming the SampleEventID for all
           Type 3 duplicates so that it is obvious that there was a duplicate.
           Make a list of Type 3 duplicates so that they can be mentioned in
           an email

    *TYPES OF DUPLICATES:
      Type 1:  Can occur if a survey is sent late enough in the day that the
          survey arrives to the online database the next day (UTC time).  This
          means the data is retrieved by script the next morning when it is run,
          AND is grabbed again the following day because the script is looking
          for all data that arrived to the database the previous day.  These
          duplicates are IDENTICAL.

          Can be FIXED by deleting either duplication.  We will delete the older.

      Type 2:  Occurs when users go into their 'Sent' folder on their device and
          opens up an already sent survey and resends the survey.  It may be an
          accident, or on purpose.  The survey may be DIFFERENT or IDENTICAL to
          the original, and there may be more than 2 of this type of duplicate.

          Can be FIXED by deleting all of these duplicates, except for the last
          submitted survey.  This is the 'youngest' survey and will act as the
          only true version.  This will allow the users to make corrections in
          the field.

      Type 3:  Occurs when two users start a survey within 1/10th of a second
          of each other on the same day.  Very rare (about once per decade if
          there are 3 monitors submitting 30 records M-F over 6 hours each day).
          These surveys will be completely DIFFERENT with the exception of the
          Sample Event ID.

          Can be FIXED by giving these duplicates a new SampleEventID that can
          still be easily converted back to the original SampleEventID.
          For example, appending an incrementing number to the end of the ID
          so that two duplicates of:
            '20170502.123456'
          becomes:
            '20170502.1234561'
          and:
            '20170502.1234562'

          NOTE: IF a Type 3 duplicate happens and a monitor resends their
          survey (creaing a Type 2 duplicate), the SampleEventID will have
          Both a Type 3 and a Type 2 duplicate associated with it.  In this event
          The script will file this duplicate as a Type 3 and will rename all
          of the duplicates.
          It will not delete the Type 2 duplicate as might be expected.
    """
    print '--------------------------------------------------------------------'
    print 'Starting Duplicate_Handler()...\n'

    # The script will change the value of all SampleEventIDs of all Type 1 and 2
    # duplicates to 'dup_type_1_2_flag' in order to 'flag' them for deletion
    # later in the script
    dup_type_1_2_flag = 'Duplicate_Delete_Me'

    # This will be a list of the Type 3 duplicates that can be included in an
    # email if we set one up.  If there are no duplicates,
    ls_type_3_dups = ['No duplicates created by two users starting a survey at the same 1/10th of a second (Type 3 duplicates) found during this run of the script.']

    #---------------------------------------------------------------------------
    #              A)  Get list of all duplicate SampleEventIDs

    unique_list   = []
    dup_list      = []
    with arcpy.da.SearchCursor(target_table, ['SampleEventID']) as cursor:
        for row in cursor:

            # Only add duplicate if it is the first instance of a duplication
            if row[0] in unique_list and row[0] not in dup_list:
                dup_list.append((row[0]))

            # Add the SampleEventID to the unique list if it is not there already
            if row[0] not in unique_list:
                unique_list.append(row[0])

    #---------------------------------------------------------------------------
    #                 Stop function if there are no duplicates

    if (len(dup_list) == 0):
        print '  There are no duplicates in: "{}"'.format(target_table)
        print '\nFinished Duplicate_Handler() for: "{}"'.format(target_table)
        return ls_type_3_dups

    #---------------------------------------------------------------------------
    #                     B)  There were duplicates,
    #         categorize the duplicates into (Type 1, 2)  and (Type 3)

    dup_typ_1_2 = []  # List to hold the Type 1 and 2 duplicates
    dup_typ_3   = []  # List to hold the Type 3 duplicates

    dup_list.sort()

    print '  There is/are: "{}" duplicate(s) to categorize:'.format(str(len(dup_list)))

    for dup in dup_list:
        where_clause = "SampleEventID = '{}'".format(dup)
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
                print '    SampleEventID: "{}" = Type 1 or 2 dup'.format(row[0])
                dup_typ_1_2.append(row[0])

            elif len(unique_creators) > 1: # Then we have a Type 3 duplicate
                print '    SampleEventID: "{}" = Type 3 dup'.format(row[0])
                dup_typ_3.append(row[0])

    #---------------------------------------------------------------------------
    #               C)  Handle Type 1 and Type 2 duplicates
    # Handle the Type 1 and 2 duplicates by changing the SampleEventID to
    # 'dup_type_1_2_flag' for all duplicates except for the youngest duplicate.
    # We want to keep the youngest Type 1 or 2 duplicate.
    print '\n  There are "{}" Type 1 and Type 2 duplicates:'.format(str(len(dup_typ_1_2)))

    if len(dup_typ_1_2) == 0:
        print '    So nothing to change'

    # If there are Type 1 / 2 duplicates...
    if len(dup_typ_1_2) > 0:

        # For each duplicated SampleEventID, go through each duplicate and leave
        # the youngest of them alone, but change all of the older ones to dup_typ_1_2_flag
        for dup in dup_typ_1_2:

            where_clause = "SampleEventID = '{}'".format(dup)
            sql_clause   = (None, 'ORDER BY OBJECTID DESC') # This will order the cursor to grab the youngest duplicate first

            with arcpy.da.UpdateCursor(target_table, ['SampleEventID', 'OBJECTID'], where_clause, '', '', sql_clause) as cursor:
                i = 0
                for row in cursor:
                    if i == 0:
                        print '\n    Not changing youngest SampleEventID duplicate: "{}"'.format(str(row[0]))

                    if i > 0:  # Only update the SampleEventID for the older duplicates (i.e. NOT the first duplicate in this cursor)
                        print '    Changing older duplicate SampleEventID from: "{}" to: "{}"'.format(str(row[0]), str(dup_type_1_2_flag))
                        row[0] = dup_type_1_2_flag
                        cursor.updateRow(row)

                    i += 1

        # Select the older Type 1 and Type 2 duplicates that were flagged for deletion
        arcpy.MakeTableView_management(target_table, 'target_table_view')

        where_clause = "SampleEventID = '{}'".format(str(dup_type_1_2_flag))
        arcpy.SelectLayerByAttribute_management('target_table_view', 'NEW_SELECTION', where_clause)

        # Test to see how many records were selected
        result = arcpy.GetCount_management('target_table_view')
        count_selected = int(result.getOutput(0))

        # Only perform deletion if there are selected rows
        if count_selected > 0:

            print '\n    Deleting "{}" Type 1 and Type 2 duplicates with SampleEventID = "{}"'.format(count_selected, dup_type_1_2_flag)

            # Delete the older Type 1 and Type 2 duplicates that were flagged for deletion
            arcpy.DeleteRows_management('target_table_view')

    #---------------------------------------------------------------------------
    #                      D)  Handle Type 3 Duplicates
    print '\n  There is/are "{}" Type 3 duplicate(s):'.format(str(len(dup_typ_3)))

    if len(dup_typ_3) == 0:
        print '    So nothing to change'

    # If there are Type 3 duplicates...
    if len(dup_typ_3) > 0:

        # If there are Type 3 duplicates, reset the list so we can start fresh and append to it below
        ls_type_3_dups = ['  Below are duplicates that were created by two or more users starting their survey at the same 1/10th of a second (Type 3 duplicate)\n  Their SampleEventIDs have been changed:']

        # For each duplicated SampleEventID, append a 7th number to the SampleEventIDs to make them unique
        for dup in dup_typ_3:

            num_to_append = 1
            where_clause = "SampleEventID = '{}'".format(dup)

            with arcpy.da.UpdateCursor(target_table, ['SampleEventID', 'Creator'], where_clause) as cursor:
                for row in cursor:

                    new_sampID = row[0] + str(num_to_append)
                    notification_dup_type_3 = '    SampleEventID: "{}" with Creator: "{}" was changed to: "{}"'.format(row[0], row[1], str(new_sampID))
                    row[0] = new_sampID
                    cursor.updateRow(row)

                    print notification_dup_type_3
                    ls_type_3_dups.append(notification_dup_type_3)

                    num_to_append += 1

        ls_type_3_dups.append('  GIS: Please check the above Type 3 duplicates for any lingering Type 2 duplicates that still need to be removed from the database')

    print '\nFinished Duplicate_Handler() for: "{}"'.format(target_table)

    return ls_type_3_dups




if __name__ == '__main__':
    main()
