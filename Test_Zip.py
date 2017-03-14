import zipfile, os, time, shutil

#http://stackoverflow.com/questions/14438928/python-zip-a-sub-folder-and-not-the-entire-folder-path
# above site can be used to find out how to remove the entire path from the zipped folder

working_folder = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data'
FGDB_to_zip = working_folder + '\\DPW_Science_and_Monitoring_prod.gdb'
file_to_zip = working_folder + '\\test.txt'

where_to_zip = working_folder + '\\DPW_Science_and_Monitoring.zip'

if os.path.exists(where_to_zip):
    os.remove(where_to_zip)

time.sleep(2)

#-------------------------------------------------------------------------------
#                             Zip the files
with zipfile.ZipFile (where_to_zip, 'w') as zip_obj:
    zip_obj.write(file_to_zip)

##os.chdir(working_folder)
####os.chdir = working_folder
##shutil.make_archive('DPW_Science_and_Monitoring_prod', 'zip', file_to_zip)


# Create container for the zip
##with zipfile.ZipFile (where_to_zip, 'w') as zip_obj:
##    for root, dirs, files in os.walk(file_to_zip):
##        for f in files:
##            zip_obj.write(os.path.join(root, file))

##    # Zip the file
##    zip_obj.write(file_to_zip)