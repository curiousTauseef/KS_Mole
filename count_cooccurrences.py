#!/usr/bin/python

import sys
import json
import re, urlparse
from elasticsearch import Elasticsearch,helpers
import itertools

def my_generator(my_jsons):
    for a in my_jsons:
        yield a

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

	es = Elasticsearch()

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
#	es.indices.create('entlemmas')
	c=0
	print "Aggregation done. Now going to sort and bulk store..."
	list_of_jsons=[]
	for row in sorted(result.items(), key = lambda t: t[1], reverse=True):
		arrk = json.loads(row[0])
		uri_link=iriToUri(arrk[0]) 
		mention=iriToUri(arrk[1])
		cnt=row[1]
		list_of_jsons.append({'_type': 'entl', '_index': 'entitylemmas', 'urilink': uri_link, 'mention': mention, 'predicate': cnt})
		c+=1
		if c==5000:
			helpers.bulk(es, my_generator(list_of_jsons))
			list_of_jsons=[]
			c=0
			print "Stored 2000"
	if c>0:
		helpers.bulk(es, my_generator(list_of_jsons))
		print "Stored " + str(c)
