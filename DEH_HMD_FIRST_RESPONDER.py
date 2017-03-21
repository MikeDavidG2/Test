#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     17/03/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
import csv, arcpy, time, math
from xml.dom import minidom
from datetime import datetime

arcpy.env.overwriteOutput = True
#-------------------------------------------------------------------------------
#                              FUNCTION: main()

def main():

    #                           User, Set Variables:

    # main working folder
    working_folder = r'U:\grue\Projects\GaryProjects'

    # XML file to read
    xml_folder      = working_folder + r'\xml_files'
    xml_file_name   = r'\DEH_HMD_FIRST_RESPONDER_INDEX_sample ORIG.xml'
    xml_file_name   = r"\DEH_HMD_FIRST_RESPONDER_INDEX.xml"
    xml_path_file   = xml_folder + '\\' + xml_file_name

    # CSV file to be saved
    csv_folder    = working_folder + '\csv_files'
    csv_file_name = 'temp_csv.csv'
    csv_path_file = csv_folder + '\\' + csv_file_name

    # FGDB the CSV will be imported to
    fgdb_path  = working_folder + r'\test.gdb'
    table_name = 'csv_to_table'

    #---------------------------------------------------------------------------
    # Below are variables used with the batch file to control which functions are called

    # Set defaults for which functions are called.  None will be called unless
    # the batch file passes one of the two correct strings ('xml_to_csv' or 'csv_to_fc')
    run_create_csv   = False
    run_xml_to_csv   = False
    run_csv_to_table = False
    run_table_to_fc  = False

    # Use parameter from batch file calling this script to drive which functions are called
    xml_to_csv_OR_csv_to_fc = arcpy.GetParameterAsText(0)

    if xml_to_csv_OR_csv_to_fc == 'xml_to_csv':
        run_create_csv   = True
        run_xml_to_csv   = True

    elif xml_to_csv_OR_csv_to_fc == 'csv_to_fc':
        run_csv_to_table = True
        run_table_to_fc  = True

    else:
        print """WARNING!  This script expects a batch file to supply the value
            to the variable 'xml_to_csv_OR_csv_to_fc' to control which functions
            are called in the script.
            Valid values are 'xml_to_csv' or 'csv_to_fc'"""


    #---------------------------------------------------------------------------
    #                     START CALLING FUNCTIONS
    #---------------------------------------------------------------------------

    # Create the CSV
    if run_create_csv:
        create_csv(csv_path_file)

    # Read xml and parse to csv file
    if run_xml_to_csv:
        xml_to_csv(xml_path_file, csv_path_file)

    # Import csv file, process table
    if run_csv_to_table:
        csv_to_table(csv_path_file, fgdb_path, table_name)

    # Turn table into a Feature Class
    if run_table_to_fc:
        table_to_fc()


    print 'FINISHED with DEH_HMD_FIRST_RESPONDER.py!'

#-------------------------------------------------------------------------------
#********************    START DEFINING FUNCTIONS    ***************************
#-------------------------------------------------------------------------------

#                        FUNCTION: create_csv()
def create_csv(csv_path_file):
    """Create CSV file with headers"""

    print 'Creating CSV file at: {}...'.format(csv_path_file)

    #Set the headers for the file
    headers = ['RECORD_ID_temp', 'LATITUDE_WGS84_GEOINFO', 'LONGITUDE_WGS84_GEOINFO']

    #Create the CSV with headers
    with open(csv_path_file, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

    print 'Done with create_csv()\n'

    return

#-------------------------------------------------------------------------------

#                          FUNCTION: xml_to_csv()
def xml_to_csv(xml_path_file, csv_path_file):
    """xml to csv"""

    print 'Parsing xml to csv...'
    # Get connection to the xml file
    xml_doc = minidom.parse(xml_path_file)
    item_list = xml_doc.getElementsByTagName('Details')

    print '  There are {} records in "{}" to write to the csv\n'.format(str(len(item_list)), xml_path_file)

    # Go through each item in 'Details' and get defined values
    for count, item in enumerate(item_list):

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

    print 'Done with xml_to_csv()\n'

    return

#-------------------------------------------------------------------------------

#                      FUNCTION: csv_to_table()
def csv_to_table(csv_path_file, fgdb_path, table_name):

    print 'Starting csv_to_table()'

    #---------------------------------------------------------------------------
    # Import csv to table
    in_rows  = csv_path_file
    out_path = fgdb_path
    out_name = table_name

    print '  Importing csv to FGDB: "{}\{}"...'.format(out_path, out_name)

    arcpy.TableToTable_conversion(in_rows, out_path, out_name)

    print '  Imported\n'

    #---------------------------------------------------------------------------
    # This import leaves any string field with 8000 characters in length!
    # Need to add a field, calculate the values to this new field and delete
    # the field that has the length of 8000

    # Add field
    in_table = fgdb_path + '\\' + table_name
    field_name = 'RECORD_ID'
    field_type = 'TEXT'
    field_length = 25

    print '  Adding field: "{}"'.format(field_name)

    arcpy.AddField_management (in_table, field_name, field_type, field_length)

    # Calculate new field to equal the RECORD_ID_temp
    expression = '!RECORD_ID_temp!'
    expression_typ = 'PYTHON_9.3'

    print '  Calculating field: "{}" so that it equals: "{}"'.format(field_name, expression)

    arcpy.CalculateField_management (in_table, field_name, expression, expression_typ)

    # Delete RECORD_ID_temp
    drop_field = 'RECORD_ID_temp'

    print '  Deleting field: "{}"'.format(drop_field)
    arcpy.DeleteField_management(in_table, drop_field)

    print '\nDone with csv_to_table()\n'

    return

#-------------------------------------------------------------------------------
def table_to_fc():
    pass

#-------------------------------------------------------------------------------
#****************************     RUN MAIN    **********************************
#-------------------------------------------------------------------------------


if __name__ == '__main__':
    main()
