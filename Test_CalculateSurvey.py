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

#TODO:  Add this function into the main DPW_Science_and_Monitoring script
import arcpy

def main():
    table = r'U:\grue\Scripts\Testing_or_Developing\data\DPW_Science_and_Monitoring_wkg.gdb\DPW_Data_wkg_2017_1_17__15_35_46'

    Set_Time_Fields(table)

def Set_Time_Fields(table):

    with arcpy.da.UpdateCursor(table, ['CreationDate_String', 'SampleDate', 'SampleTime']) as cursor:

        for row in cursor:

            # Turn the string obtained from the field into a datetime object
            UTC_dt_obj = datetime.datetime.strptime(row[0], '%m/%d/%Y %I:%M:%S %p')

            # Subtract 8 hours from the UTC (Universal Time Coordinated) to get
            # PCT
            PCT_offset = -8
            t_delta = datetime.timedelta(hours = PCT_offset)
            PCT_dt_obj = UTC_dt_obj + t_delta

            sample_date = [PCT_dt_obj.strftime('%m/%d/%Y')]

            sample_time = [PCT_dt_obj.strftime('%H:%M')]

            print 'Sample Date: ' + sample_date[0]
            row[1] = sample_date[0]
            print 'Survey Time: ' + sample_time[0]
            row[2] = sample_time[0]

            # Update the cursor with the updated list
            cursor.updateRow(row)

if __name__ == '__main__':
    main()





