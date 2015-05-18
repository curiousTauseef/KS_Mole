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

SERVER = 'knowledgestore2.fbk.eu'
authinfo = urllib2.HTTPPasswordMgrWithDefaultRealm()
authinfo.add_password(None, SERVER, 'nwr_partner', 'ks=2014!')
q = {'query': 'SELECT * WHERE { ?a sem:hasActor ?actor1 . ?a sem:hasActor ?actor2 . FILTER(str(?actor1) != str(?actor2)) }'}
#q = {'query': 'SELECT * WHERE { ?a gaf:denotedBy ?article . ?b gaf:denotedBy ?article } LIMIT 10'}
page = 'HTTPS://'+SERVER+'/nwr/dutchhouse/sparql?' + urllib.urlencode(q)
handler = urllib2.HTTPBasicAuthHandler(authinfo)
myopener = urllib2.build_opener(handler)
opened = urllib2.install_opener(myopener)
output = urllib2.urlopen(page)
results = json.loads(output.read())["results"]["bindings"]
for result in results:
	print iriToUri(result["actor1"]["value"]), iriToUri(result["actor2"]["value"])
