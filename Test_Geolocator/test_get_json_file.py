#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     30/03/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import arcpy, urllib, urllib2, json

def main():

##    gtURL       = "https://www.arcgis.com/sharing/rest/generateToken"
##
##    # Create a dictionary of the user name, password, and 2 other keys
##    gtValues = {'username' : 'mgrue_pds', 'password' : 'LOGA7407)', 'referer' : 'http://www.arcgis.com', 'f' : 'json' }
##
##    # Encode the dictionary so they are in URL format
##    gtData = urllib.urlencode(gtValues)
##
##    # Create a request object with the URL adn the URL formatted dictionary
##    gtRequest = urllib2.Request(gtURL,gtData)
##
##    # Store the response to the request
##    gtResponse = urllib2.urlopen(gtRequest)
##
##    # Store the response as a json object
##    gtJson = json.load(gtResponse)
##
##    # Store the token from the json object
##    token = gtJson['token']
##    print token

    url = 'https://gis-public.co.san-diego.ca.us/arcgis/rest/services/Composite_Super_Locator/GeocodeServer/geocodeAddresses'
    url = 'https://gis-public.co.san-diego.ca.us/arcgis/rest/services/Composite_Super_Locator/GeocodeServer?f=pjson'
    ##url = 'http://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer?f=pjson'
    ##url = 'http://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/geocodeAddresses'
    query = """?addresses={"records":[{"attributes":{"OBJECTID":1,"address":"5510 Overland Ave","Zipcode":"92123"}},{"attributes":{"OBJECTID":2,"Address":"9295 Farnham St.","zipcode":"92104"}}]}&outSR=&f=json"""

    ##fs_url = url + query
    print '  {}'.format(url)

    print 10
    request = urllib2.Request(url)

    print 20
    response = urllib2.urlopen(request)

    print 30
    json_obj = json.load(response)
    print json_obj

    json_string = json.dumps(json_obj)

    print 40
    test_connection = json_obj['currentVersion']

    print 'fs_url:  {}'.format(test_connection)

    # Save the file
    # NOTE: the file is saved to the 'current working directory' + 'JsonFileName'
    urllib.urlretrieve(json_string, 'test.json')

    # TODO.  I've left off here that I'm able to connect to the url, able to get access to the json response at the test_connection variable
    # but I'm not able to download the resulting json file to disk.

##    fs = arcpy.FeatureSet()
##
##    try:
##        fs.load(json_obj)
##    except Exception as e:
##        print str(e)


if __name__ == '__main__':
    main()
