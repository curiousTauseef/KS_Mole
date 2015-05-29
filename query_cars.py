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
import sys

######## Functions #############

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

def get_entity_mentions(mid):
        authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
        authinfo.add_password(None, SERVER, username, password)
        q = {'id': mid}
        page = 'HTTPS://'+ SERVER +'/nwr/' + dataset + '/mentions?' + urllib.urlencode(q)
        handler = urllib2.HTTPBasicAuthHandler(authinfo)
        myopener = urllib2.build_opener(handler)
        opened = urllib2.install_opener(myopener)
        output = urllib2.urlopen(page)
        results = json.loads(output.read())
        print results["@graph"][0]["ks:refersTo"]["@id"]

def get_eso_roles():
	query = "SELECT ?role WHERE { ?role nwr:isRolePropertyDefinedBy eso: }"
	results = query_ks(query)
	roles = []
	for r in results:
		roles.append(str(r["role"]["value"]))
	return roles

def get_fn_roles():
	query = "SELECT DISTINCT ?role WHERE { ?role nwr:isPropertyDefinedBy framenet: }"
        results = query_ks(query)
        roles = []
        for r in results:
                roles.append(str(r["role"]["value"]))
        return roles

####### Specific queries #############

# PropBank ROLES AND ENTITIES/E-TYPES
# 1
def get_pbroles_and_entities(): # Postprocessing needed: NO
#	for x in ["0", "1", "2", "3", "4", "5"]: # Iterate through the roles
	for x in ["M-LOC"]:
		w=open("a" + x + ".csv", "w")
		# compose role uri
		role_uri = "<http://www.newsreader-project.eu/ontologies/propbank/A" + x + ">"
		# compose query
		query = "SELECT ?entity (COUNT(?entity) AS ?cent) WHERE { ?event " + role_uri + " ?entity } GROUP BY ?entity ORDER BY DESC(?cent)"
		# POSE THE QUERY
		results = query_ks(query)
		# Print results
		for result in results:
			w.write("%s %s %d\n" % (role_uri, iriToUri(result["entity"]["value"]), int(result["cent"]["value"])))
		w.close()

# 2
def get_pbroles_and_entitytypes(): # Postprocessing needed: NO
#	for x in ["0", "1", "2", "3", "4", "5"]: # Iterate through the roles
        for x in ["M-LOC"]:
		w=open("a" + x + ".csv", "w")
                # compose role uri
                role_uri = "<http://www.newsreader-project.eu/ontologies/propbank/A" + x + ">"
                # compose query
                query = "SELECT ?class (COUNT(?entity) as ?cent) WHERE { ?event " + role_uri + " ?entity . GRAPH ?g { ?entity rdf:type ?class .} ?g dct:source db: } GROUP BY ?class ORDER BY DESC(?cent)"
                # POSE THE QUERY
                results = query_ks(query)
                # Print results
                for result in results:
                        w.write("%s %s %d\n" % (role_uri, iriToUri(result["class"]["value"]), int(result["cent"]["value"])))
		w.close()

# ESO ROLES AND ENTITIES/E-TYPES
# 3
def get_esoroles_and_entities(): # Postprocessing needed: NO
	for role in get_eso_roles():
		w=open("eso_" + role.split("#")[1] + ".csv", "w")
		role_uri="<" + role + ">"
		# compose query
                query = "SELECT ?entity (COUNT(?entity) AS ?cent) WHERE { ?event " + role_uri + " ?entity } GROUP BY ?entity ORDER BY DESC(?cent)"
                print query
		# POSE THE QUERY
                results = query_ks(query)
                # Print results
                for result in results:
                        w.write("%s %s %d\n" % (role_uri, iriToUri(result["entity"]["value"]), int(result["cent"]["value"])))
                w.close()

# 4
def get_esoroles_and_entitytypes():
	for role in get_eso_roles():
		w=open("eso_" + role.split("#")[1] + ".csv", "w")
		role_uri="<" + role + ">"
		# compose query
		query = "SELECT ?class (COUNT(?entity) as ?cent) WHERE { ?event " + role_uri + " ?entity . GRAPH ?g { ?entity rdf:type ?class .} ?g dct:source db: } GROUP BY ?class ORDER BY DESC(?cent)"
                # POSE THE QUERY
                results = query_ks(query)
                # Print results
                for result in results:
                        w.write("%s %s %d\n" % (role_uri, iriToUri(result["class"]["value"]), int(result["cent"]["value"])))
                w.close()
               
