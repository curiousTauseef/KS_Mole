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
	authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
	authinfo.add_password(None, SERVER, username, password)
	q = {'query': query}
	page = 'HTTPS://'+ SERVER +'/nwr/' + dataset + '/sparql?' + urllib.urlencode(q)
	handler = urllib2.HTTPBasicAuthHandler(authinfo)
	myopener = urllib2.build_opener(handler)
	opened = urllib2.install_opener(myopener)
	output = urllib2.urlopen(page)
	results = json.loads(output.read())["results"]["bindings"]
	return results


####### Specific queries #############
def get_actors_in_events():
	query = 'SELECT * WHERE { ?a sem:hasActor ?actor1 . ?a sem:hasActor ?actor2 . FILTER(str(?actor1) != str(?actor2)) }'
	# POSE THE QUERY
	results = query_ks(query)
	# Print 2 results
	for result in results:
                print iriToUri(result["actor1"]["value"]), iriToUri(result["actor2"]["value"])
	
def get_roles_and_entities():
	for x in ["0", "1", "2", "3", "4", "5"]: # Iterate through the roles
		# compose role uri
		role_uri = "<http://www.newsreader-project.eu/ontologies/propbank/A" + x + ">"
		# compose query
		query = "SELECT * WHERE { ?event " + role_uri + " ?entity }"
		# POSE THE QUERY
		results = query_ks(query)
		# Print results
		for result in results:
			print role_uri, iriToUri(result["entity"]["value"])
		
def get_eventtype_for_entities():
	query = 'SELECT * WHERE { ?event sem:hasActor ?entity . ?event ?eventtype ?entity }'
	# POSE THE QUERY
        results = query_ks(query)
        # Print 2 results
        for result in results:
                print iriToUri(result["entity"]["value"]), iriToUri(result["eventtype"]["value"])


####### GENERAL SETTINGS #############
dataset = "cars2" # Can be "cars2" or "dutchhouse"
SERVER = "knowledgestore2.fbk.eu"
username="nwr_partner"
password="ks=2014!"

####### MAIN ################
if __name__ == "__main__":
	# 1. This query gets all co-occurrences of actors in events (regardless of whether inter- or intra-document)
	#get_actors_in_events()
       
	# 2. This query gets all co-occurrences of semantic roles and specific entities
	get_roles_and_entities()

	# 3. This query returns event types for given entities
	#get_eventtype_for_entities()
