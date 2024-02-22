"""
	A simple script to comment out any '@instrument' lines in a file (passed
		as a command line arg). 
"""

import sys

filename = sys.argv[1]

f = open(filename, "rb")

for line in f:
    if line == "@instrument\n":
        print("# " + line, end=" ")
    else:
        print(line, end=" ")
