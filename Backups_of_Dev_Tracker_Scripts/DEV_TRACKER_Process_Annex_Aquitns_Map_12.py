#-------------------------------------------------------------------------------

# Purpose:
"""
TODO: More documentation here

"""
#
# Author:      mgrue
#
# Created:     24/07/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import datetime
import arcpy
import math
import os
import string
import sys
import time
##from datetime import datetime, date

arcpy.env.overwriteOutput = True

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Annex_Aquitns_Map_12'


    # Name of this script
    name_of_script = 'DEV_TRACKER_Process_{}.py'.format(shorthand_name)


    # Paths to folders and local FGDBs
    root_folder       = r'P:\20180510_development_tracker\DEV'
    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')
    data_folder       = '{}\{}'.format(root_folder, 'Data')
    wkg_fgdb          = '{}\{}'.format(data_folder, '{}.gdb'.format(shorthand_name))


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Misc variables
    success = True
    arcpy.env.workspace = wkg_fgdb

    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Main Function

    # Make sure the log file folder exists, create it if it does not
    if not os.path.exists(log_file_folder):
        print 'NOTICE, log file folder does not exist, creating it now\n'
        os.mkdir(log_file_folder)

##    # Turn all 'print' statements into a log-writing object
##    try:
##        log_file = r'{}\{}'.format(log_file_folder, name_of_script.split('.')[0])
##        orig_stdout, log_file_date, dt_to_append = Write_Print_To_Log(log_file, name_of_script)
##    except Exception as e:
##        success = False
##        print '\n*** ERROR with Write_Print_To_Log() ***'
##        print str(e)


    #---------------------------------------------------------------------------
    #          Delete any previously created SUCCESS/ERROR files
    #---------------------------------------------------------------------------
    try:
        if os.path.exists(success_file):
            print 'Deleting old file at:\n  {}\n'.format(success_file)
            os.remove(success_file)
        if os.path.exists(error_file):
            print 'Deleting old file at:\n  {}\n'.format(error_file)
            os.remove(error_file)

    except Exception as e:
        success = False
        print '\n*** ERROR with Deleting previously created SUCCESS/ERROR files ***'
        print str(e)

    #---------------------------------------------------------------------------
    #                      Create FGDBs if needed
    #---------------------------------------------------------------------------
##    if success == True:
##        try:
##
##            # Delete and create working FGDB
##            if arcpy.Exists(wkg_fgdb):
##                print 'Deleting FGDB at:\n  {}\n'.format(wkg_fgdb)
##                arcpy.Delete_management(wkg_fgdb)
##
##            if not arcpy.Exists(wkg_fgdb):
##                out_folder_path, out_name = os.path.split(wkg_fgdb)
##                print 'Creating FGDB at:\n  {}\n'.format(wkg_fgdb)
##                arcpy.CreateFileGDB_management(out_folder_path, out_name)
##
##        except Exception as e:
##            success = False
##            print '\n*** ERROR with Creating FGDBs ***'
##            print str(e)



    #===========================================================================
    #===========================================================================
    #                       START GARY'S MAIN FUNCTION
    #===========================================================================
    #===========================================================================

    # Set variables for GARY'S MAIN FUNCTION
    annexations  = "JUR_MUNICIPAL_ANNEX_HISTORY"
    curr_juris   = "JUR_MUNICIPAL"
    cpasg        = "CMTY_PLAN_CN"
    hexbin       = "GRID_HEX_060_ACRES"
    public       = "LAND_OWNERSHIP_SG"
    tribal       = "INDIAN_RESERVATIONS"
    pace         = "AG_PACE"
    wa_contract  = "AG_PRESERVE_CONTRACTS"
    os_easement  = "ESMT_OPEN_SPACE"
    model_out    = "PDS_HOUSING_MODEL_OUTPUT_2011"
    model_noFCI  = "PDS_HOUSING_MODEL_OUTPUT_2011_NO_FCI"
    sdepath      = os.path.join(root_folder,"Scripts","Connection_Files", 'AD@ATLANTIC@SDE.sde')  # MG
    outpath      = os.path.join(data_folder,"Annex_Aquitns_Map_12_Output.gdb")  # MG
    sde_prefix   = "SDE.SANGIS."
    adopted_date = '2011-08-03 00:00:00'


    # list of dataset name and the new field name in combined dataset (AOI)
    component_list = [
        (public,"AQUISITION"),
        (tribal,"RESERVATIONS"),
        (pace,"PACE"),
        (wa_contract,"WILLIAMSON_ACT"),
        (os_easement,"OPEN_SPACE"),
        (annexations,"ANNEXATIONS")]


