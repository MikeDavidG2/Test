import arcpy, datetime

date        = datetime.date.today() - datetime.timedelta(10) #yesterday
dateFormat  = date.strftime("%m/%d/%Y")
print dateFormat

##sdeConn     = r"D:\sde_maintenance\scripts\Database Connections\Atlantic Warehouse (sangis user).sde"
sdeConn     = r'Database Connections\AD@ATLANTIC@SDW.sde'

##table       = sdeConn + "\\SDE.SANGIS.LUEG_UPDATES"
table       = sdeConn + '\\SDW.PDS.LUEG_UPDATES'

fc_list     = ['MIKE_GRUE_TEST_DELETE_ME', 'MIKE_GRUE_TEST_DELETE_ME_1', 'MIKE_GRUE_TEST_DELETE_ME_2']
##fc          = 'MIKE_GRUE_TEST_DELETE_ME'

for fc in fc_list:
    try:
        print 'Updating UPDATE_DATE ({}) on "{}"'.format(str(dateFormat), fc)
        cur = arcpy.UpdateCursor(table,"\"LAYER_NAME\" = '" + fc + "'")
        row = cur.next()
        while row:
            print row.UPDATE_DATE
            row.UPDATE_DATE = dateFormat
            print row.UPDATE_DATE
            cur.updateRow(row)
            row = cur.next()
        del cur # Need to delete the cursor in order for changes to be 'saved'

    except Exception as e:
        errors = True
        print '*** ERROR with updating date ***'
        print str(e)

print 'DONE'