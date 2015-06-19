#!/usr/bin/python

import sys
import json
import re, urlparse

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )

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
                        larray=line.split("===")
			#larray=line.split()
			if len(larray)!=2:
				continue
			mention=larray[1]
			ent=larray[0]
			if json.dumps(larray) in result:
				result[json.dumps(larray)]+=1
			else:
				result[json.dumps(larray)]=1
	for row in sorted(result.items(), key = lambda t: t[1], reverse=True):
		arrk = json.loads(row[0])
		print iriToUri(arrk[0]), iriToUri(arrk[1]), row[1]