##    #---------------------------------------------------------------------------
##    #                            Find Program Impact
##    #---------------------------------------------------------------------------
##    if success == True:
##        print('\n-------------------------------------------------------------')
##        print('Find Program Impact:\n')
##        try:
##            # Aquisitions by public agencies
##            program_name = public
##            data_query   = "OWN <> 42"  # Don't include Indian Reservations
##            program_impact(sdepath, sde_prefix, model_out, model_noFCI, cpasg, hexbin, component_list, program_name, data_query)
##
##            # Indian Reservation expansion
##            program_name = tribal
##            data_query   = ""
##            program_impact(sdepath, sde_prefix, model_out, model_noFCI, cpasg, hexbin, component_list, program_name, data_query)
##
##            # Purchase of Agricultural Conservation Easement (PACE)
##            program_name = pace
##            data_query   = "PACE_ENROLLED = 'Y'"
##            program_impact(sdepath, sde_prefix, model_out, model_noFCI, cpasg, hexbin, component_list, program_name, data_query)
##
##            # Williamson Act Contracts
##            program_name = wa_contract
##            data_query   = ""
##            program_impact(sdepath, sde_prefix, model_out, model_noFCI, cpasg, hexbin, component_list, program_name, data_query)
##
##            # Open Space Easements (only Open Space, Biological, and Conservation)
##            program_name = os_easement
##            data_query   = "SUB_TYPE in (1, 2, 4)"
##            program_impact(sdepath, sde_prefix, model_out, model_noFCI, cpasg, hexbin, component_list, program_name, data_query)
##
##            # Annexations
##            program_name = annexations
##            data_query   = "STATUS = 2 AND DATE_ > '{}'".format(adopted_date)
##            program_impact(sdepath, sde_prefix, model_out, model_noFCI, cpasg, hexbin, component_list, program_name, data_query)
##
##
##        except Exception as e:
##            success = False
##            print '\n*** ERROR with Find Program Impact ***'
##            print str(e)
##
##
##    #---------------------------------------------------------------------------
##    #                            Process Detachments
##    #---------------------------------------------------------------------------
##    if success == True:
##        print('\n-----------------------------------------------------------------')
##        print('Processing Detachments:')
##        try:
##            print(str(time.strftime("%H:%M:%S", time.localtime())) + " | Working on detachments")
##            arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + annexations),
##                                              "detach",
##                                              "\"STATUS\" = 3 AND \"DATE_\" > '{}'".format(adopted_date))
##            arcpy.management.MultipartToSinglepart("detach","detach_units1")
##            arcpy.management.Delete("detach")
##
##            arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + curr_juris),"uninc","\"CODE\" = 'CN'")
##            arcpy.management.MakeFeatureLayer("detach_units1","lyr")
##            arcpy.management.SelectLayerByLocation("lyr","HAVE_THEIR_CENTER_IN","uninc")
##            if int(arcpy.management.GetCount("lyr")[0]) > 0:
##                arcpy.management.CopyFeatures("lyr","detach_units")
##                arcpy.management.RepairGeometry("detach_units")
##                print("\n***************************************")
##                print("NOTICE - There are DETACHMENTS that have added to the unincorporated")
##                print("         area.  You need to determine what the General Plan designation(s).")
##                print("         what the General Plan designations.  The Housing Model must be run")
##                print("         to determine how many units that will be added to capacity.")
##                print("         Please review feature class " + str(os.path.join(arcpy.env.workspace,"detach_units")) + ".\n")
##            else:
##                print("             No detachments occurred")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("detach_units1")
##
##        except Exception as e:
##            success = False
##            print '\n*** ERROR with Processing Detachments ***'
##            print str(e)
##
##
##    #---------------------------------------------------------------------------
##    #                   Combine all component fcs into 1 output fc
##    #---------------------------------------------------------------------------
##    if success == True:
##        print('\n-------------------------------------------------------------')
##        print('Combine all component fcs into 1 output fc:')
##        try:
##            print(str(time.strftime("%H:%M:%S", time.localtime())) + " | Working on combining feature classes")
##            ulist = []
##            for nm in component_list:
##                ulist.append(nm[1])
##            arcpy.analysis.Union(ulist,"COMBO1")
##            arcpy.management.MakeFeatureLayer("COMBO1","lyr")
##            arcpy.management.AddField("lyr","FLAG_LOSS","SHORT")
##            arcpy.management.CalculateField("lyr","FLAG_LOSS","1")
##            arcpy.management.Delete("lyr")
##
##            arcpy.management.MakeFeatureLayer("COMBO1","lyr")
##            arcpy.management.Dissolve("lyr","COMBO2","FLAG_LOSS")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("COMBO1")
##
##            arcpy.management.RepairGeometry("COMBO2")
##            arcpy.management.MultipartToSinglepart("COMBO2","COMBO")
##            arcpy.management.RepairGeometry("COMBO")
##            arcpy.management.Delete("COMBO2")
##
##            # Constraints including FCI
##            print(str(time.strftime("%H:%M:%S", time.localtime())) + " | Working on combining with all constraints")
##            arcpy.management.MakeFeatureLayer("COMBO","lyr")
##            arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + model_out),"units","\"FUTURE_UNITS\" > 0")
##            arcpy.analysis.Intersect(["lyr","units"],"combo_units1")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("units")
##
##            arcpy.management.MakeFeatureLayer("combo_units1","lyr")
##            arcpy.management.RepairGeometry("lyr")
##            arcpy.management.MultipartToSinglepart("lyr","combo_units")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("combo_units1")
##            arcpy.management.RepairGeometry("combo_units")
##
##            arcpy.management.MakeFeatureLayer("combo_units","aoi")
##            arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + cpasg),"cpa")
##            arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + hexbin),"hex")
##            arcpy.analysis.Union(["aoi","cpa","hex"],"combo_units_reporting1")
##            arcpy.management.RepairGeometry("combo_units_reporting1")
##            arcpy.management.Delete("aoi")
##            arcpy.management.Delete("cpa")
##            arcpy.management.Delete("hex")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting1","lyr")
##            arcpy.management.MultipartToSinglepart("lyr","combo_units_reporting")
##            arcpy.management.RepairGeometry("combo_units_reporting")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("combo_units_reporting1")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting","lyr")
##            arcpy.management.CalculateField("lyr","ACRES","!Shape_Area! / 43560","PYTHON_9.3")
##            arcpy.management.CalculateField("lyr","FUTURE_UNITS","!EFFECTIVE_DENSITY! * !ACRES! * -1","PYTHON_9.3")
##            arcpy.management.Delete("lyr")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting","lyr","\"FUTURE_UNITS\" IS NULL")
##            arcpy.management.CalculateField("lyr","FUTURE_UNITS","0")
##            arcpy.management.Delete("lyr")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting","lyr")
##            arcpy.analysis.Frequency("lyr","total_units_cpasg",["CPASG_1","CPASG_LABE"],"FUTURE_UNITS")
##            arcpy.analysis.Frequency("lyr","total_units_hex60","HEXAGONID","FUTURE_UNITS")
##            arcpy.management.Delete("lyr")
##
##            arcpy.management.MakeTableView("total_units_cpasg","tv")
##            arcpy.management.AlterField("tv","FUTURE_UNITS","DELTA_FUTURE_UNITS","DELTA_FUTURE_UNITS")
##            arcpy.management.CalculateField("tv","DELTA_FUTURE_UNITS","!DELTA_FUTURE_UNITS!","PYTHON_9.3")
##            arcpy.management.DeleteField("tv","FREQUENCY")
##            arcpy.management.Delete("tv")
##
##            arcpy.management.MakeTableView("total_units_cpasg","tv","\"CPASG_1\" = 0")
##            arcpy.management.DeleteRows("tv")
##            arcpy.management.Delete("tv")
##
##            arcpy.management.MakeTableView("total_units_hex60","tv")
##            arcpy.management.AlterField("tv","FUTURE_UNITS","DELTA_FUTURE_UNITS","DELTA_FUTURE_UNITS")
##            arcpy.management.DeleteField("tv","FREQUENCY")
##            arcpy.management.Delete("tv")
##
##            arcpy.management.MakeTableView("total_units_hex60","tv","\"HEXAGONID\" = ''")
##            arcpy.management.DeleteRows("tv")
##            arcpy.management.Delete("tv")
##
##            # Constraints without FCI
##            print(str(time.strftime("%H:%M:%S", time.localtime())) + " | Working on removing FCI constraint")
##            arcpy.management.MakeFeatureLayer("COMBO","lyr")
##            arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + model_noFCI),"units","\"FUTURE_UNITS\" > 0")
##            arcpy.analysis.Intersect(["lyr","units"],"combo_units1")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("units")
##
##            arcpy.management.MakeFeatureLayer("combo_units1","lyr")
##            arcpy.management.RepairGeometry("lyr")
##            arcpy.management.MultipartToSinglepart("lyr","combo_units_noFCI")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("combo_units1")
##            arcpy.management.RepairGeometry("combo_units_noFCI")
##
##            arcpy.management.MakeFeatureLayer("combo_units_noFCI","aoi")
##            arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + cpasg),"cpa")
##            arcpy.analysis.Union(["aoi","cpa"],"combo_units_reporting1")
##            arcpy.management.RepairGeometry("combo_units_reporting1")
##            arcpy.management.Delete("aoi")
##            arcpy.management.Delete("cpa")
##            arcpy.management.Delete("hex")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting1","lyr")
##            arcpy.management.MultipartToSinglepart("lyr","combo_units_reporting_noFCI")
##            arcpy.management.RepairGeometry("combo_units_reporting_noFCI")
##            arcpy.management.Delete("lyr")
##            arcpy.management.Delete("combo_units_reporting1")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting_noFCI","lyr")
##            arcpy.management.CalculateField("lyr","ACRES","!Shape_Area! / 43560","PYTHON_9.3")
##            arcpy.management.CalculateField("lyr","FUTURE_UNITS","!EFFECTIVE_DENSITY! * !ACRES! * -1","PYTHON_9.3")
##            arcpy.management.Delete("lyr")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting_noFCI","lyr","\"FUTURE_UNITS\" IS NULL")
##            arcpy.management.CalculateField("lyr","FUTURE_UNITS","0")
##            arcpy.management.Delete("lyr")
##
##            arcpy.management.MakeFeatureLayer("combo_units_reporting_noFCI","lyr")
##            arcpy.analysis.Frequency("lyr","total_units_cpasg_noFCI",["CPASG_1","CPASG_LABE"],"FUTURE_UNITS")
##            arcpy.management.Delete("lyr")
##
##            arcpy.management.MakeTableView("total_units_cpasg_noFCI","tv")
##            arcpy.management.AlterField("tv","FUTURE_UNITS","DELTA_FUTURE_UNITS","DELTA_FUTURE_UNITS")
##            arcpy.management.CalculateField("tv","DELTA_FUTURE_UNITS","!DELTA_FUTURE_UNITS!","PYTHON_9.3")
##            arcpy.management.DeleteField("tv","FREQUENCY")
##            arcpy.management.Delete("tv")
##
##            arcpy.management.MakeTableView("total_units_cpasg_noFCI","tv","\"CPASG_1\" = 0")
##            arcpy.management.DeleteRows("tv")
##            arcpy.management.Delete("tv")
##
##        except Exception as e:
##            success = False
##            print '\n*** ERROR with Combine all component fcs into 1 output fc ***'
##            print str(e)
##
##
##    #---------------------------------------------------------------------------
##    #                   Combine tables into 1 output table
##    #---------------------------------------------------------------------------
##    if success == True:
##        print('\n-------------------------------------------------------------')
##        print('Combine tables into 1 output table\n')
##        try:
##            new_fields = []
##            for i in component_list:
##                new_fields.append(i[1])
##
##            for geom in ["cpasg", "cpasg_noFCI", "hex60"]:
##                try:
##                    print(str(time.strftime("\n%H:%M:%S", time.localtime())) + " | Working on combining " + geom + " tables")
##                    out_name = "PDS_DEV_TRACKER_MAP12_" + geom.upper()
##                    print(out_name)
##
##                    # Create output table
##                    print('  Create output table')
##                    arcpy.management.Copy(public + "_units_"+ geom,out_name)
##                    if geom == "cpasg" or geom == "cpasg_noFCI":
##                        arcpy.management.MakeTableView(out_name,"tv")
##                        arcpy.management.AlterField("tv","CPASG_1","CPASG","CPASG")
##                        arcpy.management.Delete("tv")
##
##                    # Add fields
##                    print('  Add fields')
##                    arcpy.management.MakeTableView(out_name,"tv")
##                    for fld in new_fields:
##                        arcpy.management.AddField("tv",fld,"DOUBLE")
##                    arcpy.management.AddField("tv","VALUE_Annexations_Acquisitions","DOUBLE")
##                    arcpy.management.Delete("tv")
##
##                    # Populate fields
##                    print('  Populate fields')
##                    for i in component_list:
##                        ##print('    i: {}'.format(i))
##                        arcpy.management.MakeTableView(out_name,"tv")
##                        ##print(str(time.strftime("%H:%M:%S", time.localtime())) + " |   Adding " + i[1] + " to " + out_name)
##                        if i[0] == public:
##
##                            # === MG ===
##                            try:
##                                arcpy.management.CalculateField("tv",i[1],"!DELTA_FUTURE_UNITS!","PYTHON_9.3")
##                                arcpy.management.DeleteField("tv","DELTA_FUTURE_UNITS")
##                            except:
##                                arcpy.management.CalculateField("tv",i[1],"!DELTA_FUTURE_UNITS_NOFCI!","PYTHON_9.3")
##                                arcpy.management.DeleteField("tv","DELTA_FUTURE_UNITS_NOFCI")
##                            # ==========
##
##                        else:
##                            arcpy.management.MakeTableView(i[0] + "_units_" + geom,"tv2")
##                            if geom == "cpasg" or geom == "cpasg_noFCI":
##                                arcpy.management.AddJoin("tv","CPASG","tv2","CPASG_1")
##                            else:
##                                arcpy.management.AddJoin("tv","HEXAGONID","tv2","HEXAGONID")
##
##
##                            # === MG ===
##                            try:
##                                arcpy.management.CalculateField("tv", out_name + "." + i[1], "!" + i[0] + "_units_" + geom + ".DELTA_FUTURE_UNITS!", "PYTHON_9.3")
##                            except:
##                                arcpy.management.CalculateField("tv", out_name + "." + i[1], "!" + i[0] + "_units_" + geom + ".DELTA_FUTURE_UNITS_NOFCI!", "PYTHON_9.3")
##                            # ==========
##
##                            arcpy.management.RemoveJoin("tv",i[0] + "_units_" + geom)
##                            arcpy.management.Delete("tv2")
##                        arcpy.management.Delete("tv")
##
##                    # Total the components
##                    ##print(str(time.strftime("%H:%M:%S", time.localtime())) + " |   Adding VALUE_Annexations_Acquisitions to " + out_name)
##                    print('  Total the components')
##                    arcpy.management.MakeTableView(out_name,"tv")
##                    arcpy.management.MakeTableView("total_units_" + geom,"tv2")
##                    if geom == "cpasg" or geom == "cpasg_noFCI":
##                        arcpy.management.AddJoin("tv","CPASG","tv2","CPASG_1")
##                    else:
##                        arcpy.management.AddJoin("tv","HEXAGONID","tv2","HEXAGONID")
##
##                    # === MG ===
##                    try:
##                        arcpy.management.CalculateField("tv", out_name + ".VALUE_Annexations_Acquisitions", "!total_units_" + geom + ".DELTA_FUTURE_UNITS!", "PYTHON_9.3")
##                    except:
##                        arcpy.management.CalculateField("tv", out_name + ".VALUE_Annexations_Acquisitions", "!total_units_" + geom + ".DELTA_FUTURE_UNITS_NOFCI!", "PYTHON_9.3")
##                    # ==========
##
##                    arcpy.management.RemoveJoin("tv","total_units_" + geom)
##                    arcpy.management.Delete("tv2")
##                    arcpy.management.Delete("tv")
##
##                    if geom == "cpasg" or geom == "cpasg_noFCI":
##
##                        # Create a countywide record
##                        print('  Create a countywide record')
##                        arcpy.management.MakeTableView(out_name,"tv")
##                        arcpy.analysis.Statistics("tv","cpasg_total",[["VALUE_Annexations_Acquisitions","SUM"]])
##                        with arcpy.da.SearchCursor("cpasg_total",["SUM_VALUE_Annexations_Acquisitions"]) as cur1:
##                            for row in cur1:
##                                total_value = row[0]
##                        cur2 =  arcpy.da.InsertCursor(out_name,["CPASG","CPASG_LABE","VALUE_Annexations_Acquisitions"])
##                        cur2.insertRow([190000,"Countywide",total_value])
##                        del cur2
##                        arcpy.management.Delete("cpasg_total")
##                        arcpy.management.Delete("tv")
##
##                        # Round values  # MG changed to Round vs. Trunc
##                        print('  Round values')
##                        arcpy.management.MakeTableView(out_name,"tv")
##                        for i in component_list:
##                            expression = 'round(!{}!)'.format(i[1])
##                            ##print('    Field [{}] being calculated to equal: "{}"'.format(i[1], expression))
##                            arcpy.management.CalculateField("tv",i[1], expression,"PYTHON_9.3")
##
##                        expression = 'round(!VALUE_Annexations_Acquisitions!)'
##                        arcpy.management.CalculateField("tv","VALUE_Annexations_Acquisitions",expression, "PYTHON_9.3")
##                        arcpy.management.Delete("tv")
##
##                except Exception as e:
##                    success = False
##                    print '\n*** ERROR with geom: {} ***'.format(geom)
##                    print str(e)
##
##
##        except Exception as e:
##            success = False
##            print '\n*** ERROR with Combine tables into 1 output table ***'
##            print str(e)


    #---------------------------------------------------------------------------
    #                  Get working data into outpath FGDB
    #---------------------------------------------------------------------------
    if success == True:
        print('\n-------------------------------------------------------------')
        print('Get working data into outpath FGDB:')
        try:
            # === MG ===
            # Delete and create FGDB
            if arcpy.Exists(outpath):
                print 'Deleting FGDB at:\n  {}\n'.format(outpath)
                arcpy.Delete_management(outpath)

            if not arcpy.Exists(outpath):
                out_folder_path, out_name = os.path.split(outpath)
                print 'Creating FGDB at:\n  {}\n'.format(outpath)
                arcpy.CreateFileGDB_management(out_folder_path, out_name)
            # ==========

            # Change a field name and copy the working data into the outpath FGDB

            # CPASG
            try:
                arcpy.management.MakeTableView("PDS_DEV_TRACKER_MAP12_CPASG","tv")
                arcpy.management.AlterField("tv","CPASG_LABE","CPASG_NAME","CPASG_NAME")
                arcpy.management.Delete("tv")
            except:
                pass
            arcpy.management.Copy("PDS_DEV_TRACKER_MAP12_CPASG",os.path.join(outpath,"PDS_DEV_TRACKER_MAP12_CPASG"))

            # CPASG_NOFCI
            try:
                arcpy.management.MakeTableView("PDS_DEV_TRACKER_MAP12_CPASG_NOFCI","tv")
                arcpy.management.AlterField("tv","CPASG_LABE","CPASG_NAME","CPASG_NAME")
                arcpy.management.Delete("tv")
            except:
                pass
            arcpy.management.Copy("PDS_DEV_TRACKER_MAP12_CPASG_NOFCI",os.path.join(outpath,"PDS_DEV_TRACKER_MAP12_CPASG_NO_FCI"))

            # HEX
            arcpy.management.Copy("PDS_DEV_TRACKER_MAP12_HEX60",os.path.join(outpath,"PDS_DEV_TRACKER_MAP12_HEX60"))


        except Exception as e:
            success = False
            print '\n*** ERROR with Get working data into outpath FGDB ***'
            print str(e)

    #===========================================================================
    #===========================================================================
    #                       FINISH GARY'S MAIN FUNCTION
    #===========================================================================
    #===========================================================================


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    # Write a file to disk to let other scripts know if this script ran
    # successfully or not
    print '\n------------------------------------------------------------------'
    try:

        # Set a file_name depending on the 'success' variable.
        if success == True:
            file_to_create = success_file
        else:
            file_to_create = error_file

        # Write the file
        print '\nCreating file:\n  {}\n'.format(file_to_create)
        open(file_to_create, 'w')

    except Exception as e:
        success = False
        print '*** ERROR with Writing a Success or Fail file() ***'
        print str(e)


    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    # Footer for log file
    finish_time_str = [datetime.datetime.now().strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                    {}'.format(finish_time_str)
    print '              Finished {}'.format(name_of_script)
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'

    # End of script reporting
    print 'Successfully ran script = {}'.format(success)
    time.sleep(3)
##    sys.stdout = orig_stdout
    sys.stdout.flush()

    if success == True:
        print '\nSUCCESSFULLY ran {}'.format(name_of_script)
    else:
        print '\n*** ERROR with {} ***'.format(name_of_script)

##    print 'Please find log file at:\n  {}\n'.format(log_file_date)
    print '\nSuccess = {}'.format(success)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#                            START DEFINING FUNCTIONS
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Write_Print_To_Log()
def Write_Print_To_Log(log_file, name_of_script):
    """
    PARAMETERS:
      log_file (str): Path to log file.  The part after the last "\" will be the
        name of the .log file after the date, time, and ".log" is appended to it.

    RETURNS:
      orig_stdout (os object): The original stdout is saved in this variable so
        that the script can access it and return stdout back to its orig settings.
      log_file_date (str): Full path to the log file with the date appended to it.
      dt_to_append (str): Date and time in string format 'YYYY_MM_DD__HH_MM_SS'

    FUNCTION:
      To turn all the 'print' statements into a log-writing object.  A new log
        file will be created based on log_file with the date, time, ".log"
        appended to it.  And any print statements after the command
        "sys.stdout = write_to_log" will be written to this log.
      It is a good idea to use the returned orig_stdout variable to return sys.stdout
        back to its original setting.
      NOTE: This function needs the function Get_DT_To_Append() to run

    """
    ##print 'Starting Write_Print_To_Log()...'

    # Get the original sys.stdout so it can be returned to normal at the
    #    end of the script.
    orig_stdout = sys.stdout

    # Get DateTime to append
    dt_to_append = Get_DT_To_Append()

    # Create the log file with the datetime appended to the file name
    log_file_date = '{}_{}.log'.format(log_file,dt_to_append)
    write_to_log = open(log_file_date, 'w')

    # Make the 'print' statement write to the log file
    print 'Find log file found at:\n  {}'.format(log_file_date)
    print '\nProcessing...\n'
    sys.stdout = write_to_log

    # Header for log file
    start_time = datetime.datetime.now()
    start_time_str = [start_time.strftime('%m/%d/%Y  %I:%M:%S %p')][0]
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
    print '                  {}'.format(start_time_str)
    print '             START {}'.format(name_of_script)
    print '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n'

    return orig_stdout, log_file_date, dt_to_append


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#                          FUNCTION Get_dt_to_append
def Get_DT_To_Append():
    """
    PARAMETERS:
      none

    RETURNS:
      dt_to_append (str): Which is in the format 'YYYY_MM_DD__HH_MM_SS'

    FUNCTION:
      To get a formatted datetime string that can be used to append to files
      to keep them unique.
    """
    ##print 'Starting Get_DT_To_Append()...'

    start_time = datetime.datetime.now()

    date = start_time.strftime('%Y_%m_%d')
    time = start_time.strftime('%H_%M_%S')

    dt_to_append = '%s__%s' % (date, time)

    ##print '  DateTime to append: {}'.format(dt_to_append)

    ##print 'Finished Get_DT_To_Append()\n'
    return dt_to_append

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def program_impact(sdepath, sde_prefix, model_out, model_noFCI, cpasg, hexbin, component_list, program_name, data_query):
    """
    TODO: Add documentation here
    """

    print(str(time.strftime("\n  %H:%M:%S", time.localtime())) + " | Working on {}".format(program_name))
    print('    Data query:  "{}"'.format(data_query))

    arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + program_name),"program",data_query)
    arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + model_out),"units","\"FUTURE_UNITS\" > 0")
    arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + model_noFCI),"units_nofci","\"FUTURE_UNITS\" > 0")
    arcpy.analysis.Intersect(["program","units","units_nofci"],"program_units1")
    arcpy.management.Delete("program")
    arcpy.management.Delete("units")
    arcpy.management.Delete("units_nofci")

    # alter fields from "nofci"
    arcpy.management.MakeFeatureLayer("program_units1","lyr")
    arcpy.management.AlterField("lyr","EFFECTIVE_DENSITY_1","EFFECTIVE_DENSITY_NOFCI","EFFECTIVE_DENSITY_NOFCI")
    arcpy.management.AlterField("lyr","FUTURE_UNITS_1","FUTURE_UNITS_NOFCI","FUTURE_UNITS_NOFCI")
    arcpy.management.Delete("lyr")

    arcpy.management.MakeFeatureLayer("program_units1","lyr")
    arcpy.management.RepairGeometry("lyr")
    arcpy.management.MultipartToSinglepart("lyr","program_units")
    arcpy.management.Delete("lyr")
    arcpy.management.Delete("program_units1")
    arcpy.management.RepairGeometry("program_units")

    for nm in component_list:
        if nm[0] == program_name:
            arcpy.management.Copy("program_units",nm[1])

    arcpy.management.MakeFeatureLayer("program_units","aoi")
    arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + cpasg),"cpa")
    arcpy.management.MakeFeatureLayer(os.path.join(sdepath,sde_prefix + hexbin),"hex")
    arcpy.analysis.Union(["aoi","cpa","hex"],"program_units_reporting1")
    arcpy.management.RepairGeometry("program_units_reporting1")
    arcpy.management.Delete("aoi")
    arcpy.management.Delete("cpa")
    arcpy.management.Delete("hex")

    arcpy.management.MakeFeatureLayer("program_units_reporting1","lyr")
    arcpy.management.MultipartToSinglepart("lyr","program_units_reporting")
    arcpy.management.RepairGeometry("program_units_reporting")
    arcpy.management.Delete("lyr")
    arcpy.management.Delete("program_units_reporting1")

    arcpy.management.MakeFeatureLayer("program_units_reporting","lyr")
    arcpy.management.CalculateField("lyr","ACRES","!Shape_Area! / 43560","PYTHON_9.3")
    arcpy.management.CalculateField("lyr","FUTURE_UNITS","!EFFECTIVE_DENSITY! * !ACRES! * -1","PYTHON_9.3")
    arcpy.management.CalculateField("lyr","FUTURE_UNITS_NOFCI","!EFFECTIVE_DENSITY_NOFCI! * !ACRES! * -1","PYTHON_9.3")
    arcpy.management.Delete("lyr")

    arcpy.management.MakeFeatureLayer("program_units_reporting","lyr","\"FUTURE_UNITS\" IS NULL")
    arcpy.management.CalculateField("lyr","FUTURE_UNITS","0")
    arcpy.management.Delete("lyr")

    arcpy.management.MakeFeatureLayer("program_units_reporting","lyr","\"FUTURE_UNITS_NOFCI\" IS NULL")
    arcpy.management.CalculateField("lyr","FUTURE_UNITS_NOFCI","0")
    arcpy.management.Delete("lyr")

    arcpy.management.MakeFeatureLayer("program_units_reporting","lyr")
    arcpy.analysis.Frequency("lyr",program_name + "_units_cpasg",["CPASG_1","CPASG_LABE"],"FUTURE_UNITS")
    arcpy.analysis.Frequency("lyr",program_name + "_units_cpasg_noFCI",["CPASG_1","CPASG_LABE"],"FUTURE_UNITS_NOFCI")
    arcpy.analysis.Frequency("lyr",program_name + "_units_hex60","HEXAGONID","FUTURE_UNITS")
    arcpy.management.Delete("lyr")

    arcpy.management.MakeTableView(program_name + "_units_cpasg","tv")
    arcpy.management.AlterField("tv","FUTURE_UNITS","DELTA_FUTURE_UNITS","DELTA_FUTURE_UNITS")
    arcpy.management.CalculateField("tv","DELTA_FUTURE_UNITS","!DELTA_FUTURE_UNITS!","PYTHON_9.3")
    arcpy.management.DeleteField("tv","FREQUENCY")
    arcpy.management.Delete("tv")

    arcpy.management.MakeTableView(program_name + "_units_cpasg","tv","\"CPASG_1\" = 0")
    arcpy.management.DeleteRows("tv")
    arcpy.management.Delete("tv")

    arcpy.management.MakeTableView(program_name + "_units_cpasg_noFCI","tv")
    arcpy.management.AlterField("tv","FUTURE_UNITS_NOFCI","DELTA_FUTURE_UNITS_NOFCI","DELTA_FUTURE_UNITS_NOFCI")
    arcpy.management.CalculateField("tv","DELTA_FUTURE_UNITS_NOFCI","!DELTA_FUTURE_UNITS_NOFCI!","PYTHON_9.3")
    arcpy.management.DeleteField("tv","FREQUENCY")
    arcpy.management.Delete("tv")

    arcpy.management.MakeTableView(program_name + "_units_cpasg_noFCI","tv","\"CPASG_1\" = 0")
    arcpy.management.DeleteRows("tv")
    arcpy.management.Delete("tv")

    arcpy.management.MakeTableView(program_name + "_units_hex60","tv")
    arcpy.management.AlterField("tv","FUTURE_UNITS","DELTA_FUTURE_UNITS","DELTA_FUTURE_UNITS")
    arcpy.management.DeleteField("tv","FREQUENCY")
    arcpy.management.Delete("tv")

    arcpy.management.MakeTableView(program_name + "_units_hex60","tv","\"HEXAGONID\" = ''")
    arcpy.management.DeleteRows("tv")
    arcpy.management.Delete("tv")


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
