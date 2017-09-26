#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     22/09/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():

    #---------------------------------------------------------------------------
    #                            Set variables

    # File with username and pwd
    cfgFile = r"P:\DPW_ScienceAndMonitoring\Scripts\DEV\DEV_branch\Control_Files\accounts.txt"
    cfgFile = r"U:\grue\Projects\Accounts\accounts.txt"

    name_of_FS = 'DPW_WP_SITES_DEV_VIEW_2'
    index_of_layer_in_FS = 0
    where_clause = "Site_Status = 'To Be Deleted'"
    fields_to_report = ['OBJECTID', 'StationID', 'Site_Status']
    #---------------------------------------------------------------------------
    #                          Start Calling Functions

    # Get Token
    token = Get_Token(cfgFile)

##    # Get OBJECTIDs
##    object_ids = Get_AGOL_Object_Ids_Where(name_of_FS, index_of_layer_in_FS, where_clause, token)
##
##    if len(object_ids) > 0:
##        # Report which object_ids are going to be deleted
##        Query_AGOL_Features(name_of_FS, index_of_layer_in_FS, object_ids, fields_to_report, token)
##
##        # Delete OBJECTIDs
##        Delete_AGOL_Features(name_of_FS, index_of_layer_in_FS, object_ids, token)
##
##    else:
##        print 'Nothing to delete'

    Unregister_AGOL_Replica_Ids(name_of_FS, token)

    print 'Finished with script'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                 FUNCTION:  Unregister AGOL Replica IDs

