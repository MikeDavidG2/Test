##import xml.etree.ElementTree
##
xml_file = r"U:\grue\Projects\GaryProjects\DEH_HMD_FIRST_RESPONDER_INDEX_sample ORIG.xml"
##xml_obj = xml.etree.ElementTree.parse(xml_file).getroot()
##
##print 10
##for detail in xml_obj.findall('Details'):
##    print 20
##    print detail.get('RECORD_ID')
##
##


from xml.dom import minidom
xml_doc = minidom.parse(xml_file)
item_list = xml_doc.getElementsByTagName('Details')
print 'There are {} values'.format(str(len(item_list)))

for item in item_list:
    print item.attributes['RECORD_ID'].value