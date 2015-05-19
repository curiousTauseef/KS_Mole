#!/usr/bin/python

import sys
import json

if __name__ == "__main__":
	infile=""
	if len(sys.argv)<2:
		print "Please add the filename to postprocess as an argument. Usage (output file is optional): python count_cooccurrences.py inputfile > outputfile\n\npython count_cooccurrences.py file.csv > out.csv"
		sys.exit()
	infile = sys.argv[1]

	result = {}
	with open(infile, "r") as f:
		for line in f:
			if line.strip()=="":
				continue
			larray=line.split()
			if json.dumps(larray) in result:
				result[json.dumps(larray)]+=0.5
			elif json.dumps([larray[1],larray[0]]) in result:
				result[json.dumps([larray[1],larray[0]])]+=0.5
			else:
				result[json.dumps(larray)]=0.5
	for k in result:
		arrk = json.loads(k)
		print arrk[0], arrk[1], int(result[k])
