# Import system modules
import arcpy
import ConfigParser
import json
import logging
import os
import requests
import sys
import time
import urllib
import urllib2
from xml.etree import ElementTree as ET

startTime  = str(time.strftime("%H:%M:%S",time.localtime()))
path       = r"D:\OES"
agolFile   = os.path.join(path,"config","agol.ini")
#logFileDir = os.path.join(path,"logs")

class AGOLHandler(object):    
    
    def __init__(self, username, password, serviceName):
        self.username = username
        self.password = password
        self.serviceName = serviceName
        self.token, self.http = self.getToken(username, password)
        self.itemID = self.findItem("Feature Service")
        self.SDitemID = self.findItem("Service Definition")
        
    def getToken(self, username, password, exp=60):
        
        referer = "http://www.arcgis.com/"
        query_dict = {'username': username,
                      'password': password,
                      'expiration': str(exp),
                      'client': 'referer',
                      'referer': referer,
                      'f': 'json'}   
        
        query_string = urllib.urlencode(query_dict)
        url = "https://www.arcgis.com/sharing/rest/generateToken"
        
        token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
        
        if "token" not in token:
            log.error(token['error'])
            sys.exit()
        else: 
            httpPrefix = "http://www.arcgis.com/sharing/rest"
            if token['ssl'] == True:
                httpPrefix = "https://www.arcgis.com/sharing/rest"
                
            return token['token'], httpPrefix
            
    def findItem(self, findType):
        #
        # Find the itemID of whats being updated
        #        
        searchURL = self.http + "/search"
        
        query_dict = {'f': 'json',
                      'token': self.token,
                      'q': "title:\""+ self.serviceName + "\"AND owner:\"" + self.username + "\" AND type:\"" + findType + "\""}    
        
        jsonResponse = sendAGOLReq(searchURL, query_dict)
        
        if jsonResponse['total'] == 0:
            log.error("Could not find a service to update. Check the service name in the update_public_features.ini")
            sys.exit()
        else:
            log.info(("     {}: {}").format(findType, jsonResponse['results'][0]["id"])) 
        
        return jsonResponse['results'][0]["id"]
            

def urlopen(url, data=None):
    # monkey-patch URLOPEN
    referer = "http://www.arcgis.com/"
    req = urllib2.Request(url)
    req.add_header('Referer', referer)

    if data:
        response = urllib2.urlopen(req, data)
    else:
        response = urllib2.urlopen(req)

    return response


def makeSD(MXD, serviceName, tempDir, outputSD, maxRecords):
    #
    # create a draft SD and modify the properties to overwrite an existing FS
    #    
    
    arcpy.env.overwriteOutput = True
    # All paths are built by joining names to the tempPath
    SDdraft = os.path.join(tempDir, "tempdraft.sddraft")
    newSDdraft = os.path.join(tempDir, "updatedDraft.sddraft")    
     
    arcpy.mapping.CreateMapSDDraft(MXD, SDdraft, serviceName, "MY_HOSTED_SERVICES")
    
    # Read the contents of the original SDDraft into an xml parser
    doc = ET.parse(SDdraft)  
    
    root_elem = doc.getroot()
    if root_elem.tag != "SVCManifest":
        raise ValueError("Root tag is incorrect. Is {} a .sddraft file?".format(SDDraft))
    
    
    # Change service type from map service to feature service
    for config in doc.findall("./Configurations/SVCConfiguration/TypeName"):
        if config.text == "MapServer":
            config.text = "FeatureServer"
    
    #Turn off caching
    for prop in doc.findall("./Configurations/SVCConfiguration/Definition/" +
                                "ConfigurationProperties/PropertyArray/" +
                                "PropertySetProperty"):
        if prop.find("Key").text == 'isCached':
            prop.find("Value").text = "false"
        if prop.find("Key").text == 'maxRecordCount':
            prop.find("Value").text = maxRecords
    
    # Turn on feature access capabilities
    for prop in doc.findall("./Configurations/SVCConfiguration/Definition/Info/PropertyArray/PropertySetProperty"):
        if prop.find("Key").text == 'WebCapabilities':
            prop.find("Value").text = "Query"

    # Add the namespaces which get stripped, back into the .SD    
    root_elem.attrib["xmlns:typens"] = 'http://www.esri.com/schemas/ArcGIS/10.1'
    root_elem.attrib["xmlns:xs"] ='http://www.w3.org/2001/XMLSchema'

    # Write the new draft to disk
    with open(newSDdraft, 'w') as f:
        doc.write(f, 'utf-8')
        
    # Analyze the service
    analysis = arcpy.mapping.AnalyzeForSD(newSDdraft)
     
    if analysis['errors'] == {}:
        # Stage the service
        arcpy.StageService_server(newSDdraft, outputSD)
        log.info("     Created {}".format(outputSD))
            
    else:
        # If the sddraft analysis contained errors, display them and quit.
        log.error(analysis['errors'])
        sys.exit()
   
           
def upload(fileName, tags, description): 
    #
    # Overwrite the SD on AGOL with the new SD.
    # This method uses 3rd party module: requests
    #
    
    updateURL = agol.http+'/content/users/{}/items/{}/update'.format(agol.username, agol.SDitemID)
        
    filesUp = {"file": open(fileName, 'rb')}
    
    url = updateURL + "?f=json&token="+agol.token+ \
          "&filename="+fileName+ \
          "&type=Service Definition"\
          "&title="+agol.serviceName+ \
          "&tags="+tags+\
          "&description="+description
          
    response = requests.post(url, files=filesUp);
    itemPartJSON = json.loads(response.text)
    
    if "success" in itemPartJSON:
        itemPartID = itemPartJSON['id']
        log.info(("     Updated SD:   {}").format(itemPartID))
        return True
    else:
        log.error("sd file not uploaded. Check the errors and try again.")  
        log.error(itemPartJSON)
        sys.exit()        
    
    
