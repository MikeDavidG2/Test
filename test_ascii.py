s = 'jkl;lkjlkj?lk'

print type(s)

s = unicode(s, 'utf-8')

print type(s)

try:
    s.decode('ascii')

except UnicodeDecodeError:
    print 'not ascii'

print s
##else:
##    print 'maybe ascii'