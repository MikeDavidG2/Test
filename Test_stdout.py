#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      mgrue
#
# Created:     10/02/2017
# Copyright:   (c) mgrue 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sys

def main():
    old_stdout = sys.stdout

    log_file = r'U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\Data\Logs\test.log'

    log_file = open(log_file, 'w')

    print 'this will be written to the screen'

    sys.stdout = log_file

    print 'this will be written to a log file'
    test_func()

    sys.stdout = old_stdout

    print 'this will be written to the screen.'

    log_file.close



def test_func():
    print 'This is in a function'

if __name__ == '__main__':
    main()