def Unregister_AGOL_Replica_Ids(name_of_FS, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      token (str): Obtained from the Get_Token().

    RETURNS:
      None

    FUNCTION:
      To be used to get a list of replicas for an AGOL Feature Service and then
      ask the user if they wish to unregister the replicas that were listed.
      This will primarily be used to be allowed to overwrite an existing FS that
      has replicas from other users who have not removed a map from Collector.
    """
    print '--------------------------------------------------------------------'
    print 'Starting Unregister_AGOL_Replica_Ids()'
    import urllib2, urllib, json

    #---------------------------------------------------------------------------
    #              Get list of Replicas for the Feature Service

    # Set the URLs
    list_replica_url     = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/{}/FeatureServer/replicas'.format(name_of_FS)
    query                = '?f=json&token={}'.format(token)
    get_replica_list_url = list_replica_url + query
    ##print get_replica_list_url

    # Get the replicas
    print '  Getting replicas for: {}'.format(name_of_FS)
    response = urllib2.urlopen(get_replica_list_url)
    replica_json_obj = json.load(response)
    ##print replica_json_obj

    if len(replica_json_obj) == 0:
        print '  No replicas for this feature service.'
    else:
        #-----------------------------------------------------------------------
        #               Print out the replica ID and username owner
        for replica in replica_json_obj:
            print '  Replica: {}'.format(replica['replicaID'])

            list_replica_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/arcgis/rest/services/{}/FeatureServer/replicas/{}'.format(name_of_FS, replica['replicaID'])
            query            = '?f=json&token={}'.format(token)
            replica_url      = list_replica_url + query
            response = urllib2.urlopen(replica_url)
            owner_json_obj = json.load(response)
            print '  Is owned by: {}\n'.format(owner_json_obj['replicaOwner'])

        #-----------------------------------------------------------------------
        #                      Unregister Replicas
        # Ask user if they want to unregister the replicas mentioned above
        unregister_replicas = raw_input('Do you want to unregister the above replicas? (y/n)')

        if unregister_replicas == 'y':
            for replica in replica_json_obj:
                print '  Unregistering replica: {}'.format(replica['replicaID'])
                unregister_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/unRegisterReplica?token={}'.format(name_of_FS, token)
                unregister_params = urllib.urlencode({'replicaID': replica['replicaID'], 'f':'json'})

                response = urllib2.urlopen(unregister_url, unregister_params)
                unregister_json_obj = json.load(response)
                print '    Success: {}'.format(unregister_json_obj['success'])

    print 'Finished Unregister_AGOL_Replica_Ids()'
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                 FUNCTION:  Query_AGOL_Feature
def Query_AGOL_Features(name_of_FS, index_of_layer_in_FS, object_ids, fields_to_report, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      object_ids (list of str): List of OBJECTID's that should be querried.
      fields_to_report (list of str): List of fields in the database that should
        be reported on.
      token (str): Obtained from the Get_Token().

    RETURNS:
      None

    FUNCTION:
      To print out a report using the OBJECTID list obtained from
      Get_AGOL_Object_Ids_Where() function.  Pass in a list of fields that you
      want reported and the script will print out the field and the fields value
      for each OBJECTID passed into this function.
    """
    print '--------------------------------------------------------------------'
    print 'Starting Query_AGOL_Features()'
    import urllib2, urllib, json


    # Turn the list of object_ids into one string with comma separated IDs,
    #   Then url encode it
    object_ids_str = ','.join(str(x) for x in object_ids)
    encoded_obj_ids = urllib.quote(object_ids_str)

    # Turn the list of required fields into one string with comma separations
    #   Then url encode it
    fields_to_report_str = ','.join(str(x) for x in fields_to_report)
    encoded_fields_to_rpt = urllib.quote(fields_to_report_str)

    print '  Querying Features in FS: "{}" and index "{}"'.format(name_of_FS, index_of_layer_in_FS)
    print '  OBJECTIDs to be queried: {}'.format(object_ids_str)
    print '  Fields to be reported on: {}'.format(fields_to_report_str)

    # Set URLs
    query_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/query'.format(name_of_FS, index_of_layer_in_FS)
    query = '?where=&objectIds={}&outFields={}&returnGeometry=false&f=json&token={}'.format(encoded_obj_ids,encoded_fields_to_rpt, token)
    get_report_url = query_url + query
    ##print get_report_url

    # Get the report data and print
    response = urllib2.urlopen(get_report_url)
    response_json_obj = json.load(response)
    ##print response_json_obj

    # Print out a report for each field for each feature in the object_ids list
    print '\n  Reporting:'
    for feature in (response_json_obj['features']):
        for field in fields_to_report:
            print '    {}: {}'.format(field, feature['attributes'][field])
        print ''

    print 'Finished Query_AGOL_Features()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                FUNCTION:    Delete AGOL Features

def Delete_AGOL_Features(name_of_FS, index_of_layer_in_FS, object_ids, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      object_ids (list of str): List of OBJECTID's that should be deleted.
      token (str): Obtained from the Get_Token().

    RETURNS:
      None

    FUNCTION:
      To Delete features on an AGOL Feature Service.
    """

    print '--------------------------------------------------------------------'
    print "Starting Delete_AGOL_Features()"
    import urllib2, urllib, json

    # Turn the list of object_ids into one string with comma separated IDs
    object_ids_str = ','.join(str(x) for x in object_ids)

    # Set URLs
    delete_url       = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/deleteFeatures?token={}'.format(name_of_FS, index_of_layer_in_FS, token)
    del_params       = urllib.urlencode({'objectIds': object_ids_str, 'f':'json'})


    # Delete the features
    print '  Deleting Features in FS: "{}" and index "{}"'.format(name_of_FS, index_of_layer_in_FS)
    print '  OBJECTIDs to be deleted: {}'.format(object_ids_str)
    ##print delete_url + del_params
    response  = urllib2.urlopen(delete_url, del_params)
    response_json_obj = json.load(response)
    ##print response_json_obj

    for result in response_json_obj['deleteResults']:
        ##print result
        print '    OBJECTID: {}'.format(result['objectId'])
        print '      Deleted? {}'.format(result['success'])

    print 'Finished Delete_AGOL_Features()\n'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                FUNCTION:    Get AGOL Object IDs Where

def Get_AGOL_Object_Ids_Where(name_of_FS, index_of_layer_in_FS, where_clause, token):
    """
    PARAMETERS:
      name_of_FS (str): The name of the Feature Service (do not include things
        like "services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services", just
        the name is needed.  i.e. "DPW_WP_SITES_DEV_VIEW".
      index_of_layer_in_FS (int): The index of the layer in the Feature Service.
        This will frequently be 0, but it could be a higer number if the FS has
        multiple layers in it.
      where_clause (str): Where clause.
      token (str): Obtained from the Get_Token()

    RETURNS:
      object_ids (list of str): List of OBJECTID's that satisfied the
      where_clause.

    FUNCTION:
      To get a list of the OBJECTID's of the features that satisfied the
      where clause.  This list will be the full list of all the records in the
      FS regardless of the number of the returned OBJECTID's or the max record
      count for the FS.

    NOTE: This function assumes that you have already gotten a token from the
    Get_Token() and are passing it to this function via the 'token' variable.
    """

    print '--------------------------------------------------------------------'
    print "Starting Get_AGOL_Object_Ids_Where()"
    import urllib2, urllib, json

    # Create empty list to hold the OBJECTID's that satisfy the where clause
    object_ids = []

    # Encode the where_clause so it is readable by URL protocol (ie %27 = ' in URL).
    # visit http://meyerweb.com/eric/tools/dencoder to test URL encoding.
    where_encoded = urllib.quote(where_clause)

    # Set URLs
    query_url = r'https://services1.arcgis.com/1vIhDJwtG5eNmiqX/ArcGIS/rest/services/{}/FeatureServer/{}/query'.format(name_of_FS, index_of_layer_in_FS)
    query = '?where={}&returnIdsOnly=true&f=json&token={}'.format(where_encoded, token)
    get_object_id_url = query_url + query

    # Get the list of OBJECTID's that satisfied the where_clause

    print '  Getting list of OBJECTID\'s that satisfied the where clause for layer:\n    {}'.format(query_url)
    print '  Where clause: "{}"'.format(where_clause)
    response = urllib2.urlopen(get_object_id_url)
    response_json_obj = json.load(response)
    object_ids = response_json_obj['objectIds']

    if len(object_ids) > 0:
        print '  There are "{}" features that satisfied the query.'.format(len(object_ids))
        print '  OBJECTID\'s of those features:'
        for obj in object_ids:
            print '    {}'.format(obj)

    else:
        print '  No features satisfied the query.'

    print "Finished Get_AGOL_Object_Ids_Where()\n"

    return object_ids

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                       FUNCTION:    Get AGOL token

def Get_Token(cfgFile, gtURL="https://www.arcgis.com/sharing/rest/generateToken"):
    """
    PARAMETERS:
      cfgFile (str):
        Path to the .txt file that holds the user name and password of the
        account used to access the data.  This account must be in a group
        that has access to the online database.
      gtURL {str}: URL where ArcGIS generates tokens. OPTIONAL.

    VARS:
      token (str):
        a string 'password' from ArcGIS that will allow us to to access the
        online database.

    RETURNS:
      token (str): A long string that acts as an access code to AGOL servers.
        Used in later functions to gain access to our data.

    FUNCTION: Gets a token from AGOL that allows access to the AGOL data.
    """

    print '--------------------------------------------------------------------'
    print "Getting Token..."

    import ConfigParser, urllib, urllib2, json

    # Get the user name and password from the cfgFile
    configRMA = ConfigParser.ConfigParser()
    configRMA.read(cfgFile)
    usr = configRMA.get("mgrue","usr")
    pwd = configRMA.get("mgrue","pwd")

    # Create a dictionary of the user name, password, and 2 other keys
    gtValues = {'username' : usr, 'password' : pwd, 'referer' : 'http://www.arcgis.com', 'f' : 'json' }

    # Encode the dictionary so they are in URL format
    gtData = urllib.urlencode(gtValues)

    # Create a request object with the URL adn the URL formatted dictionary
    gtRequest = urllib2.Request(gtURL,gtData)

    # Store the response to the request
    gtResponse = urllib2.urlopen(gtRequest)

    # Store the response as a json object
    gtJson = json.load(gtResponse)

    # Store the token from the json object
    token = gtJson['token']
    ##print token  # For testing purposes

    print "Successfully retrieved token.\n"

    return token

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
