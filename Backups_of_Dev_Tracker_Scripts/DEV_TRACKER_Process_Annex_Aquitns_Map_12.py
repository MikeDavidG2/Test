#-------------------------------------------------------------------------------

# Purpose:
"""
Combine all "programs" that cause a loss of development potential.
The programs currently are:
    Purchase of Agricultural Conservation Easement (PACE)
    Williamson Act Contract lands
    Open Space Easements
Additionally, the following loss of jurisdiction is considered:
    Annexations to municipalities
    Public ownership
    Indian Reservation expansion
The housing model is used to determine the predicted development potential that is removed.
"""
#
# Author:      Gary Ross / (Mike Grue wrote template)
#
# Created:     24/07/2018
# Copyright:   (c) Gary Ross 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import datetime, arcpy, math, os, string, sys, time, ConfigParser

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


    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    #                   Use cfgFile to set the below variables

    # Find a connection to the config file
    # You can set multiple config files (to easily move this script to another network)
    # Recommended (A = BLUE network) and (B = COUNTY network)
    cfgFile_A     = r"P:\20180510_development_tracker\DEV\Scripts\Config_Files\DEV_TRACKER_Main_Config_File.ini"
    cfgFile_B     = r"D:\DEV_TRACKER\PROD\Scripts\Config_Files\DEV_TRACKER_Main_Config_File.ini"

    if os.path.exists(cfgFile_A):
        cfgFile = cfgFile_A  # Use config file A

    elif os.path.exists(cfgFile_B):
        cfgFile = cfgFile_B  # Use config file B

    else:
        print("*** ERROR! cannot find valid INI file ***\nMake sure a valid INI file exists at:\n  {}\nOR:\n  {}".format(cfgFile_A, cfgFile_B))
        print 'You may have to change the name/location of the INI file,\nOR change the variable in this script.'
        success = False
        time.sleep(10)
        return  # Stop the script

    if os.path.isfile(cfgFile):
        print 'Using INI file found at:\n  {}\n'.format(cfgFile)
        config = ConfigParser.ConfigParser()
        config.read(cfgFile)


    # Get variables from .ini file
    root_folder        = config.get('Paths_Local',   'Root_Folder')
    prod_SDE_conn_file = config.get('Prod_SDE_Info', 'Prod_SDE_Conn_File')
    prod_SDE_prefix    = config.get('Prod_SDE_Info', 'Prod_SDE_Prefix')


    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')
    data_folder       = '{}\{}'.format(root_folder, 'Data')
    wkg_fgdb          = '{}\{}'.format(data_folder, '{}.gdb'.format(shorthand_name))


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])


    # Misc variables
    success = True

    #---------------------------------------------------------------------------
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #---------------------------------------------------------------------------
    #                          Start Main Function

    # Make sure the log file folder exists, create it if it does not
    if not os.path.exists(log_file_folder):
        print 'NOTICE, log file folder does not exist, creating it now\n'
        os.mkdir(log_file_folder)

    # Turn all 'print' statements into a log-writing object
    try:
        log_file = r'{}\{}'.format(log_file_folder, name_of_script.split('.')[0])
        orig_stdout, log_file_date, dt_to_append = Write_Print_To_Log(log_file, name_of_script)
    except Exception as e:
        success = False
        print '\n*** ERROR with Write_Print_To_Log() ***'
        print str(e)


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
    if success == True:
        try:

            # Delete and create working FGDB
            if arcpy.Exists(wkg_fgdb):
                print 'Deleting FGDB at:\n  {}\n'.format(wkg_fgdb)
                arcpy.Delete_management(wkg_fgdb)

            if not arcpy.Exists(wkg_fgdb):
                out_folder_path, out_name = os.path.split(wkg_fgdb)
                print 'Creating FGDB at:\n  {}\n'.format(wkg_fgdb)
                arcpy.CreateFileGDB_management(out_folder_path, out_name)
            arcpy.env.workspace = wkg_fgdb

        except Exception as e:
            success = False
            print '\n*** ERROR with Creating FGDBs ***'
            print str(e)



    #===========================================================================
    #===========================================================================
    #                       START GARY'S MAIN FUNCTION
    #===========================================================================
    #===========================================================================



    # Set variables for GARY'S MAIN FUNCTION
    annexations  = "JUR_MUNICIPAL_ANNEX_HISTORY"
    curr_juris   = "JUR_MUNICIPAL"
    public       = "LAND_OWNERSHIP_SG"
    tribal       = "INDIAN_RESERVATIONS"
    pace         = "AG_PACE"
    wa_contract  = "AG_PRESERVE_CONTRACTS"
    os_easement  = "ESMT_OPEN_SPACE"
    model_out    = "PDS_HOUSING_MODEL_OUTPUT_2011"
    model_noFCI  = "PDS_HOUSING_MODEL_OUTPUT_2011_NO_FCI"
    adopted_date = '2011-08-03 00:00:00'


    # list of dataset name and the new field name in combined dataset (AOI)
    component_list = [
        (public,"AQUISITION"),
        (tribal,"RESERVATIONS"),
        (pace,"PACE"),
        (wa_contract,"WILLIAMSON_ACT"),
        (os_easement,"OPEN_SPACE"),
        (annexations,"ANNEXATIONS")]


    #---------------------------------------------------------------------------
    #                            Find Program Impact
    #---------------------------------------------------------------------------
    if success == True:
        print('\n-------------------------------------------------------------')
        print('Find Program Impact:\n')
        try:
            # Aquisitions by public agencies
            program_name = public
            data_query   = "OWN <> 42"  # Don't include Indian Reservations
            program_impact(prod_SDE_conn_file,prod_SDE_prefix,model_out,model_noFCI,program_name,data_query)


            # Indian Reservation expansion
            program_name = tribal
            data_query   = ""
            program_impact(prod_SDE_conn_file,prod_SDE_prefix,model_out,model_noFCI,program_name,data_query)

            # Purchase of Agricultural Conservation Easement (PACE)
            program_name = pace
            data_query   = "PACE_ENROLLED = 'Y'"
            program_impact(prod_SDE_conn_file,prod_SDE_prefix,model_out,model_noFCI,program_name,data_query)

            # Williamson Act Contracts
            program_name = wa_contract
            data_query   = ""
            program_impact(prod_SDE_conn_file,prod_SDE_prefix,model_out,model_noFCI,program_name,data_query)

            # Open Space Easements (only Open Space, Biological, and Conservation)
            program_name = os_easement
            data_query   = "SUB_TYPE in (1, 2, 4)"
            program_impact(prod_SDE_conn_file,prod_SDE_prefix,model_out,model_noFCI,program_name,data_query)

            # Annexations
            program_name = annexations
            data_query   = "STATUS = 2 AND DATE_ > '{}'".format(adopted_date)
            program_impact(prod_SDE_conn_file,prod_SDE_prefix,model_out,model_noFCI,program_name,data_query)


        except Exception as e:
            success = False
            print '\n*** ERROR with Find Program Impact ***'
            print str(e)


    #---------------------------------------------------------------------------
    #                            Process Detachments
    #---------------------------------------------------------------------------
    if success == True:
        print('\n-----------------------------------------------------------------')
        print('Processing Detachments:')
        try:
            print(str(time.strftime("%H:%M:%S", time.localtime())) + " | Working on detachments")
            arcpy.management.MakeFeatureLayer(os.path.join(prod_SDE_conn_file,prod_SDE_prefix + annexations),
                                              "detach",
                                              "\"STATUS\" = 3 AND \"DATE_\" > '{}'".format(adopted_date))
            arcpy.management.MultipartToSinglepart("detach","detach_units1")
            arcpy.management.Delete("detach")

            arcpy.management.MakeFeatureLayer(os.path.join(prod_SDE_conn_file,prod_SDE_prefix + curr_juris),"uninc","\"CODE\" = 'CN'")
            arcpy.management.MakeFeatureLayer("detach_units1","lyr")
            arcpy.management.SelectLayerByLocation("lyr","HAVE_THEIR_CENTER_IN","uninc")
            if int(arcpy.management.GetCount("lyr")[0]) > 0:
                arcpy.management.CopyFeatures("lyr","detach_units")
                arcpy.management.RepairGeometry("detach_units")
                print("\n***************************************")
                print("NOTICE - There are DETACHMENTS that have added to the unincorporated")
                print("         area.  You need to determine what the General Plan designation(s).")
                print("         what the General Plan designations.  The Housing Model must be run")
                print("         to determine how many units that will be added to capacity.")
                print("         Please review feature class " + str(os.path.join(arcpy.env.workspace,"detach_units")) + ".\n")
            else:
                print("             No detachments occurred")
            arcpy.management.Delete("lyr")
            arcpy.management.Delete("detach_units1")

        except Exception as e:
            success = False
            print '\n*** ERROR with Processing Detachments ***'
            print str(e)


    #---------------------------------------------------------------------------
    #                   Combine all component fcs into 1 output fc
    #---------------------------------------------------------------------------
    if success == True:
        arcpy.env.workspace = wkg_fgdb# DELETE after testing
        print('\n-------------------------------------------------------------')
        print('Combine all component fcs into 1 output fc:')
        try:
            print(str(time.strftime("%H:%M:%S", time.localtime())) + " | Working on combining feature classes")
            # Combine all the components into 1 layer
            ulist = []
            for nm in component_list:
                ulist.append(nm[0])
            arcpy.analysis.Union(ulist,"COMBO1")
            arcpy.management.MakeFeatureLayer("COMBO1","lyr")
            arcpy.management.AddField("lyr","FLAG_LOSS","SHORT")
            arcpy.management.CalculateField("lyr","FLAG_LOSS","1")
            arcpy.management.Delete("lyr")

            arcpy.management.MakeFeatureLayer("COMBO1","lyr")
            arcpy.management.Dissolve("lyr","COMBO2","FLAG_LOSS")
            arcpy.management.Delete("lyr")
            arcpy.management.Delete("COMBO1")

            arcpy.management.RepairGeometry("COMBO2")
            arcpy.management.MultipartToSinglepart("COMBO2","COMBO")
            arcpy.management.RepairGeometry("COMBO")
            arcpy.management.Delete("COMBO2")

            arcpy.management.MakeFeatureLayer("COMBO","program")
            arcpy.management.MakeFeatureLayer(os.path.join(prod_SDE_conn_file,prod_SDE_prefix + model_out),"units","\"FUTURE_UNITS\" > 0")
            arcpy.management.MakeFeatureLayer(os.path.join(prod_SDE_conn_file,prod_SDE_prefix + model_noFCI),"units_nofci","\"FUTURE_UNITS\" > 0")
            arcpy.analysis.Intersect(["program","units","units_nofci"],"program_units1")
            arcpy.management.Delete("program")
            arcpy.management.Delete("units")
            arcpy.management.Delete("units_nofci")

            arcpy.management.MakeFeatureLayer("program_units1","lyr")
            arcpy.management.AlterField("lyr","EFFECTIVE_DENSITY_1","DENSITY_NOFCI","DENSITY_NOFCI")
            arcpy.management.AlterField("lyr","EFFECTIVE_DENSITY","DENSITY_FCI","DENSITY_FCI")
            arcpy.management.Delete("lyr")

            arcpy.management.MakeFeatureLayer("program_units1","lyr")
            arcpy.management.RepairGeometry("lyr")
            arcpy.management.MultipartToSinglepart("lyr","COMBO")
            arcpy.management.Delete("lyr")
            arcpy.management.Delete("program_units1")
            arcpy.management.RepairGeometry("COMBO")

            #-------------------------------------------------------------------
            # Create ready2bin
            arcpy.management.MakeFeatureLayer("COMBO","lyr")
            arcpy.management.Dissolve("lyr",shorthand_name + "1","DENSITY_FCI","","SINGLE_PART")
            arcpy.management.RepairGeometry(shorthand_name + "1")
            arcpy.management.MultipartToSinglepart(shorthand_name + "1",shorthand_name + "_READY2BIN")
            arcpy.management.RepairGeometry(shorthand_name + "_READY2BIN")
            arcpy.management.Delete(shorthand_name + "1")
            arcpy.management.Delete("lyr")

            arcpy.management.MakeFeatureLayer(shorthand_name + "_READY2BIN","lyr")
            arcpy.management.AlterField("lyr","DENSITY_FCI","DENSITY","DENSITY")
            arcpy.management.DeleteField("lyr","ORIG_FID")

            # Calculate [DENSITY] field to be all negatives ([DENSITY]*-1)
            expression = '!DENSITY!*-1'
            print '\n  Calculating all values in field "{}" to be negative: {}\n'.format('DENSITY', expression)
            arcpy.CalculateField_management("lyr", 'DENSITY', expression, 'PYTHON_9.3')

            arcpy.management.Delete("lyr")


            #-------------------------------------------------------------------
            # Create no_fci ready2bin
            arcpy.management.MakeFeatureLayer("COMBO","lyr")
            arcpy.management.Dissolve("lyr",shorthand_name + "1","DENSITY_NOFCI","","SINGLE_PART")
            arcpy.management.RepairGeometry(shorthand_name + "1")
            arcpy.management.MultipartToSinglepart(shorthand_name + "1",shorthand_name + "_NOFCI_READY2BIN")
            arcpy.management.RepairGeometry(shorthand_name + "_NOFCI_READY2BIN")
            arcpy.management.Delete(shorthand_name + "1")
            arcpy.management.Delete("lyr")

            arcpy.management.MakeFeatureLayer(shorthand_name + "_NOFCI_READY2BIN","lyr")
            arcpy.management.AlterField("lyr","DENSITY_NOFCI","DENSITY","DENSITY")
            arcpy.management.DeleteField("lyr","ORIG_FID")

            # Calculate [DENSITY] field to be all negatives ([DENSITY]*-1)
            expression = '!DENSITY!*-1'
            print '\n  Calculating all values in field "{}" to be negative: {}\n'.format('DENSITY', expression)
            arcpy.CalculateField_management("lyr", 'DENSITY', expression, 'PYTHON_9.3')
            arcpy.management.Delete("lyr")


        except Exception as e:
            success = False
            print '\n*** ERROR with Combine all component fcs into 1 output fc ***'
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
    sys.stdout = orig_stdout
    sys.stdout.flush()

    if success == True:
        print '\nSUCCESSFULLY ran {}'.format(name_of_script)
    else:
        print '\n*** ERROR with {} ***'.format(name_of_script)

    print 'Please find log file at:\n  {}\n'.format(log_file_date)
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
def program_impact(sdepath,sde_prefix,model_out,model_noFCI,program_name,data_query):
    """
    Calculate the Housing Model output for the areas covered by the program (such as PACE, Williamson Act).
    It is calculated both with and witout FCI as a constraint.
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
    arcpy.management.AlterField("lyr","EFFECTIVE_DENSITY_1","DENSITY_NOFCI","DENSITY_NOFCI")
    arcpy.management.AlterField("lyr","EFFECTIVE_DENSITY","DENSITY_FCI","DENSITY_FCI")
    arcpy.management.Delete("lyr")

    arcpy.management.MakeFeatureLayer("program_units1","lyr")
    arcpy.management.RepairGeometry("lyr")
    arcpy.management.MultipartToSinglepart("lyr",program_name)
    arcpy.management.Delete("lyr")
    arcpy.management.Delete("program_units1")
    arcpy.management.RepairGeometry(program_name)


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
