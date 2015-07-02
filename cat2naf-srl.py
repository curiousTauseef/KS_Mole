#!/usr/bin/env python

# This script reads a CAT XML file and converts it to NAF XML
# This script also takes into account the named entities from the CROMER layer that 
# were already included in the CAT files by FBK.

# It writes the SRL Layer 

# Date: 20 April 2015
# Author: Marieke van Erp  
# Contact: marieke.van.erp@vu.nl 

import sys
from KafNafParserPy import *
import re

#infile = open('Data/wikinews_CAT_CROMER_160415/corpus_airbus/1173_Internal_emails_expose_Boeing-Air_Force_contract_discussions.txt.xml',"r")
infile = open(sys.argv[1],"r")
raw = infile.read()    
root = etree.XML(raw)

# Make a list of all the tokens:
token_list = root.findall(".//token")
num_sents = int(token_list[-1].get("sentence"))

# Init KafNafParserobject
my_parser = KafNafParser(None, type='NAF')
my_parser.root.set('{http://www.w3.org/XML/1998/namespace}lang','en')
my_parser.root.set('version','v3')
textlayer = Ctext()
termlayer = Cterms()

offset = 0
num = 0 
rawtext = '' 

sents = [root.findall(".//token[@sentence='%s']" % str(n)) for n in range(0,num_sents + 1)]
for sent in sents:
	num = num + 1 
	for node in sent:
		wf = Cwf() 
		wf.set_id(node.get("t_id"))
		sentence_no = int(node.get("sentence")) + 1
		wf.set_sent(str(sentence_no))
		wf.set_para("1")
		wf.set_offset(str(offset))
		offset = offset + len(node.text)
		wf.set_length(str(len(node.text)))
		wf.set_text(node.text)
		my_parser.add_wf(wf)
		term = Cterm()
		term.set_id(node.get("t_id"))
		term.set_lemma(node.text)
		term_span = Cspan()
		term_target = Ctarget()
		term_target.set_id(node.get("t_id"))
		term_span.add_target(term_target)
		term.set_span(term_span)
		my_parser.add_term(term)
		rawtext = rawtext + " " + node.text
        
# Create the raw text layer 
rawlayer = my_parser.set_raw(rawtext) 
        
# Initialise the mentions dictionary to capture all the CAT mentions         
mention_ids = {}

# get a list of all entity mentions :
entity_mentions_list = root.findall(".//ENTITY_MENTION")
for entity in entity_mentions_list:
    mention_ids[entity.get("m_id")] = []
    entity_mention_anchors = entity.findall(".//token_anchor")
    for tokens in entity_mention_anchors:
        mention_ids[entity.get("m_id")].append(tokens.get("t_id"))
         
# get a list of all event mentions :
event_mentions_list = root.findall(".//EVENT_MENTION")
for event in event_mentions_list:
    mention_ids[event.get("m_id")] = []
    event_mention_anchors = event.findall(".//token_anchor")
    for tokens in event_mention_anchors:
        mention_ids[event.get("m_id")].append(tokens.get("t_id"))
     
# get a list of all timex mentions :
timex_mentions_list = root.findall(".//TIMEX3")
for timex in timex_mentions_list:
    mention_ids[timex.get("m_id")] = []
    timex_mention_anchors = timex.findall(".//token_anchor")
    for tokens in timex_mention_anchors:
        mention_ids[timex.get("m_id")].append(tokens.get("t_id"))
        
        
# Get a list of all the SRL relations
srl_mentions_list = root.findall(".//HAS_PARTICIPANT")
srl_sources = {}
srl_targets = {}
srl_predicates = {}
srl_roles = {}
for srl in srl_mentions_list:
    srl_source_mentions = srl.findall(".//source")
    srl_target_mentions = srl.findall(".//target")
    srl_targets[srl.get("r_id")] = srl_target_mentions[0].get("m_id")
    srl_sources[srl.get("r_id")] = srl_source_mentions[0].get("m_id")
    srl_roles[srl.get("r_id")] = srl.get("sem_role")
    if srl_source_mentions[0].get("m_id") in srl_predicates:
        srl_predicates[srl_source_mentions[0].get("m_id")].append(srl.get("r_id"))
    else:
        srl_predicates[srl_source_mentions[0].get("m_id")] = []
        srl_predicates[srl_source_mentions[0].get("m_id")].append(srl.get("r_id"))
       
# Create NAF SRL objects
for predicate in srl_predicates:
    new_predicate = Cpredicate()
    new_predicate.set_id('pr'+ str(predicate))
    source_target = Ctarget()
    predicate_span = Cspan()
    source_target.set_id(predicate)
    predicate_span.add_target(source_target)
    new_predicate.set_span(predicate_span)
    my_parser.add_predicate(new_predicate)
    for relation in srl_predicates[predicate]:
        role = Crole()
        role.set_id(relation)
        role.set_sem_role(srl_roles[relation])
        target = Ctarget()
        target_span = Cspan()
        for item in mention_ids[srl_targets[relation]]:
            target.set_id(item)
            target_span.add_target(target)
            role.set_span(target_span)
        new_predicate.add_role(role)	
        

# Print the whole thing 
my_parser.dump()
        