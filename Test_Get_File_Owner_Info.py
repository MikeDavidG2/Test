#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     15/06/2018
# Copyright:   (c) mgrue 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os, getpass

def main():


    folder_to_analyze = raw_input('What root folder contains the files you want to get owner info?')
    ##folder_to_analyze = r'U:\yakos\hep_A\PROD'  # Uncomment out this line to force a specific folder_to_analyze
    print 'Folder to analyze: {}'.format(folder_to_analyze)

    # Get the User ID for the currently logged in account
    user_name = getpass.getuser()
    domain = os.environ['USERDOMAIN']
    user_id = os.path.join(domain, user_name)

    ##user_id = 'BLUE\mgrue'  # Uncomment out this line to force a specific user_id
    print 'User ID: {}'.format(user_id)

    # Create counters for reporting purposes
    num_files_analyzed     = 0
    files_owned_by_user_id   = []
    files_owned_by_others    = []
    files_without_owner_info = []


    for root, directories, filenames in os.walk(folder_to_analyze):
        ##print 'Root: {}'.format(root)
        ##print 'Directory: {}'.format(directories)
        ##print 'File name: {}\n'.format(filenames)

        # Analyze all the files in the folder_to_analyze
        for filename in filenames:

            # Don't try to analyze files in a FGDB
            if not root.endswith('.gdb'):

                file_path = os.path.join(root, filename)

                # Don't try to analyze some file types (i.e. Thumbs.db)
                if not file_path.endswith('db'):

                    print 'Getting Owner Information for FILE:\n  {}'.format(file_path)
                    owner = Get_Owner_Info(file_path)

                    # Print based on the result from Get_Owner_Info() and increase
                    # the count for the respective counter
                    if owner == '':
                        print 'Owner:\n  !WARNING! There was no owner information'
                        files_without_owner_info.append(file_path)

                    elif owner == user_id:
                        print 'Owner:\n  YOU are the owner of this file, {}'.format(owner)
                        files_owned_by_user_id.append(file_path)

                    else:
                        print 'Owner:\n  {}'.format(owner)
                        files_owned_by_others.append(file_path)

                    num_files_analyzed += 1

                    print '\n--------------------------------------------------'

    print '\n\n----------------------------------------------------------------'
    print '----------------------------------------------------------------'
    print 'REPORTING:'

    if len(files_owned_by_user_id) > 0:
        print '\n\n  FILES OWNED BY "{}":'.format(user_id)
        for f in files_owned_by_user_id:
            print '    {}'.format(f)

    if len(files_owned_by_others) > 0:
        print '\n\n  FILES OWNED BY OTHERS:'
        for f in files_owned_by_others:
            print '    {}'.format(f)

    if len(files_without_owner_info) > 0:
        print '\n\n  FILES WITHOUT OWNER INFORMATION:'
        for f in files_without_owner_info:
            print '    {}'.format(f)


    print '\n\n  {} = Total Number of Files Analyzed'.format(num_files_analyzed)
    print '  {} = Number of files owned by "{}"'.format(len(files_owned_by_user_id), user_id)
    print '  {} = Number of files owned by another user'.format(len(files_owned_by_others))
    print '  {} = Number of files without owner information'.format(len(files_without_owner_info))
    print '\n  NOTE: Folders are not checked for owner information.'
    print '  Keep this in mind if a script needs to delete a folder owned by someone else.'
    print '\n  This also means that FGDBs (which are folders) are not checked for ownership.'
    print '  Files inside of a FGDB are also not checked for ownership'
    print '  Keep this in mind if a script needs to edit a FGDB owned by someone else.'

    raw_input('Press ENTER to continue')
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Get_Owner_Info(path):
    """
    """

    # Create the owner variable here in case owner information is not found
    owner = ''

    # Get directory info for that file and split any whitespace into a list
    print os.popen('dir /q "{}"'.format(path)).read()  # For testing
    file_info_ls = os.popen('dir /q "{}"'.format(path)).read().split()
    ##print file_info_ls  # For testing

    # Find the Owner info from the list
    # The format for the owner info should be something like 'BLUE\<user_id>'
    for element in file_info_ls:
        if element.startswith('BLUE'):
            owner = element
            break

    ##print 'Owner: {}'.format(owner)  # For testing

    return owner


#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()


