#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     24/10/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import arcpy
def main():
    try:
        sites_CURRENT = r'U:\yakos\hep_A\PROD\Environment_B\Data\Homeless_Activity_CURRENT.gdb\Sites'
        visits_CURRENT = r'U:\yakos\hep_A\PROD\Environment_B\Data\Homeless_Activity_CURRENT.gdb\Visits'

# TODO: order the below search cursor in ascending order for each site number

        with arcpy.da.SearchCursor(sites_CURRENT, ['Site_Number', 'Site_Status_Collector', 'Cleanup_Recommended_Collector']) as sites_search_cur:
            for row in sites_search_cur:
                site_num_col            = row[0]
                site_stat_col           = row[1]
                cleanup_rec_col         = row[2]
                print '  Site Number     : {}'.format(site_num_col)
                print '       Status     : {}'.format(site_stat_col)
                print '       Cleanup Rec: {}\n'.format(cleanup_rec_col)

    except Exception as e:
        print 'ERROR'
        print str(e)

if __name__ == '__main__':
    main()
