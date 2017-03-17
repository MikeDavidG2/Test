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

#-------------------------------------------------------------------------------
#                              FUNCTION: main()

def main():

    #                           User, Set Variables:

    # main working folder
    working_folder = r'U:\grue\Projects\GaryProjects'

    # XML file to read
    xml_file = working_folder + r"\DEH_HMD_FIRST_RESPONDER_INDEX_sample ORIG.xml"
    ##xml_file = working_folder + r"\DEH_HMD_FIRST_RESPONDER_INDEX.xml"

    # Folder CSV file will be saved to
    csv_folder = working_folder + '\csv_files'
    csv_file_name = 'temp_csv.csv'

    # FGDB the CSV will be imported to
    fgdb_path = working_folder + r'\test.gdb'
    table_name = 'csv_to_table'

    #---------------------------------------------------------------------------
    #             Set variables that shouldn't have to be changed

    csv_path_file = csv_folder + '\\' + csv_file_name


    #---------------------------------------------------------------------------
    #                       Start running processes

    # Get connection to and READ the XML file
    xml_doc = minidom.parse(xml_file)
    item_list = xml_doc.getElementsByTagName('Details')

    # Number of records to process per loop
    num_rec_per_loop = 3

    # Get the number of loops needed to process whole XML (round up with math.ceil)
    list_len = len(item_list)
    num_loops_needed = math.ceil(list_len / float(num_rec_per_loop))  # Need num_rec_per_loop to be a float

    print ('There are {} records in "{}"\n  With {} records per loop, we need {} loops.'.format(str(list_len), xml_file, str(num_rec_per_loop), str(num_loops_needed)))

    # Start looping here
    num_loops_done = 0
    while num_loops_done < num_loops_needed:
        print 'Performing loop #: {}'.format(num_loops_done)

        # Create CSV
        create_csv(csv_path_file)

        # Send part of XML to CSV


        # Import CSV to table in FGDB


        # Delete CSV and table_temp


        # Increment num_loops_done
        num_loops_done += 1

    # Turn table_master into a FC


#-------------------------------------------------------------------------------
#********************    START CALLING FUNCTIONS    ****************************
#-------------------------------------------------------------------------------

#                        FUNCTION: create_csv()
def create_csv(csv_path_file):
    """Create CSV file with headers"""

    print '  Creating CSV file '.format(csv_path_file)

    #Set the headers for the file
    headers = ['RECORD_ID_temp', 'LATITUDE_WGS84_GEOINFO', 'LONGITUDE_WGS84_GEOINFO']

    #Create the CSV with headers
    with open(csv_path_file, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)

    return

#-------------------------------------------------------------------------------

#                        FUNCTION: XML to CSV
def xml_to_csv():
    pass

    return

#-------------------------------------------------------------------------------

#                        FUNCTION: CSV to Table
def csv_to_table():
    pass

    return

#-------------------------------------------------------------------------------

#                        FUNCTION: Delete Files
def delete_files():
    pass

    return


#-------------------------------------------------------------------------------
#****************************     RUN MAIN    **********************************
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
