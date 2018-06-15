#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     11/04/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import time, arcpy

def main():
    #---------------------------------------------------------------------------
    # Get an extract of all parcels that intersect with the DA Reports
    parcels_all          = r'Database Connections\AD@ATLANTIC@SDE.sde\SDE.SANGIS.PARCELS_ALL'
    orig_DA_reports_fc   = r'P:\Damage_Assessment_GIS\Fire_Damage_Assessment\DEV\Data\DA_Fire_From_AGOL.gdb\DA_Fire_from_AGOL_2018_04_09__13_38_22'
    parcels_extract_path = r'P:\Damage_Assessment_GIS\Fire_Damage_Assessment\DEV\Data\DA_Fire_Processing.gdb\Parcel_All_Int_DA_Reports'

    try:
        print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        Extract_Parcels(parcels_all, orig_DA_reports_fc, parcels_extract_path)
        print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    except Exception as e:
        success = False
        print '\n*** ERROR with Extract_Parcels() ***'
        print str(e)


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                         FUNCTION: Extract Parcels
def Extract_Parcels(parcels_all, related_fc, parcels_int_related_fc):
    """
    PARAMETERS:
      parcels_all (str): Full path to the PARCELS_ALL FC.  This should be an SDE
        FC.

      related_fc (str):  Full path to a FC that will be used to select parcels
        that intersect features in this FC.

      parcels_int_related_fc (str):  Full path to an EXISTING FC that will contain
        the selected parcels.

    RETURNS:
      None

    FUNCTION:
      To select the parcels that intersect the 'related_fc' features and then
      appending the selected parcels into the the 'parcels_int_related_fc'.

      This function is usually used to speed up other geoprocessing tasks that
      may be performed on a parcels database.

      NOTE: This function deletes the existing features in the
        'parcels_int_related_fc' before appending the selected parcels so we get
        a 'fresh' FC each run of the script AND there is no schema lock to worry
        about.
    """

    print '--------------------------------------------------------------------'
    print 'Starting Extract_Parcels()'

    print '  PARCELS_ALL FC path:\n    {}'.format(parcels_all)
    print '  Related FC used to select parcels:\n    {}\n'.format(related_fc)

    # Delete the existing features
    print '  Deleting the old existing parcels at:\n    {}'.format(parcels_int_related_fc)
    arcpy.DeleteFeatures_management(parcels_int_related_fc)

    # Make a feature layer out of the PARCELS_ALL FC
    where_clause = "SITUS_JURIS = 'CN'"
    arcpy.MakeFeatureLayer_management(parcels_all, 'par_all_lyr', where_clause)

    # Make a feature layer out of the related_fc
    arcpy.MakeFeatureLayer_management(related_fc, 'related_fc_lyr')

    # Select Parcels that intersect with the DA Reports
    print '\n  Selecting parcels that intersect with the DA Reports'
    arcpy.SelectLayerByLocation_management('par_all_lyr', 'INTERSECT', related_fc)

    # Get count of selected parcels
    count = Get_Count_Selected('par_all_lyr')
    print '  There are: "{}" selected parcels\n'.format(count)

    # Export selected parcels
    if (count != 0):

        # Append the newly selected features
        print '  Appending the selected parcels to:\n    {}'.format(parcels_int_related_fc)
        arcpy.Append_management('par_all_lyr', parcels_int_related_fc, 'NO_TEST')

    else:
        print '*** WARNING! There were no selected parcels. ***'
        print '  Please find out why there were no selected parcels.'
        print '  Script still allowed to run w/o an error flag.'

    print 'Finished Extract_Parcels()\n'

    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                        FUNCTION Get_Count_Selected()
def Get_Count_Selected(lyr):
    """
    PARAMETERS:
      lyr (lyr): The layer that should have a selection on it that we want to test.

    RETURNS:
      count_selected (int): The number of selected records in the lyr

    FUNCTION:
      To get the count of the number of selected records in the lyr.
    """

    ##print 'Starting Get_Count()...'

    # See if there are any selected records
    desc = arcpy.Describe(lyr)

    if desc.fidSet: # True if there are selected records
        result = arcpy.GetCount_management(lyr)
        count_selected = int(result.getOutput(0))

    # If there weren't any selected records
    else:
        count_selected = 0

    ##print '  Count of Selected: {}'.format(str(count_selected))

    ##print 'Finished Get_Count()\n'

    return count_selected


if __name__ == '__main__':
    main()
