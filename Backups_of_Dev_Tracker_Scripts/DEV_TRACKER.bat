::Set paths to scripts to be called
set name_of_batch_file=DEV_TRACKER

::Set path to working folder
set wkg_folder=P:\20180510_development_tracker\DEV\Scripts

::Set the path and name for the log file
set log=%wkg_folder%\Logs\%name_of_batch_file%.log

::Set path to Format CSV Extracts
set Format_CSV_Extracts=%wkg_folder%\Source_Code\DEV_TRACKER_Format_CSV_Extracts.py

::Set paths to PROCESSING scripts. The order that they are set below is also the order they should be run
set Process_Approved_GPA_Map_02=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Approved_GPA_Map_02.py
set Process_Existing_DU_Map_03=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Existing_DU_Map_03.py
set Process_Approved_DU_Map_04=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Approved_DU_Map_04.py
set Process_Grading_In_Process_Map_05=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Grading_In_Process_Map_05.py
set Process_In_Process_DU_Map_07=%wkg_folder%\Source_Code\DEV_TRACKER_Process_In_Process_DU_Map_07.py
set Process_In_Process_GPA_Map_08_A=%wkg_folder%\Source_Code\DEV_TRACKER_Process_In_Process_GPA_Map_08_A.py
set Process_In_Process_GPA_Map_08_B=%wkg_folder%\Source_Code\DEV_TRACKER_Process_In_Process_GPA_Map_08_B.py
set Process_In_Process_GPA_Map_08_C=%wkg_folder%\Source_Code\DEV_TRACKER_Process_In_Process_GPA_Map_08_C.py
set Process_GP_Delta_Map_09=%wkg_folder%\Source_Code\DEV_TRACKER_Process_GP_Delta_Map_09.py
set Process_Cmpltd_Bld_Permits_Map_11=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Cmpltd_Bld_Permits_Map_11.py
set Process_Annex_Aquitns_Map_12=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Annex_Aquitns_Map_12.py

::Set paths to BINNING script
set Bin_Processed_Data=%wkg_folder%\Source_Code\DEV_TRACKER_Bin_Processed_Data.py

::Set paths to PROCESSING scripts that should be run AFTER the BINNING script (because they use binned data)
set Process_Curnt_Dev_Potentl_Map_06=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Curnt_Dev_Potentl_Map_06.py
set Process_Future_Dev_Potentl_Map_10=%wkg_folder%\Source_Code\DEV_TRACKER_Process_Future_Dev_Potentl_Map_10.py

::Set path to LAST_DATA_UPDATE script
set Update_LAST_DATA_UPDATE=%wkg_folder%\Source_Code\DEV_TRACKER_Update_LAST_DATA_UPDATE.py

::Set path to MXD to PDF script
set Export_MXD_to_PDF=%wkg_folder%\Source_Code\DEV_TRACKER_Export_MXD_to_PDF.py

::Set path to Create_QA_QC script
set Create_QA_QC_File=%wkg_folder%\Source_Code\DEV_TRACKER_Create_QA_QC_File.py


::START RUNNING SCRIPTS
echo -----------------------[START %date% %time%]------------------->>%log%


::Format Original CSV Extracts so they can be imported to FGDB Tables
echo Running %Format_CSV_Extracts%>>%log%
Start /wait  %Format_CSV_Extracts%


::Process Map 02 Using SDE GIS Data
echo Running %Process_Approved_GPA_Map_02%>>%log%
Start /wait  %Process_Approved_GPA_Map_02%

::Process Map 03 Using Extract
echo Running %Process_Existing_DU_Map_03%>>%log%
Start /wait  %Process_Existing_DU_Map_03%

::Process Map 04 Using Extract
echo Running %Process_Approved_DU_Map_04%>>%log%
Start /wait  %Process_Approved_DU_Map_04%

::Process Map 05 Using Extract
echo Running %Process_Grading_In_Process_Map_05%>>%log%
Start /wait  %Process_Grading_In_Process_Map_05%

::Process Map 07 Using Extract
echo Running %Process_In_Process_DU_Map_07%>>%log%
Start /wait  %Process_In_Process_DU_Map_07%

::Process Applicant Initiated GPA Extract
echo Running %Process_In_Process_GPA_Map_08_A%>>%log%
Start /wait  %Process_In_Process_GPA_Map_08_A%

::Process County Initiated GPA Extract
echo Running %Process_In_Process_GPA_Map_08_B%>>%log%
Start /wait  %Process_In_Process_GPA_Map_08_B%

::Process Map 08 Using Data from "Map_08_A" and "Map_08_B"
echo Running %Process_In_Process_GPA_Map_08_C%>>%log%
Start /wait  %Process_In_Process_GPA_Map_08_C%

::Process Map 09 Using READY2BIN Data from Maps 4, 7
echo Running %Process_GP_Delta_Map_09%>>%log%
Start /wait  %Process_GP_Delta_Map_09%

::Process Map 11 Using Extract
echo Running %Process_Cmpltd_Bld_Permits_Map_11%>>%log%
Start /wait  %Process_Cmpltd_Bld_Permits_Map_11%

::Process Map 12 Using SDE GIS Data
echo Running %Process_Annex_Aquitns_Map_12%>>%log%
Start /wait  %Process_Annex_Aquitns_Map_12%


:: Bin Processed Data
echo Running %Bin_Processed_Data%>>%log%
Start /wait  %Bin_Processed_Data%


::Process Map 06 Using BINNED Data from Maps 1, 2, 3, 4, 12
echo Running %Process_Curnt_Dev_Potentl_Map_06%>>%log%
Start /wait  %Process_Curnt_Dev_Potentl_Map_06%

::Process Map 10 Using BINNED Data from Maps 6, 7, 8
echo Running %Process_Future_Dev_Potentl_Map_10%>>%log%
Start /wait  %Process_Future_Dev_Potentl_Map_10%


::Update the Date for each Map
echo Running %Update_LAST_DATA_UPDATE%>>%log%
Start /wait  %Update_LAST_DATA_UPDATE%


::If no ERROR files created, then Export MXD to PDF
::Export MXD to PDF
echo Running %Export_MXD_to_PDF%>>%log%
Start /wait  %Export_MXD_to_PDF%


::Create a QA/QC file with the most recent log file from each script (Run regardless of SUCCESS/ERROR files)
echo Running %Create_QA_QC_File%>>%log%
Start /wait  %Create_QA_QC_File%


echo -----------------------[END %date% %time%]--------------------->>%log%
echo ---------------------------------------------------------------------------->>%log%
echo ---------------------------------------------------------------------------->>%log%
echo ---------------------------------------------------------------------------->>%log%