# FN ROLES AND ENTITIES/E-TYPES
# 5
def get_fnroles_and_entities(): # Postprocessing needed: NO
        for role in get_fn_roles():
                w=open("csvs/5_fnroles_entities/fn_" + role.split("framenet/")[1] + ".csv", "w")
                role_uri="<" + role + ">"
                # compose query
                query = "SELECT ?entity (COUNT(?entity) AS ?cent) WHERE { ?event " + role_uri + " ?entity } GROUP BY ?entity ORDER BY DESC(?cent)"
                print query
                # POSE THE QUERY
                results = query_ks(query)
                # Print results
                for result in results:
                        w.write("%s %s %d\n" % (role_uri, iriToUri(result["entity"]["value"]), int(result["cent"]["value"])))
                w.close()

# 6
def get_fnroles_and_entitytypes():
        for role in get_fn_roles():
                w=open("csvs/6_fnroles_entitytypes/fn_" + role.split("framenet/")[1] + ".csv", "w")
                role_uri="<" + role + ">"
                # compose query
                query = "SELECT ?class (COUNT(?entity) as ?cent) WHERE { ?event " + role_uri + " ?entity . GRAPH ?g { ?entity rdf:type ?class .} ?g dct:source db: } GROUP BY ?class ORDER BY DESC(?cent)"
                # POSE THE QUERY
                results = query_ks(query)
                # Print results
                for result in results:
                        w.write("%s %s %d\n" % (role_uri, iriToUri(result["class"]["value"]), int(result["cent"]["value"])))
                w.close()

###### ENTITY-ENTITY #########

def get_actors_in_events(): # Postprocessing needed: YES
	query = 'SELECT ?actor1 ?actor2 WHERE { ?a rdf:type sem:Event . ?a sem:hasActor ?actor1, ?actor2 . FILTER(str(?actor1) < str(?actor2)) }'
	# POSE THE QUERY
	results = query_ks(query)
	# Print 2 results
	for result in results:
                print iriToUri(result["actor1"]["value"]), iriToUri(result["actor2"]["value"])

# 11
def get_cooccurring_entity_types():
	w=open("cooc_ent_types.csv", "w")
	query = 'SELECT ?t1 ?t2 (COUNT(?a) as ?cnt) WHERE { ?event rdf:type sem:Event . ?event sem:hasActor ?a . ?a rdf:type ?t1 . ?a rdf:type ?t2 . FILTER(?t1<?t2) } GROUP BY ?t1 ?t2 ORDER BY DESC(?cnt)'
	# POSE THE QUERY
        results = query_ks(query)
        # Print 2 results
        for result in results:
                w.write("%s %s %d\n" % (iriToUri(result["t1"]["value"]), iriToUri(result["t2"]["value"]), int(result["cnt"]["value"])))
	w.close()
	

###### MENTIONS #############
	
def get_all_mentions():
	query='SELECT DISTINCT ?mention WHERE { ?x gaf:denotedBy ?mention }'

	results=query_ks(query)

	for result in results:
		print iriToUri(result["mention"]["value"])

def get_all_event_mentions():
        query='SELECT DISTINCT ?mention WHERE { ?event rdf:type sem:Event . ?event gaf:denotedBy ?mention }'

        results=query_ks(query)

        for result in results:
                print iriToUri(result["mention"]["value"])

###### ROLE-ROLE #######

def get_cooc_roles():
	query = 'SELECT ?propa ?propb (COUNT(?entx) AS ?cnt) WHERE { ?event rdf:type sem:Event . ?event sem:hasActor ?entx . ?event ?propa ?entx . ?event ?propb ?entx . FILTER(STR(?propa)!=STR(?propb)) } GROUP BY ?propa ?propb ORDER BY ?cnt'
	# POSE THE QUERY
        results = query_ks(query)
        # Print 2 results
        for result in results:
                print iriToUri(result["propa"]["value"]), iriToUri(result["propb"]["value"]), result["cnt"]["value"]

