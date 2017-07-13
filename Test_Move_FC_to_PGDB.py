

import arcpy
arcpy.env.overwriteOutput = True

master_table = r'X:\month\Test_FGDB.gdb\Field_Data'
to_update_table = r'X:\month\Test_PGDB.mdb\Field_Data'

print 'Deleting rows'
arcpy.DeleteRows_management(to_update_table)

print 'Copying rows'
arcpy.CopyRows_management(master_table, to_update_table)
