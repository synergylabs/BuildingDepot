"""
	A simple script to uncomment any '@instrument' lines in a file (passed
		as a command line arg). 
"""

import sys

filename = sys.argv[1]

f = open(filename, 'rb')

for line in f:
    if line == '# @instrument\n':
        print "@instrument\n",
    else:
        print line,
