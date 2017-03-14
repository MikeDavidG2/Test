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
import csv, arcpy
from xml.dom import minidom
from datetime import datetime

#-------------------------------------------------------------------------------
#                              FUNCTION: main()

def main():

    # Set Variables
    xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX_sample ORIG.xml"

    # Folder CSV file will be saved to
    csv_folder = r'U:\grue\Projects\GaryProjects\csv_files'
    csv_file_name = 'xml_to_csv'

    # FGDB the CSV will be imported to
    fgdb_path = r'U:\grue\Projects\GaryProjects\test.gdb'
    table_name = 'csv_to_table'

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    # Call function
    xml_to_table(xml_file, csv_folder, csv_file_name, fgdb_path, table_name)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION: xml_to_table()

def xml_to_table(xml_file, csv_folder, csv_file_name, fgdb_path, table_name):

    #---------------------------------------------------------------------------
    #                    Create CSV file with headers

    print 'Creating CSV file at: {}'.format(csv_folder)

    #Create a unique name for the CSV file based on the date and time
    currentTime = datetime.now()
    date = '{}_{}_{}'.format(currentTime.year, currentTime.month, currentTime.day)
    time = '{}_{}_{}'.format(currentTime.hour, currentTime.minute, currentTime.second)
    dt = '{}__{}'.format(date, time)
    csv_path_file = '{}\{}_{}.csv'.format(csv_folder, csv_file_name, dt)

    #Set the headers for the file
    headers = ['RECORD_ID', 'LATITUDE_WGS84_GEOINFO', 'LONGITUDE_WGS84_GEOINFO']

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
    for item in item_list:

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

    #---------------------------------------------------------------------------
    #                    Import csv to FGDB table

    # TODO: this import creates a very long field for the RECORD_ID, I may have to create a field mapping object to correct this...need to reserach
    in_rows  = csv_path_file
    out_path = fgdb_path
    out_name = table_name + '_' + dt

    print 'Importing csv to FGDB: {}\n  Named: {}'.format(out_path, out_name)
    arcpy.TableToTable_conversion(in_rows, out_path, out_name)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
