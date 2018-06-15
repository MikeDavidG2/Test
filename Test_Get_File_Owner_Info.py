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
import os

def main():

    folder_to_analyze = r'P:\parks\MXDs\17'
    user_id = 'BLUE\mgrue'

    # Create counters for reporting purposes
    total_files_analyzed     = 0
    files_owned_by_user_id   = 0
    files_owned_by_others    = 0
    files_without_owner_info = 0

    # TODO: Find a way to get the current user id
    # TODO: Print out the total number of files checked and how many are owned
    #       by the user_id and how many are not.

    for root, directories, filenames in os.walk(folder_to_analyze):
##        for directory in directories:
##            print os.path.join(root, directory)
##            pass

        # Analyze all the files in the folder_to_analyze
        for filename in filenames:
            file_path = os.path.join(root, filename)

            # Don't try to analyze some file types (i.e. Thumbs.db)
            if not file_path.endswith('db__'):

                print 'Getting Owner Information for file:\n  {}'.format(file_path)
                owner = Get_Owner_Info(file_path)

                # Print based on the result from Get_Owner_Info() and increase
                # the count for the respective counter
                if owner == '':
                    print 'Owner:\n  !WARNING! There was no owner information'
                    files_without_owner_info += 1

                elif owner == user_id:
                    print 'Owner:\n  YOU are the owner of this file, {}'.format(owner)
                    files_owned_by_user_id += 1

                else:
                    print 'Owner:\n  {}'.format(owner)
                    files_owned_by_others += 1

                total_files_analyzed += 1

                print '\n------------------------------------------------------'

    print '\n\n----------------------------------------------------------------'
    print '----------------------------------------------------------------'
    print 'REPORTING:'
    print '  {} = Total Number of Files Analyzed'.format(total_files_analyzed)
    print '  {} = Number of files owned by "{}"'.format(files_owned_by_user_id, user_id)
    print '  {} = Number of files owned by another user'.format(files_owned_by_others)
    print '  {} = Number of files without owner information'.format(files_without_owner_info)

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def Get_Owner_Info(path):
    """
    """

    # Create the owner variable here in case owner information is not found
    owner = ''

    # Get directory info for that file and split any whitespace into a list
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


