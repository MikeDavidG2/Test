#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     13/01/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy

def main():
    table = r'U:\grue\Scripts\Testing_or_Developing\Test_SampleDate\Test_SampleDate.gdb\DPW_Data_wkg_2017_1_13__11_22_13'

    Set_Time_Fields(table)

def Set_Time_Fields(table):
    with arcpy.da.SearchCursor(table, ['CreationDate_String']) as cursor:

        for row in cursor:

            # Turn the string obtained from the field into a datetime object
            dt_obj = datetime.datetime.strptime(row[0], '%m/%d/%Y %I:%M:%S %p')

            sample_date = [dt_obj.strftime('%m/%d/%Y')]

            survey_time = [dt_obj.strftime('%H:%M')]

            print 'Sample Date: ' + sample_date[0]
            print 'Survey Time: ' + survey_time[0]


if __name__ == '__main__':
    main()