def publish():
    #
    # Publish the existing SD on AGOL (it will be turned into a Feature Service)
    #
    
    publishURL = agol.http+'/content/users/{}/publish'.format(agol.username)
    
    query_dict = {'itemID': agol.SDitemID,
              'filetype': 'serviceDefinition',
              'overwrite': 'true',
              'f': 'json',
              'token': agol.token}    
    
    jsonResponse = sendAGOLReq(publishURL, query_dict)
            
    log.info("     Successfully updated service...")
    
    return jsonResponse['services'][0]['serviceItemId']
    

def enableSharing(newItemID, everyone, orgs, groups):
    #
    # Share an item with everyone, the organization and/or groups
    #
    shareURL = agol.http+'/content/users/{}/items/{}/share'.format(agol.username, newItemID)

    if groups == None:
        groups = ''
    
    query_dict = {'f': 'json',
                  'everyone' : everyone,
                  'org' : orgs,
                  'groups' : groups,
                  'token': agol.token}    
    
    jsonResponse = sendAGOLReq(shareURL, query_dict)
    
    log.info(("     Successfully shared {}...").format(jsonResponse['itemId']))  
    
    
    
def sendAGOLReq(URL, query_dict):
    #
    # Helper function which takes a URL and a dictionary and sends the request
    #
    
    query_string = urllib.urlencode(query_dict)    
    
    jsonResponse = urllib.urlopen(URL, urllib.urlencode(query_dict))
    jsonOuput = json.loads(jsonResponse.read())
    
    wordTest = ["success", "results", "services", "notSharedWith"]
    if any(word in jsonOuput for word in wordTest):
        return jsonOuput    
    else:
        log.error("failed:")
        log.error(jsonOuput)
        sys.exit()
        
    
if __name__ == "__main__":
    try:
        # Create log file
        log = logging.getLogger("update_public_features")
        logFileName = os.path.join(path,"logs","update_public_features_" + str(time.strftime("%Y%m%d_%H%M%S",time.localtime())) + ".txt")
        hdlr = logging.FileHandler(logFileName)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        hdlr.setFormatter(formatter)
        log.addHandler(hdlr)
        log.setLevel(logging.DEBUG)
        
        # Find and gather settings from the ini file
        settingsFile = os.path.join(path,"scripts","update_public_features.ini")
        
        if os.path.isfile(settingsFile):
            config = ConfigParser.ConfigParser()
            config.read(settingsFile)
        else:
            log.error("Make sure " + settingsFile + " exists and is valid.")
            sys.exit()

        if os.path.isfile(agolFile):
            config2 = ConfigParser.ConfigParser()
            config2.read(agolFile)
        else:
            log.error("Make sure " + agolFile + " exists and is valid.")
            sys.exit()
        
        # AGOL Credentials
        inputUsername = config2.get( 'AGOL', 'USER')
        inputPswd     = config2.get('AGOL', 'PASS')

        # FS values
        MXD         = config.get('FS_INFO', 'MXD')
        MXD         = os.path.join(path,"maps",MXD)
        serviceName = config.get('FS_INFO', 'SERVICENAME')   
        tags        = config.get('FS_INFO', 'TAGS')
        description = config.get('FS_INFO', 'DESCRIPTION')
        maxRecords  = config.get('FS_INFO', 'MAXRECORDS')
        
        # Share FS to: everyone, org, groups
        shared   = config.get('FS_SHARE', 'SHARE')
        everyone = config.get('FS_SHARE', 'EVERYONE')
        orgs     = config.get('FS_SHARE', 'ORG')
        groups   = config.get('FS_SHARE', 'GROUPS')  #Groups are by ID. Multiple groups comma separated
        
##        logFileName = os.path.join(logFileDir,"ago_update_" + serviceName + "_" + str(time.strftime("%Y%m%d",time.localtime())) + ".txt")
##        old_output  = sys.stdout
##        logFile     = open(logFileName,"a")
##        sys.stdout  = logFile
        log.info("Feature Service " + serviceName + " publish process started (" + str(startTime) + ")")
          
        # create a temp directory under the script
        tempDir = os.path.join(path,"working",serviceName)
        if not os.path.isdir(tempDir):
            os.mkdir(tempDir)  
        finalSD = os.path.join(tempDir, serviceName + ".sd")
        
        #initialize AGOLHandler class
        agol = AGOLHandler(inputUsername, inputPswd, serviceName)
        
        # Turn map document into .SD file for uploading
        makeSD(MXD, serviceName, tempDir, finalSD, maxRecords)
        
        # overwrite the existing .SD on arcgis.com
        if upload(finalSD, tags, description):
            
            # publish the sd which was just uploaded
            newItemID = publish()
            
            # share the item
            if shared:
                enableSharing(newItemID, everyone, orgs, groups)
                
            log.info("Feature Service " + serviceName + " publish process complete (" + str(time.strftime("%H:%M:%S",time.localtime())) + ")")

##        # Close log file
##        sys.stdout = old_output
##        logFile.close()
##
##        print str(sys.argv[0]).upper(),"COMPLETE"
##        print "CHECK LOG FILE", logFileName.upper()

    except:
        log.error("RUNNING " + str(sys.argv[0]).upper())
        log.error("CHECK LOG FILE " + logFileName.upper())
        
        
        
    
