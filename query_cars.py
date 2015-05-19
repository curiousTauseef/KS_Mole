'''
Created on May 11, 2015
@author: Filip Ilievski
'''

#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
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

def query_ks(query):
#	print "lsososl"
	authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
	authinfo.add_password(None, SERVER, username, password)
	q = {'query': query}
	page = 'HTTPS://'+ SERVER +'/nwr/' + dataset + '/sparql?' + urllib.urlencode(q)
	handler = urllib2.HTTPBasicAuthHandler(authinfo)
	myopener = urllib2.build_opener(handler)
	opened = urllib2.install_opener(myopener)
	output = urllib2.urlopen(page)
	results = json.loads(output.read())["results"]["bindings"]
	print "Hello"
	for result in results:
		print iriToUri(result["actor1"]["value"]), iriToUri(result["actor2"]["value"])

# GENERAL SETTINGS
dataset = "dutchhouse"
SERVER = "knowledgestore2.fbk.eu"
username="nwr_partner"
password="ks=2014!"
if __name__ == "__main__":
	# This query gets all co-occurrences of actors in events (regardless of whether inter- or intra-document)
	query = 'SELECT * WHERE { ?a sem:hasActor ?actor1 . ?a sem:hasActor ?actor2 . FILTER(str(?actor1) != str(?actor2)) }'
	query_ks(query)
