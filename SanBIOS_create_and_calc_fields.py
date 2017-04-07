#-------------------------------------------------------------------------------
# Name:        module1

"""Purpose:
    To create the fields that are needed in SDE
    Join the tables that act as domains
    Calculate the new fields
    Remove the joins
    Append the data to SDW
    Delete the new fields now that they are no longer needed
"""
#
# Author:      mgrue
#
# Created:     07/04/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# TODO: document this script
# TODO: get the polygons working on this script too
# TODO: put this script in the SanBIOS folder

import arcpy, os
arcpy.env.overwriteOutput = True

def main():

    # Set variables
    sanbios_fgdb     = r'P:\SanBIOS\Geodatabase\SANBIOS.gdb'
    sanbios_pts_cn   = sanbios_fgdb + '\\' + r'observations\SANBIOS_PTS_CN'



    field_list   = ['MASTER_LAT', 'MASTER_COM', 'STATUS', 'DEPTNAME', 'LIFEFORM', 'ORIGINDESC', 'PNAME', 'SITEQUALDE', 'SOURCE_NAM']

    # Create fields
    ##Add_Fields(sanbios_pts_cn, field_list)

    # Perform join and calc fields
    Join_Calc_Fields(sanbios_pts_cn, sanbios_fgdb)
#-------------------------------------------------------------------------------

def Add_Fields(input_table, field_list):

    print 'Starting Add_Fields()'


    for field in field_list:
        in_table          = input_table
        field_name        = field
        field_type        = 'TEXT'
        field_precision   = ''
        field_scale       = ''
        field_length      = 255
        field_alias       = ''
        field_is_nullable = ''
        field_is_required = ''
        field_domain      = ''

        try:
            print '  Adding field: ' + field
            arcpy.AddField_management(in_table, field_name, field_type, field_precision,
                                  field_scale, field_length, field_alias,
                                  field_is_nullable, field_is_required, field_domain)
        except:
            print '  Couln\'t add field: ' + field

    print 'Finished Add_Fields()'

#-------------------------------------------------------------------------------

def Join_Calc_Fields(master_table, sanbios_fgdb):

    # Define tables to join to master_table
    departments_tbl  = sanbios_fgdb + '\\' + r'Departments'
    life_form_tbl    = sanbios_fgdb + '\\' + r'LifeForm'
    origin_tbl       = sanbios_fgdb + '\\' + r'Origin'
    precision_tbl    = sanbios_fgdb + '\\' + r'Precision'
    site_quality_tbl = sanbios_fgdb + '\\' + r'SiteQuality'
    source_tbl       = sanbios_fgdb + '\\' + r'Source'
    species_tbl      = sanbios_fgdb + '\\' + r'Species'

    tables_list = [departments_tbl, life_form_tbl, origin_tbl, precision_tbl,
                   site_quality_tbl, source_tbl, species_tbl]

    #---------------------------------------------------------------------------
    # Make layers for all tables
    for table in tables_list:
        view_name = os.path.basename(table) + '_view'
        print '  Making table view from table: ' + table
        print '    Named: ' + view_name

        arcpy.MakeTableView_management(table, view_name)

    # Make layer for master_table
    print '  Making feature layer from FC: ' + master_table
    master_table_lyr = 'master_table_lyr'
    print '    Named: ' + master_table_lyr

    arcpy.MakeFeatureLayer_management(master_table, master_table_lyr)

    #---------------------------------------------------------------------------
    #                           Join tables to master_table
    # Constants for table joins
    in_layer_or_view = master_table_lyr
    join_type = 'KEEP_ALL'


    # Perform joins
    in_field   = 'DeptID'
    join_table = 'Departments_view'
    join_field = 'DeptID'
    print '  Joining: {} with: {} based on in_field: {} and join_field: {}'.format(in_layer_or_view, join_table, in_field, join_field)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)

    in_field   = 'LifeID'
    join_table = 'LifeForm_view'
    join_field = 'LifeID'
    print '  Joining: {} with: {} based on in_field: {} and join_field: {}'.format(in_layer_or_view, join_table, in_field, join_field)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)

    in_field   = 'OriginID'
    join_table = 'Origin_view'
    join_field = 'OriginID'
    print '  Joining: {} with: {} based on in_field: {} and join_field: {}'.format(in_layer_or_view, join_table, in_field, join_field)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)

    in_field   = 'PCode'
    join_table = 'Precision_view'
    join_field = 'PCode'
    print '  Joining: {} with: {} based on in_field: {} and join_field: {}'.format(in_layer_or_view, join_table, in_field, join_field)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)

    in_field   = 'SiteQualID'
    join_table = 'SiteQuality_view'
    join_field = 'SiteQualID'
    print '  Joining: {} with: {} based on in_field: {} and join_field: {}'.format(in_layer_or_view, join_table, in_field, join_field)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)

    in_field   = 'SourceID'
    join_table = 'Source_view'
    join_field = 'SourceID'
    print '  Joining: {} with: {} based on in_field: {} and join_field: {}'.format(in_layer_or_view, join_table, in_field, join_field)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)

    in_field   = 'spID'
    join_table = 'Species_view'
    join_field = 'spID'
    print '  Joining: {} with: {} based on in_field: {} and join_field: {}'.format(in_layer_or_view, join_table, in_field, join_field)
    arcpy.AddJoin_management(in_layer_or_view, in_field, join_table, join_field, join_type)

    #---------------------------------------------------------------------------
    #                      Perform field calculations

    for field in arcpy.ListFields(master_table_lyr):
        print field.name

    # Constants for calculations
    in_table        = master_table_lyr
    expression_type = 'PYTHON_9.3'
    code_block      = ''

    # Calculate fields
    field      = "SANBIOS_PTS_CN.DEPTNAME"
    expression = '!Departments.DeptName!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    field      = "SANBIOS_PTS_CN.LIFEFORM"
    expression = '!LifeForm.LifeForm!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    field      = "SANBIOS_PTS_CN.ORIGINDESC"
    expression = '!Origin.OriginDesc!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    field      = "SANBIOS_PTS_CN.PNAME"
    expression = '!Precision.PName!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    field      = "SANBIOS_PTS_CN.SITEQUALDE"
    expression = '!SiteQuality.SiteQualDe!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    field      = "SANBIOS_PTS_CN.SOURCE_NAM"
    expression = '!Source.source_nam!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    field      = "SANBIOS_PTS_CN.MASTER_LAT"
    expression = '!Species.master_lat!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    field      = "SANBIOS_PTS_CN.MASTER_COM"
    expression = '!Species.master_com!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

    # TODO: check to make sure this last calculation is performing as expected
    field      = "SANBIOS_PTS_CN.STATUS"
    expression = '!Species.Status!'
    print 'Calculating field: "{}" in table: "{}" equal to: "{}"'.format(field, in_table, expression)
    arcpy.CalculateField_management(in_table, field, expression, expression_type, code_block)

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
