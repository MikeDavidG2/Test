
import datetime

UNIX_timestamp = '1492718741'

daily_unique_timestamp = '529009'


# Unique number should be 'YYYYMMDD'+daily_unique_timestamp
yyyymmdd = datetime.datetime.fromtimestamp(int(UNIX_timestamp)).strftime('%Y%m%d')

print yyyymmdd + daily_unique_timestamp