# 8
def get_cooccurring_eso_roles():
	w=open("cooc_eso.csv", "w")
	query = "SELECT ?prop1 ?prop2 (COUNT(?entity) as ?cnt) WHERE { ?event rdf:type sem:Event . ?event ?prop1 ?entity . ?event ?prop2 ?entity . FILTER(?prop1<?prop2) . ?prop1 nwr:isPropertyDefinedBy eso: . ?prop2 nwr:isPropertyDefinedBy eso: } GROUP BY ?prop1 ?prop2 ORDER BY DESC(?cnt)"
	 # POSE THE QUERY
	results = query_ks(query)
	# Print results
	for result in results:
		w.write("%s %s %d\n" % (iriToUri(result["prop1"]["value"]), iriToUri(result["prop2"]["value"]), int(result["cnt"]["value"])))
	w.close()

# 9
def get_cooccurring_fn_roles():
	w=open("cooc_fn.csv", "w")
	query = "SELECT ?prop1 ?prop2 (COUNT(?entity) as ?cnt) WHERE { ?event rdf:type sem:Event . ?event ?prop1 ?entity . ?event ?prop2 ?entity . FILTER(?prop1<?prop2) . ?prop1 nwr:isPropertyDefinedBy framenet: . ?prop2 nwr:isPropertyDefinedBy framenet: } GROUP BY ?prop1 ?prop2 ORDER BY DESC(?cnt)"
	 # POSE THE QUERY
	results = query_ks(query)
	# Print results
	for result in results:
		w.write("%s %s %d\n" % (iriToUri(result["prop1"]["value"]), iriToUri(result["prop2"]["value"]), int(result["cnt"]["value"])))
	w.close()

# 10
def get_cooccurring_pb_roles():
	w=open("cooc_pb.csv", "w")
	query = "SELECT ?prop1 ?prop2 (COUNT(?entity) as ?cnt) WHERE { ?event rdf:type sem:Event . ?event ?prop1 ?entity . ?event ?prop2 ?entity . FILTER(?prop1<?prop2) . ?prop1 nwr:isPropertyDefinedBy <http://www.newsreader-project.eu/ontologies/propbank/> . ?prop2 nwr:isPropertyDefinedBy <http://www.newsreader-project.eu/ontologies/propbank/> } GROUP BY ?prop1 ?prop2 ORDER BY DESC(?cnt)"
	 # POSE THE QUERY
	results = query_ks(query)
	# Print results
	for result in results:
		w.write("%s %s %d\n" % (iriToUri(result["prop1"]["value"]), iriToUri(result["prop2"]["value"]), int(result["cnt"]["value"])))
	w.close()

####### GENERAL SETTINGS #############
dataset = "cars2" # Can be "cars2" or "dutchhouse"
SERVER = "knowledgestore2.fbk.eu"
username="nwr_partner"
password="ks=2014!"

####### MAIN ################
if __name__ == "__main__":
      
	if len(sys.argv)<2:
		print "Choose what to execute by entering a number"
		sys.exit()
	choice = sys.argv[1]

	##### #1-#6 get the co-occurrence of roles (fn, pb, eso) and entities/entity types
	if choice=="1":
		get_pbroles_and_entities() #  propbank roles and specific entities
        elif choice=="2":
		get_pbroles_and_entitytypes() # propbank roles and specific entity types
	elif choice=="3":
		get_esoroles_and_entities() # eso roles and specific entities
	elif choice=="4":
		get_esoroles_and_entitytypes() # eso roles and entity types
	elif choice=="5":
		get_fnroles_and_entities() # fn roles and entities
	elif choice=="6":
		get_fnroles_and_entitytypes() # fn roles and entity types
	elif choice=="7":
		get_actors_in_events() # pairs of actors which co-occur in the same event
	elif choice=="8":
		get_cooccurring_eso_roles() # pairs of eso roles that cooccur for the same entity
        elif choice=="9":
                get_cooccurring_fn_roles() # pairs of fn roles that cooccur for the same entity
	elif choice=="10":
		get_cooccurring_pb_roles() # pairs of pb roles that cooccur for the same entity
	elif choice=="11":
		get_cooccurring_entity_types() # pairs of entity types which cooccur for given entity mention
	elif choice=="m":
		get_all_mentions()
	elif choice=="evm":
		get_all_event_mentions()
	elif choice=="e":
		get_entity_mentions("<http://www.newsreader-project.eu/data/cars/2005/08/14/4GW8-V1N0-TWMD-626C.xml#char=232,242>") 
	else:
		print "You have entered incorrect value. Try again!" 
