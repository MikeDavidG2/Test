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


def main():
    #---------------------------------------------------------------------------
    #                             Set variables


    #---------------------------------------------------------------------------
    #                       Start calling functions



    #---------------------------------------------------------------------------
    #                           DEFINE FUNCTIONS
    #---------------------------------------------------------------------------





#-------------------------------------------------------------------------------
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#-------------------------------------------------------------------------------

#  Call main()
if __name__ == '__main__':
    main()
