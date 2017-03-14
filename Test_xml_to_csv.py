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

from xml.dom import minidom

def main():
    xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX_sample ORIG.xml"

    # Folder CSV file will be saved to
    csv_folder = r'U:\grue\Projects\GaryProjects'

    # Send variables to function
    xml_to_csv(xml_file, csv_folder)


#-------------------------------------------------------------------------------
def xml_to_csv(xml_file, csv_folder):

    # Get connection to the xml file
    xml_doc = minidom.parse(xml_file)
    item_list = xml_doc.getElementsByTagName('Details')

    print 'There are {} records in {}\n'.format(str(len(item_list)), xml_file)

    # Create empty lists
    record_ids  = []
    lat_wgs84s  = []
    long_wgs84s = []

    # Go through each item in 'Details' and get defined values
    for item in item_list:

        # Get value for each 'Details' row
        record_id  = item.attributes['RECORD_ID'].value
        lat_wgs84  = item.attributes['LATITUDE_WGS84_GEOINFO'].value
        long_wgs84 = item.attributes['LONGITUDE_WGS84_GEOINFO'].value

        # Append each value to the respective list
        record_ids.append(record_id)
        lat_wgs84s.append(lat_wgs84)
        long_wgs84s.append(long_wgs84)

    # Print out the info
    for count in range(len(record_ids)):
        print 'Record ID:  {rec_id}\nLatitude:    {lat}\nLongitude:  {lon}\n'.format(rec_id=record_ids[count], lat=lat_wgs84s[count], lon=long_wgs84s[count])



#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
