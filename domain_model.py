#!/usr/bin python

from KafNafParserPy import *
import os
import sys
sys.path.append('./')
from dbpediaEnquirerPy import *

##########################################################################################
################################### HELPER FUNCTIONS #####################################
##########################################################################################

def get_start_term(parser):
	# Find the start of sentence 2 (after title)
	for token in parser.get_tokens():
		if token.get_sent()=="2":
			token_after_title=int(token.get_id().replace("w", ""))
			break		
	# Process from sentence 2 on
	# First find the appropriate term where sentence 2 starts
	for term in parser.get_terms():
		target_ids=term.get_span().get_span_ids()
		if int(target_ids[0].replace("w", ""))>=token_after_title:
			term_after_title=int(term.get_id().replace("t", ""))
			break
	return term_after_title

def get_most_confident_link(e):
	maxconf=-0.1
	maxref=None
	for ref in e.get_external_references():
		if ref.get_resource()=="spotlight_v1" and float(ref.get_confidence())>maxconf:
			maxconf=float(ref.get_confidence())
			maxref=ref.get_reference()
	return maxref

def get_entity_mention(parser, terms):
    	term_text=[]
	for t in terms:
		term=parser.get_term(t)
		target_ids=term.get_span().get_span_ids()
		for tid in target_ids:
            		term_text.append(parser.get_token(tid).get_text())
        res=(" ").join(term_text)
	return res

def get_initials(entity_string):
	initials=""
	ent_split=entity_string.split()
	if len(ent_split)>1:
		for word in ent_split:
			#if word.isupper():
			#	initials+=word
			if word[0].isupper():
				initials+=word[0]
	else:
		initials=None
	return initials

def is_person(dblink):
	return not dblink or ('http://dbpedia.org/ontology/Person' in my_dbpedia.get_dbpedia_ontology_labels_for_dblink(dblink))

def add_entity_extref(entity, extref):
	#print entity, extref
	my_ext_ref = CexternalReference()
	my_ext_ref.set_reference(extref)
	my_ext_ref.set_resource('domain_model')
	my_ext_ref.set_confidence('1.0')
	entity.add_external_reference(my_ext_ref)
	return entity

##########################################################################################
####################################### MODULES ##########################################
##########################################################################################

def get_previous_occurrence(all_entities, entity_string): #1
	extref=None
	for ekey in all_entities:
		#print entity_string, ekey
		if entity_string==ekey or (entity_string in ekey.split() and is_person(all_entities[ekey]["extref"])): 
			extref=all_entities[ekey]["extref"]
			print "D1", entity_string, ekey, extref
	return extref

def solve_initials_and_abbreviations_before(entity_string, all_entities): #2
	#2 Initials and abbreviations
	extref=None
	for ekey in all_entities:
		if entity_string==all_entities[ekey]["initials"]:
			extref=all_entities[ekey]["extref"]
			print "D2", entity_string, ekey, extref
	return extref

def solve_initials_and_abbreviations_after(entity_string, term_id, parser): #3
	#2 Initials and abbreviations
	extref=None
	for other_entity in parser.get_entities():
		if other_entity.get_id()[0]=="g":
			continue
		for ref in other_entity.get_references():
			terms=ref.get_span().get_span_ids()
		if int(terms[0].replace("t", ""))<=term_id:
			continue
		other_entity_string = get_entity_mention(parser, terms)
		other_initials=get_initials(other_entity_string)
		if other_initials and entity_string==other_initials:
			extref=get_most_confident_link(other_entity)
			print "D3", entity_string, other_entity_string, extref
			break
	return extref

def do_disambiguation(entity_string, all_entities, terms, parser):
			
	extref=get_previous_occurrence(all_entities, entity_string); #D1  Get previous occurrence


	if not extref:
		if len(entity_string.split())==1 and entity_string.isupper():
			extref = solve_initials_and_abbreviations_before(entity_string, all_entities) or solve_initials_and_abbreviations_after(entity_string, terms[0].replace("t", ""), parser)
		#D2 Initials and abbreviations of occurred entities
		#D3 Initials and abbreviations explained afterwards
		
	return extref


##########################################################################################
####################################### MAIN #############################################
##########################################################################################

if __name__=="__main__":
	my_dbpedia = Cdbpedia_enquirer()
	path="dev_corpus/"
	out_path="proc_dev_corpus/"
	count_all = 0
	count_dis=0
	for file in os.listdir(path):
		print file
		parser=KafNafParser(path + file)

		term_start = get_start_term(parser) # Get the first term in sentence 2 to avoid the title

		all_entities={}
		for entity in parser.get_entities():
			if entity.get_id()[0]=="g":
				continue
			for ref in entity.get_references():
				terms=ref.get_span().get_span_ids()
			if int(terms[0].replace("t", ""))<term_start:
				continue
			
			entity_string = get_entity_mention(parser, terms)
			
			############ THE RULES START FROM HERE ONWARDS #############
			
			########### Disambiguation #############
			
			extref=do_disambiguation(entity_string, all_entities, terms, parser)
			if extref:
				entity=add_entity_extref(entity, extref)
				count_dis+=1

			############ Recognition ###############
			if not extref and len(entity_string.split())==1 and not get_most_confident_link(entity) and "-" in entity_string: # R3
				found=False
				for new_ent in entity_string.split("-"):
					extref=do_disambiguation(new_ent, all_entities, terms, parser)
					if extref:
						found=True
						entity=add_entity_extref(entity, extref)
						print "R3", file, terms, extref

			if not extref:
#				count_after_3+=1
				extref=get_most_confident_link(entity)
				print entity_string
				entity=add_entity_extref(entity, extref)
			count_all+=1
			all_entities[entity_string]={"extref": extref, "terms": terms, "initials": get_initials(entity_string)}
		parser.dump(out_path + file)
	print count_all, count_dis