#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
"""

"""
#
# Notes:
"""
The below url is successful in receiving geolocated coordinates
https://gis-public.co.san-diego.ca.us/arcgis/rest/services/Composite_Super_Locator/GeocodeServer/geocodeAddresses?addresses={%22records%22:[{%22attributes%22:{%22OBJECTID%22:1,%22address%22:%223954%20Bancroft%20St.%22,%22Zipcode%22:%2292104%22}},{%22attributes%22:{%22OBJECTID%22:2,%22Address%22:%223954%20Bancroft%20St.%22,%22zipcode%22:%2292104%22}}]}&outSR=&f=pjson

Workflow:
    1)  Excel spreadsheet
    2)  Import into a FGDB as a table
    3)  Get list of info from table (street address, and zip)
    4)  Pass info to the geocoder located at:
        https://gis-public.co.san-diego.ca.us/arcgis/rest/services/Composite_Super_Locator/GeocodeServer
    5)  Structure query with a '?' following ...GeocodeServer then follow with the structure defined at:
        https://gis-public.co.san-diego.ca.us/arcgis/sdk/rest/index.html#/Geocode_Addresses/02ss00000040000000/
    6)  Download the resulting json file
    7)  Parse the downloaded file into a FGDB table
    8)  Make Event XY layer and save to disk as a FC

"""
# Author:      mgrue
#
# Created:     28/03/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Imports
import arcpy, os, xlrd

arcpy.env.overwriteOutput = True

def main():
    #---------------------------------------------------------------------------
    #                             Set variables
    working_folder = 'U:\grue\Scripts\GitHub\Test\Test_Geolocator'

    # Excel file
    excel_file     = 'Addresses.xlsx'
    excel_path    = os.path.join(working_folder, excel_file)

    # fgdb file
    fgdb_file     = 'Addresses.gdb'
    out_fgdb_path = os.path.join(working_folder, fgdb_file)

    #---------------------------------------------------------------------------
    #                       Start calling functions

    # Import excel file to fgdb
    Import_Excel(excel_path, out_fgdb_path)

    #
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                           DEFINE FUNCTIONS
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Import_Excel(excel_path, out_fgdb_path):
    """
    Documentation here
    """

    print 'Starting Import_Excel()'

    # Get list of sheets in excel file
    workbook = xlrd.open_workbook(excel_path)
    sheets = [sheet.name for sheet in workbook.sheets()]

    # For each sheet, import to the out_fgdb_path
    print ('  {} sheets found: {}'.format(len(sheets), ', '.join(sheets)))
    for sheet in sheets:

        # The out_table is based on the input excel file name then an
        # underscore (_) separator followed by the sheet name
        out_table = os.path.join(
            out_fgdb_path,
            arcpy.ValidateFieldName(
                "{}_{}".format(os.path.basename(excel_path), sheet),
                out_fgdb_path))

        print ('  Converting {} to {}'.format(sheet, out_table))

        # Perform conversion
        arcpy.ExcelToTable_conversion(excel_path, out_table, sheet)

        # Test to see if table has data, delete table if not
        result = arcpy.GetCount_management(out_table)
        count = int(result.getOutput(0))

        if count == 0:
            print '    There were no records in this table.  Deleting...'
            arcpy.Delete_management(out_table)
            print '    Deleted'

    print 'Completed Import_Excel() successfully.'





#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------

#  Call main()
if __name__ == '__main__':
    main()
