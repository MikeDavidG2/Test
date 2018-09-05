"""
Purpose:     Update the "update date" in the disclaimers and export the data-driven map series pdf.
             Requires table PDS_DEV_TRACKER_LAST_DATA_UPDATE with a definition query in the mxd so
                only 1 record is accessible.
             Requires text box element that will be updated in mxd to be called "text_box_element"
                (except map 12 which is called "text_box_map12").
Author:      gr
Created:     08/21/2018
"""
import arcpy, os, time, ConfigParser, sys

def main():
    #---------------------------------------------------------------------------
    #                  Set variables that only need defining once
    #                    (Shouldn't need to be changed much)
    #---------------------------------------------------------------------------

    # Set name to give outputs for this script
    shorthand_name    = 'Export_MXD_to_PDF'


    # Name of this script
    name_of_script = 'DEV_TRACKER_{}.py'.format(shorthand_name)


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
    root_folder      = config.get('Paths_Local', 'Root_Folder')
    pds_share_folder = config.get('Paths_Local', 'Folder_To_Share_w_PDS')

    #---------------------------------------------------------------------------
    # Paths to folders and local FGDBs
    log_file_folder   = '{}\{}\{}'.format(root_folder, 'Scripts', 'Logs')

    mxd_folder        = os.path.join(root_folder, "MXDs_to_Generate_PDFs")

    pdf_folder        = os.path.join(pds_share_folder, "PDFs")


    # Success / Error file info
    success_error_folder = '{}\Scripts\Source_Code\Success_Error'.format(root_folder)
    success_file = '{}\SUCCESS_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])
    error_file   = '{}\ERROR_running_{}.txt'.format(success_error_folder, name_of_script.split('.')[0])

    # Number of SUCCESS files this script needs to see in the success_error_folder
    # in order to safely run
    desired_num_success_files = 17


    # Misc variables
    success = True
    map_01_name  = "MAP_01_DT.mxd"


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
    if os.path.exists(success_file):
        print 'Deleting old file at:\n  {}\n'.format(success_file)
        os.remove(success_file)
    if os.path.exists(error_file):
        print 'Deleting old file at:\n  {}\n'.format(error_file)
        os.remove(error_file)


    #---------------------------------------------------------------------------
    #          Only run the Export if all previously run scripts were
    #                          SUCCESSFULLY run
    #---------------------------------------------------------------------------
    if success == True:
        try:
            # List all files in "success_error_folder"
            print('\n-----------------------------------------------------------------')
            print('Listing all files at:\n  {}\nTo confirm that all previous scripts ran sucessfully'.format(success_error_folder))
            files = [f for f in os.listdir(success_error_folder) if os.path.isfile(os.path.join(success_error_folder, f))]

            # Check to see if any files start with 'ERROR'
            print('\n  Checking to see if any scripts produced an "ERROR" file')
            for f in files:
                if f.startswith('ERROR'):
                    success = False
                    print('*** WARNING! There is an "ERROR" file at:\n  {}\n'.format(os.path.join(success_error_folder, f)))


            # If there were no ERROR files,
            # Check to confirm there are the correct number of files that start with "SUCCESS"
            if success == True:
                print('\n  Checking to see if there are the correct number of "SUCCESS" files')
                count_success = 0
                for f in files:
                    if f.startswith('SUCCESS'):
                        count_success += 1

                if count_success < desired_num_success_files:
                    success = False
                    print('*** WARNING!  There should be {} "SUCCESS" files, but there are {}'.format(desired_num_success_files, count_success))
                    print('This means that some previously run scripts were not successfully run.')
                    print('But they did not produce an ERROR file for some reason')


            if success == False:
                print('\nThe above "WARNINGS" mean that this script will not be run')
                print('Please fix the previously run scripts and rerun this script')

            else:
                print('  OK! All previously run scripts were "SUCCESSFULLY" run.  Continuing to run this script.')

        except Exception as e:
            success = False
            print '\n*** ERROR with Checking if all previously run scripts were SUCCESSFULLY run ***'
            print str(e)


    #---------------------------------------------------------------------------
    #                      Create Folders if needed
    #---------------------------------------------------------------------------
    if success == True:
        try:

            # Make sure the MXD folder exists
            # (this cannot be created by the script but must already exist with MXDs)
            if not os.path.exists(mxd_folder):
                success == False
                print('*** ERROR! The below folder does not exist.')
                print('  This script needs MXDs in this folder in order to export them to PDFs:')
                print('    {}'.format(mxd_folder))

            # Create the PDF folder if it does not exist
            if not os.path.exists(pdf_folder):
                print 'INFO, folder "{}" does not exist, creating it now'.format(os.path.basename(pdf_folder))
                os.mkdir(pdf_folder)

        except Exception as e:
            success = False
            print '\n*** ERROR with Creating Folders ***'
            print str(e)


    #===========================================================================
    #===========================================================================
    #                       START GARY'S MAIN FUNCTION
    #===========================================================================
    #===========================================================================

    # Loops through each .mxd file in "mxd_folder" (with the exception of "map_01_name")
    # and export each page (CPA/SG/countywide) to individual .pdf files.  Each .mxd
    # produces 37 .pdf files.


    # Get a list of MXDs to export to PDF
    if success == True:
        try:
            # Get a list of all the MXDs in the MXD Folder
            print('Getting list of all MXDs in the folder:\n  {}'.format(mxd_folder))

            arcpy.env.workspace = mxd_folder
            mxd_list = arcpy.ListFiles("*.mxd")


            # Map 01 is static, no need to export it to PDF.  Remove it from the list to process
            if map_01_name in mxd_list:
                mxd_list.remove(map_01_name)
            else:
                print('INFO {} does not exist in the MXD Folder'.format(map_01_name))
                print('  Not an error, but this MXD should still be there...')

        except Exception as e:
            success = False
            print '\n*** ERROR with ListFiles() ***'
            print str(e)


    #---------------------------------------------------------------------------
    # Loop through each .mxd and 1) Update the Disclaimer  |  2) Export series to PDF
    if success == True:
        print('\n-------------------------------------------------------------')
        print('Export MXDs to PDFs:\n')
        for map_name in mxd_list:
            print('  {} | Processing "{}":'.format(time.strftime("%H:%M:%S", time.localtime()), map_name))


            # Update the Disclaimer before exporting
            try:
                update_disclaimer(mxd_folder, map_name)

            except Exception as e:
                success = False
                print '\n*** ERROR with update_disclaimer() ***'
                print str(e)


            # Export the MXD to PDF
            try:
                export_map_series(mxd_folder, map_name, pdf_folder)

            except Exception as e:
                success = False
                print '\n*** ERROR with export_map_series() ***'
                print str(e)


    #---------------------------------------------------------------------------
    #                            Rename the PDFs
    if success == True:
        try:
            print('\n{} | Renaming PDF files'.format(time.strftime("%H:%M:%S", time.localtime())))
            rename_pdf_files(pdf_folder)
        except Exception as e:
            success = False
            print '\n*** ERROR with rename_pdf_files() ***'
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
def update_disclaimer(mxd_path, mxd_name):
    """
    Updates the disclaimer with the date of the data extract obtained from PDS_DEV_TRACKER_LAST_DATA_UPDATE table
    and saves the .mxd file.  This will fail if the .mxd is open or a read-only file.
    """

    print('    Updating Disclaimer with date:')

    mxd = arcpy.mapping.MapDocument(os.path.join(mxd_path,mxd_name))
    df = arcpy.mapping.ListDataFrames(mxd)[0]

    # This table should have a definition query so only 1 record is used
    tab = arcpy.mapping.ListTableViews(mxd,"*DATA_UPDATE",df)[0]


    # Get the date of the maps data
    with arcpy.da.SearchCursor(tab,"LAST_DATA_UPDATE") as c:
        for r in c:
            the_date = r[0]  # The date from LAST_DATA_UPDATE

    print('      {}'.format(the_date))


    # Set the text to update the text_box_element
    txt        = "This map is an estimate intended for discussion purposes only. This map is a representation of permitting data extracted from the County of San Diego Planning and Development Services Accela database on <BOL>{}</BOL>.\n<BOL>HexBin</BOL> is a data process and cartographic technique for showing the density of point features in a standard area polygon.  HexBinning involves overlaying a grid of uniform hexagonal shapes onto a point dataset.  Each hexagonal cell in the grid is then assigned the number of points that falls within it.  A graduated color classification is then employed to show visually which cells contain the largest number of points.  The term hexbin is the portmanteau for hexagonal binning.".format(the_date)

    txt_Map_12 = "This map is an estimate intended for discussion purposes only. This map is a representation of processed GIS data from the County of San Diego Planning and Development Services on <BOL>{}</BOL>.\n<BOL>HexBin</BOL> is a data process and cartographic technique for showing the density of point features in a standard area polygon.  HexBinning involves overlaying a grid of uniform hexagonal shapes onto a point dataset.  Each hexagonal cell in the grid is then assigned the number of points that falls within it.  A graduated color classification is then employed to show visually which cells contain the largest number of points.  The term hexbin is the portmanteau for hexagonal binning.".format(the_date)

    for le in arcpy.mapping.ListLayoutElements(mxd):
        if le.name == "text_box_element":
            le.text = txt
        if le.name == "text_box_map12":
            le.text = txt_Map_12
    mxd.save()

    del df, tab, mxd, the_date
    return

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def export_map_series(mxd_path, mxd_name, out_folder):
    """
    Export each .mxd file to individual .pdf files.
    Each Community Plan Area, Sponsor Group, and countywide has a separate file.
    """

    print('    Exporting Map Series')

    mxd = arcpy.mapping.MapDocument(os.path.join(mxd_path,mxd_name))
    df = arcpy.mapping.ListDataFrames(mxd)[0]

    mxd.dataDrivenPages.exportToPDF(os.path.join(out_folder,df.name),"ALL","","PDF_MULTIPLE_FILES_PAGE_NAME")

    del df, mxd
    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def rename_pdf_files(out_folder):
    """
    Renames all data-driven page names in out_folder from format
    "PDSDevTracker_Map#XX_Community Name.pdf" to
    "Community_Name_PDSDevTracker_Map#XX.pdf"
    """

    for old_name in os.listdir(out_folder):
        try:
            if old_name[:13] == "PDSDevTracker":
                new_name = old_name[21:-4].replace(" ","_") + "_" + old_name[:20] + ".pdf"

                try:
                    os.rename(out_folder + "\\" + old_name, out_folder + "\\" + new_name)
                except: # if new file name already exists, delete it first
                    os.remove(out_folder + "\\" + new_name)
                    os.rename(out_folder + "\\" + old_name, out_folder + "\\" + new_name)
                del new_name

        except Exception as e:
            print '\n*** ERROR with Changing name for {} ***'.format(old_name)
            print str(e)

    return


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
