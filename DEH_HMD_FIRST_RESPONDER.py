#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
"""This script takes an xml file from the DEH_HMD_FIRST_RESPONDER process and
1)  Creates a csv with all of the xml keys as column headers.
2)  Parses the xml attributes to their respective columns.
3)  Imports the csv to a FGDB table.
4)  Turns the table into a FC using the X and Y fields in the table.

Folder structure this script expects:
    ...\working_folder\
           \csv_files\
           \log_files\
           \scripts\     (including the .bat file)
           \FGDB\
           \xml_files\

This script should be called from a .bat file that passes a parameter to the
variable "xml_to_csv_OR_csv_to_fc" which is used to control which functions are
called.  This was needed because Python fails if it is asked to read the xml
file and import the csv into a FGDB during the same compiled run.  The .bat
file can call this script and pass the string 'xml_to_csv' for the first run
and then call this script again and pass the string 'csv_to_fc' to finish the
process.
"""
# TODO:        Document this script
# TODO:        Make print statements into a log file
# TODO:        Error handling
# Author:      mgrue
#
# Created:     17/03/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
import csv, arcpy, time, math, os
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
    ##xml_file_name   = r'\DEH_HMD_FIRST_RESPONDER_INDEX_sample ORIG.xml' # For testing
    xml_file_name   = r"\DEH_HMD_FIRST_RESPONDER_INDEX.xml" # The FULL dataset
    xml_path_file   = xml_folder + '\\' + xml_file_name

    # CSV file to be saved
    csv_folder    = working_folder + '\csv_files'
    csv_file_name = 'temp_csv.csv'
    csv_path_file = csv_folder + '\\' + csv_file_name

    # FGDB the CSV will be imported to
    fgdb_path  = working_folder + r'\test.gdb'
    table_name = 'csv_to_table'
    fc_name    = 'DEH_HMD_FIRST_RESPONDER'

    #---------------------------------------------------------------------------
    # Below are variables used with the batch file to control which functions are called

    # Set defaults for which functions are called.  None will be called unless
    # the batch file passes one of the two correct strings ('xml_to_csv' or 'csv_to_fc')
    run_create_csv   = False
    run_xml_to_csv   = False
    run_csv_to_table = False
    run_table_to_fc  = False

    # Use parameter from batch file calling this script to drive which functions are called
    xml_to_csv_OR_csv_to_fc = arcpy.GetParameterAsText(0) ##or 'csv_to_fc' uncomment to test specific functions

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
        details_list, full_key_list = create_csv(xml_path_file, csv_path_file)

    # Read xml and parse to csv file
    if run_xml_to_csv:
        xml_to_csv(xml_path_file, csv_path_file, details_list, full_key_list)

    # Import csv file
    if run_csv_to_table:
        csv_to_table(csv_path_file, fgdb_path, table_name)

    # Turn table into a Feature Class
    if run_table_to_fc:
        table_to_fc(fgdb_path, table_name, fc_name)


    print 'FINISHED with DEH_HMD_FIRST_RESPONDER.py!'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#********************    START DEFINING FUNCTIONS    ***************************
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

