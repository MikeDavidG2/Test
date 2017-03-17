#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     14/03/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import csv, arcpy, time
from xml.dom import minidom
from datetime import datetime

#-------------------------------------------------------------------------------
#                              FUNCTION: main()

def main():

    # Set Variables
    xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX_sample ORIG.xml"
    xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX.xml"
    xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX.xml"
    ##xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX First 5000 records.xml"
    ##xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX 5001 to 10000.xml"
    ##xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX last 4015.xml"

    # Number of records in xml to process
    num_records_to_process = 10

    # Folder CSV file will be saved to
    csv_folder = r'U:\grue\Projects\GaryProjects\csv_files'
    csv_file_name = 'xml_to_csv'

    # FGDB the CSV will be imported to
    fgdb_path = r'U:\grue\Projects\GaryProjects\test.gdb'
    table_name = 'csv_to_table'

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    # Call functions
    csv_path_file, dt = xml_to_csv(xml_file, csv_folder, csv_file_name, fgdb_path, table_name, num_records_to_process)

    csv_to_feature_class(csv_path_file, fgdb_path, table_name, dt)

#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------
#                          FUNCTION: xml_to_table()

def xml_to_csv(xml_file, csv_folder, csv_file_name, fgdb_path, table_name, num_records_to_process):

    #---------------------------------------------------------------------------
    #                    Create CSV file with headers

    print 'Creating CSV file at: {}'.format(csv_folder)

    #Create a unique name for the CSV file based on the date and time
    currentTime = datetime.now()
    date_now = '{}_{}_{}'.format(currentTime.year, currentTime.month, currentTime.day)
    time_now = '{}_{}_{}'.format(currentTime.hour, currentTime.minute, currentTime.second)
    dt = '{}__{}'.format(date_now, time_now)
    csv_path_file = '{}\{}_{}.csv'.format(csv_folder, csv_file_name, dt)

    #Set the headers for the file
    headers = ['RECORD_ID_temp', 'LATITUDE_WGS84_GEOINFO', 'LONGITUDE_WGS84_GEOINFO']

    #Create the CSV with headers
    with open(csv_path_file, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

    #---------------------------------------------------------------------------
    #                     Parse xml info to csv

    # Get connection to the xml file
    xml_doc = minidom.parse(xml_file)
    item_list = xml_doc.getElementsByTagName('Details')

    print 'There are {} records in "{}" to write to the csv\n'.format(str(len(item_list)), xml_file)

    # Go through each item in 'Details' and get defined values
    for count, item in enumerate(item_list):

        if (count < num_records_to_process):
            # Get value for each 'Details' row
            record_id  = item.attributes['RECORD_ID'].value
            lat_wgs84  = item.attributes['LATITUDE_WGS84_GEOINFO'].value
            long_wgs84 = item.attributes['LONGITUDE_WGS84_GEOINFO'].value

            # Set values into one list
            row_info = [record_id, lat_wgs84, long_wgs84]

            # Set list into csv file
            with open(csv_path_file, 'ab') as csv_file:
                print 'Writing to csv:\n  Record ID:  {}\n  Latitude:   {}\n  Longitude: {}\n'.format(record_id, lat_wgs84, long_wgs84)
                writer = csv.writer(csv_file)
                writer.writerow(row_info)

    print 'Done with xml_to_csv()'
    return csv_path_file, dt

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
    #                    Import csv to FGDB table

def csv_to_feature_class(csv_path_file, fgdb_path, table_name, dt):
    #TODO: put this part into a separate function to see if that resolves the existing connection being closed error
    in_rows  = csv_path_file
    out_path = fgdb_path
    out_name = table_name + '_' + dt

    print 'Importing csv to FGDB: {}\n  Named: {}\n'.format(out_path, out_name)
    ##time.sleep(30)
    try:
        arcpy.TableToTable_conversion(in_rows, out_path, out_name)
    except Exception as e:
        print 'String e: ' + str(e)
        print 'Type e: ' + type(e)

    print 'Imported'
    #---------------------------------------------------------------------------
    # This import leaves any string field with 8000 characters in length!
    # Need to add a field, calculate the values to this new field and delete
    # the field that has the length of 8000

    # Add field
    in_table = fgdb_path + '\\' + table_name + '_' + dt
    field_name = 'RECORD_ID'
    field_type = 'TEXT'
    field_length = 25

    print 'Adding field: "{}"\n'.format(field_name)
    arcpy.AddField_management (in_table, field_name, field_type, field_length)

    # Calculate new field to equal the RECORD_ID_temp
    expression = '!RECORD_ID_temp!'
    expression_typ = 'PYTHON_9.3'

    print 'Calculating field: "{}" so that it equals: "{}"\n'.format(field_name, expression)
    arcpy.CalculateField_management (in_table, field_name, expression, expression_typ)

    # Delete RECORD_ID_temp
    drop_field = 'RECORD_ID_temp'

    print 'Deleting field: "{}"\n'.format(drop_field)
    arcpy.DeleteField_management(in_table, drop_field)

    #---------------------------------------------------------------------------
    #                   Turn table into a Feature Class

# TODO: fill this out



    print 'Successfully completed CSV to Feature Class'


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
