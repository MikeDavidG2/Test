set jobdir=U:\grue\Projects\GaryProjects
set script=%jobdir%\scripts\DEH_HMD_FIRST_RESPONDER.py
set script=U:\grue\Scripts\GitHub\Test\DEH_HMD_FIRST_RESPONDER.py
set log=%jobdir%\log_files\DEH_HMD_FIRST_RESPONDER.log

echo ----------------------[START %date% %time%]------------------- >>%log%

echo Running DEH_HMD_FIRST_RESPONDER.py with xml_to_csv functions... >>%log%
Start /wait %script% xml_to_csv >> %log%

timeout /T 5

echo Running DEH_HMD_FIRST_RESPONDER.py with csv_to_fc functions... >>%log%
Start /wait %script% csv_to_fc >> %log%


echo -----------------------[END %date% %time%]--------------------- >>%log%
echo ---------------------------------------------------------------------------- >>%log%
echo ---------------------------------------------------------------------------- >>%log%