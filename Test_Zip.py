import zipfile, os

#http://stackoverflow.com/questions/14438928/python-zip-a-sub-folder-and-not-the-entire-folder-path
# above site can be used to find out how to remove the entire path from the zipped folder

working_folder = r'C:\Users\MikeG\Scripts\Developing_Locally\Test_Zipfile'
file_to_zip = working_folder + '\FileToZip.txt'
where_to_zip = working_folder + '\DPW_FGDB.zip'

##pwd = os.getcwd()
##print pwd

# Create container for the zip
with zipfile.ZipFile (where_to_zip, 'w') as DPW_zip:
    # Zip the file
    DPW_zip.write(file_to_zip)