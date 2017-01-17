#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      MikeG
#
# Created:     16/01/2017
# Copyright:   (c) MikeG 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import datetime

def main():
    given_time = datetime.datetime(2017, 1, 13, 16, 27, 00, 100000)

    t_delta = datetime.timedelta(hours=-8)

    actual_time = given_time + t_delta

    print 'Given time: %s' % str(given_time)
    print 'Actual time: %s' % str(actual_time)



if __name__ == '__main__':
    main()