#                        FUNCTION: create_csv()
def create_csv(xml_path_file, csv_path_file):
    """Create CSV file with headers"""

    print 'Creating CSV file at: {}...'.format(csv_path_file)


    # Get connection to the xml file
    xml_doc = minidom.parse(xml_path_file)
    details_list = xml_doc.getElementsByTagName('Details')

    # Each detauls element may have different keys so cycle through the elements
    # to get a list of headers from the elements
    full_key_list = []
    for count in range (len(details_list)):
        detail = details_list[count]
        keys = detail.attributes.keys()

        for key in keys:
            if key not in full_key_list:
                full_key_list.append(key)

    # Alphabetize list
    full_key_list.sort()

    print '  Num of keys from xml: {}\n  List of keys from xml below'.format(str(len(full_key_list)))
    print full_key_list

    #Set the headers for the file
    headers = full_key_list

    #Create the CSV with headers
    with open(csv_path_file, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

    print 'Done with create_csv()\n'

    return details_list, full_key_list

#-------------------------------------------------------------------------------

#                          FUNCTION: xml_to_csv()
def xml_to_csv(xml_path_file, csv_path_file, details_list, full_key_list):
    """xml to csv"""

    print 'Parsing xml to csv...'

    print '  There are {} records in: {}\n  to write to the csv at: {}'.format(str(len(details_list)), xml_path_file, csv_path_file)

    #---------------------------------------------------------------------------
    # Go through each 'Details' element get and write the value for each key
    for count, detail in enumerate(details_list):
        row_info = []

        # Print status for every 1000 elements written
        if (count % 1000 == 0):
            print '  Writing: {} of {}'.format(str(count), str(len(details_list)))

        #-----------------------------------------------------------------------
        # Go through each key and get attribute values for the specific element
        for key in full_key_list:

            # Use try / except to catch the exception
            # if the element does not have a specific key.
            try:
                value = detail.attributes[key].value
            except:
                value = 'Null'

            ##print '  Key: ' + key
            ##print '  Value: ' + str(value)

            # Use try / except to catch if there is a non ascii character in the
            # xml.  Remove non-ascii characters and replace with a '?' so that the
            # value can be written to the csv without failure.
            try:
                value.encode('ascii')

            except UnicodeEncodeError:
                print '  \nUnicode Decode Error at record: {} for: {}\n    Removing non-ascii characters'.format(str(count + 1), value.encode('ascii', errors='ignore'))
                value = ''.join([c if ord(c) < 128 else '?' for c in value])
                print '    New value = {}\n'.format(value)

            row_info.append(value)

        #-----------------------------------------------------------------------
        # Set list of values from row_info into csv file for the specific element
        with open(csv_path_file, 'ab') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(row_info)
            del row_info

    # Loop back to get the next detail element in the details_list

    print 'Done with xml_to_csv()\n'

    return

#-------------------------------------------------------------------------------

#                      FUNCTION: csv_to_table()
def csv_to_table(csv_path_file, fgdb_path, table_name):

    print 'Starting csv_to_table()'

    #---------------------------------------------------------------------------
    # Create the FGDB if it does not exist
    if not os.path.exists(fgdb_path):

        # split full path into folder and FGDB name
        out_folder_path, out_name = os.path.split(fgdb_path)

        arcpy.CreateFileGDB_management(out_folder_path, out_name)
    #---------------------------------------------------------------------------
    # Import csv to table
    in_rows  = csv_path_file
    out_path = fgdb_path
    out_name = table_name

    print '  Importing csv to FGDB: "{}\{}"...'.format(out_path, out_name)
    arcpy.TableToTable_conversion(in_rows, out_path, out_name)

    print '  Imported\n'

    # Below was a solution to get rid of the 8000 character long field in the
    # FGDB table, but it is complicated to do with many dozens of text fields
    # and it may not be needed anyways.
##    #---------------------------------------------------------------------------
##    # This import leaves any string field with 8000 characters in length!
##    # Need to add a field, calculate the values to this new field and delete
##    # the field that has the length of 8000
##
##    # Add field
##    in_table = fgdb_path + '\\' + table_name
##    field_name = 'RECORD_ID'
##    field_type = 'TEXT'
##    field_length = 25
##
##    print '  Adding field: "{}"'.format(field_name)
##    arcpy.AddField_management (in_table, field_name, field_type, field_length)
##
##    # Calculate new field to equal the RECORD_ID_temp
##    expression = '!RECORD_ID_temp!'
##    expression_typ = 'PYTHON_9.3'
##
##    print '  Calculating field: "{}" so that it equals: "{}"'.format(field_name, expression)
##    arcpy.CalculateField_management (in_table, field_name, expression, expression_typ)
##
##    # Delete RECORD_ID_temp
##    drop_field = 'RECORD_ID_temp'
##
##    print '  Deleting field: "{}"\n'.format(drop_field)
##    arcpy.DeleteField_management(in_table, drop_field)

    print 'Done with csv_to_table()\n'

    return

#-------------------------------------------------------------------------------
def table_to_fc(fgdb_path, table_name, fc_name):
    """Turn the Table into a Feature Class"""

    print 'Turning the Table into a Feature Class...'

    #---------------------------------------------------------------------------
    # Make an XY Event Layer from the Table
    table = fgdb_path + '\\' + table_name
    in_x_field = 'LONGITUDE_WGS84_GEOINFO'
    in_y_field = 'LATITUDE_WGS84_GEOINFO'
    out_layer  = fc_name + '_lyr'
    spatial_reference = arcpy.SpatialReference(4269)

    print '  Making XY Event Layer\n    From: "{}"\n    Named: "{}"\n'.format(table, out_layer)
    arcpy.MakeXYEventLayer_management (table, in_x_field, in_y_field, out_layer,
                                       spatial_reference)

    #---------------------------------------------------------------------------
    # Save the XY Event Layer to a Feature Class
    in_features = out_layer
    out_path    = fgdb_path
    out_name    = fc_name

    print '  Saving XY Event Layer "{}"\n    To: "{}"\n    Named: "{}"\n'.format(in_features, out_path, out_name)
    arcpy.FeatureClassToFeatureClass_conversion(in_features, out_path, out_name)

    print 'Done with table_to_fc()\n'

    return

#-------------------------------------------------------------------------------
#****************************     RUN MAIN    **********************************
#-------------------------------------------------------------------------------


if __name__ == '__main__':
    main()
