import datetime
import sys
import time

# USAGE: sleeter.py <time_of_day> {additional_day(s)}
# USAGE: sleeper.py 14:00 1 (in order to sleep until next 2pm PLUS 1 day)
# USAGE: sleeper.py 14:00 (in order to sleep until the next 2pm)
try:
    startTime     = str(sys.argv[1]) + ":00" # add seconds
    startTimeDate = datetime.datetime.strptime(str(datetime.date.today()) + " " + str(startTime),"%Y-%m-%d %H:%M:%S")
    timenow       = datetime.datetime.now()
    deltaTime     = startTimeDate - datetime.datetime.now()
    deltaSecs     = int(deltaTime.seconds)

    if len(sys.argv) == 3:
        deltaSecs = deltaSecs + (int(sys.argv[2]) * 86400) # add 24 hours * day(s)

    time.sleep(deltaSecs)
except:
    print "ERROR"
    print "USAGE: sleeter.py <time_of_day> {additional_day(s)}"
    print "USAGE: sleeper.py 14:00 1 (in order to sleep until next 2pm PLUS 1 day)"
    print "USAGE: sleeper.py 14:00 (in order to sleep until the next 2pm)"
    time.sleep(60)


