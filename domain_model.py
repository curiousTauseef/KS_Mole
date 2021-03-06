#!/usr/bin python

"""
Domain model for NED, NewsReader project.

@author: U{Filip Ilievski<filipilievski.wordpress.com>}
@version: 0.1
@contact: U{f.ilievski@vu.nl<mailto:f.ilievski@vu.nl>} 
@since: 08-Jul-2015
"""

__version__ = '0.1'
__modified__ = '08Jul2015'
__author__ = 'Filip Ilievski'

from KafNafParserPy import *
import os
import sys
import json
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

def get_entity_terms(entity):
	for ref in entity.get_references():
		terms=ref.get_span().get_span_ids()
	return terms
		

def get_terms_mention(parser, terms):
    	term_text=[]
	c=0
	new_terms=terms
	for t in terms:
		term=parser.get_term(t)
		target_ids=term.get_span().get_span_ids()
		for tid in target_ids:
			c+=1
			word=parser.get_token(tid).get_text()
			if (c==1 or c==len(terms)) and (word=="'" or word=="''" or word=="\""):
				new_terms.remove(t)
				continue
            		term_text.append(word)
        res=(" ").join(term_text)
	return res, new_terms

def get_entity_mention(parser, entity):
	terms=get_entity_terms(entity)
	return get_terms_mention(parser, terms)

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

def prestore_terms_and_tokens(parser):
	global term_for_token
	term_for_token = {}
	global tokens_for_term
	tokens_for_term = {}
	global term_sentences
	term_sentences={}
	for term in parser.get_terms():
		token_arr=[]
		for token_id in term.get_span().get_span_ids():
			term_for_token[token_id] = term.get_id()
			token_arr.append(token_id)
			token=parser.get_token(token_id)
			term_sentences[term.get_id()]=token.get_sent()
		tokens_for_term[term.get_id()]=token_arr

def get_id_not_used(used_ids):
	n = 1
	while True:
		possible_id = 'f'+str(n)
		if possible_id not in used_ids:
			return possible_id
		n += 1

##########################################################################################
#################################### Recognition #########################################
##########################################################################################

def extend_string_with_numbers_and_nnps(entity_string, ts, parser):
	sentence=term_sentences[ts[0]]
	begin=int(ts[0].replace("t",""))
	end=int(ts[len(ts)-1].replace("t", ""))
	new_terms=list(ts)
	num_terms=len(term_sentences)
	# prepend
	ext_string=""

	# Append
	ext_string= ext_string.strip() + " " + entity_string
	temp=end
	while True:
		temp+=1
		if temp>num_terms:
			break
		new_term="t" + str(temp)
		try:
			addition, added_terms = get_terms_mention(parser, [new_term])
			if term_sentences[new_term]==sentence and (parser.get_term(new_term).get_pos() in ["NNP", "NNPS"] or (addition!="" and addition.isdigit())):
				ext_string =  ext_string + " " + addition
				new_terms.append(new_term)
			else:
				break
		except KeyError: #out of bounds
			break
	return ext_string.strip(), new_terms


##########################################################################################
####################################### MODULES ##########################################
##########################################################################################

def get_previous_occurrence(e, all_entities, entity_string): #1
	other_ref=None

	for ent in all_entities:
		if e!=ent and (((int(e["eid"][1:])>int(ent["eid"][1:])) and (e["title"] is ent["title"])) or (e["title"] and not ent["title"])):
		# Entities that are different AND either (entities that passed from the same text type (main or title) OR entities in title)

			ekey=None
			#print ent["eid"]
			if "extended" in ent and ent["extended"]["extref"]:
				ekey=ent["extended"]["mention"].lower()
				if entity_string==ekey or ((entity_string in ekey.split()) and is_person(ent["extended"]["extref"])):
					other_ref=ent["extended"]["extref"]
					if other_ref: # Stop after one match
						break
					#print "D1", entity_string, ekey, other_ref
			if ent["original"]["extref"] or ent["original"]["nwr_extref"]:
				#if entity_string=="smith":
				#	print ent["eid"], entity_string, e["original"]["mention"]
				ekey=ent["original"]["mention"].lower()
				
				if entity_string==ekey: 
					#print "D1", entity_string, ekey, other_ref
					other_ref=ent["original"]["extref"]
					if other_ref:
						break
				elif entity_string in ekey.split():

					if ent["original"]["extref"] is not None: 
						this_extref=ent["original"]["extref"]
					else: # NOTE: THIS SHOULD NEVER BE THE CASE
						this_extref=ent["original"]["nwr_extref"]
					if is_person(this_extref):
						other_ref=this_extref
						if other_ref:
							break
	#if entity_string=="smith":
	#	print other_ref
	return other_ref

def solve_initials_and_abbreviations(entity, entity_string, all_entities): #3
	#2 Initials and abbreviations
	extref=None
	for other_entity in all_entities:
		if other_entity!=entity:
			if "extended" in other_entity and other_entity["extended"]["extref"]:
				initials=other_entity["extended"]["initials"]
				other_ref=other_entity["extended"]["extref"]
				if entity_string==initials:
					extref=other_ref
			elif other_entity["original"]["extref"]:
				initials=other_entity["original"]["initials"]
				other_ref=other_entity["original"]["extref"]
				if entity_string==initials:
					extref=other_ref
			else:
				initials=other_entity["original"]["initials"]
				other_ref=other_entity["original"]["nwr_extref"]
				if entity_string==initials:
					extref=other_ref
	return extref

def do_disambiguation(entity, entity_string, all_entities):
			
	extref=get_previous_occurrence(entity, all_entities, entity_string.lower()); #D1  Get previous occurrence

	if not extref:
		if len(entity_string.split())==1 and entity_string.isupper(): # If one term, all-upper, then it may be an abbreviation
			extref = solve_initials_and_abbreviations(entity, entity_string, all_entities)
		
	return extref

def occurred_in_article(extname, all_entities):
	for ent in all_entities:
		if extname==ent["original"]["mention"]:
			return ent["original"]["nwr_extref"]
		
def get_from_es(pattern):
	max_occurrences=0
	best_candidate=None
	total=0
	if pattern in lemma_to_entity:
		for candidate in lemma_to_entity[pattern]:
			num_occurrences=lemma_to_entity[pattern][candidate]
			if num_occurrences>max_occurrences:
				max_occurrences=lemma_to_entity[pattern][candidate]
				best_candidate=candidate
			total+=num_occurrences
		if max_occurrences>10 and max_occurrences/float(total)>=0.5:			
			return best_candidate
		else:
			return None
	return None
				
def create_dbpedia_uri(t):
	dburl="http://dbpedia.org/resource/" + t.replace(" ", "_")
	return dburl

def get_from_dbpedia(mention):
	dblink=create_dbpedia_uri(e["extended"]["mention"])
	results=my_dbpedia.query_dbpedia_for_unique_dblink(dblink)
	return dblink if (results is not None and len(results)>0) else None

##########################################################################################
####################################### MAIN #############################################
##########################################################################################

global term_for_token
global tokens_for_term
global term_sentences

global lemma_to_entity

fname="lemma.json"
f=open(fname, "r")

for line in f:
        lemma_to_entity=json.loads(line)

if __name__=="__main__":

	if len(sys.argv)>1: # Local instance is specified
		my_dbpedia = Cdbpedia_enquirer(sys.argv[1])		
	else: # default remote dbpedia
		my_dbpedia = Cdbpedia_enquirer()
	path="NWR_EvalSet/"
	#path="eval_corpus/"
	out_path="POCUS_EvalSet/"
	count_all = 0
	count_dis=0
	for file in os.listdir(path):
		print file
		parser=KafNafParser(path + file)
		prestore_terms_and_tokens(parser)

		out_file=out_path + file

		all_entities=[]

		for entity in parser.get_entities():
			if entity.get_id()[0]!="e":
				continue
			entity_string, terms = get_entity_mention(parser, entity)
			# Normalization step
			if len(terms)==1 and entity_string.endswith("-based"):
				norm_entity_string=entity_string[:-6]
			else:
				norm_entity_string=entity_string
			ext_norm_entity_string, ext_terms=extend_string_with_numbers_and_nnps(norm_entity_string, terms, parser)
			
			istitle = (term_sentences[terms[0]]=="1")
			
			if ext_norm_entity_string==norm_entity_string:
				entity_entry = {"eid": entity.get_id(), "original": {"raw": entity_string, "mention": norm_entity_string, "terms": terms, "nwr_extref": get_most_confident_link(entity), "extref": None, "initials": get_initials(norm_entity_string)}, "title": istitle}
			else:
				entity_entry = {"eid": entity.get_id(), "original": {"raw": entity_string, "mention": norm_entity_string, "terms": terms, "nwr_extref": get_most_confident_link(entity), "extref": None, "initials": get_initials(entity_string)}, "extended": {"mention": ext_norm_entity_string, "terms": ext_terms, "initials": get_initials(ext_norm_entity_string)}, "title": istitle, "extref": None}
			
			all_entities.append(entity_entry)

		for consider_title_entities in [False, True]:
			for e in all_entities:
				if e["title"] is consider_title_entities: # 1) Extended mention - This line ensures title entities get processed in a second iteration
					if "extended" in e: # 1) extension
						#e["extended"]["extref"]=occurred_in_article(e["extended"]["mention"], all_entities) or get_from_es(e["extended"]["mention"]) or get_from_dbpedia(e["extended"]["mention"]) # TODO: Try without ES
						e["extended"]["extref"]=occurred_in_article(e["extended"]["mention"], all_entities) or get_from_es(e["extended"]["mention"]) or get_from_dbpedia(e["extended"]["mention"]) # TODO: Try without ES
			
			for e in all_entities:
				if e["title"] is consider_title_entities: # 2) original mention	 - This line ensures title entities get processed in a second iteration	
					e["original"]["extref"]=do_disambiguation(e, e["original"]["mention"], all_entities) #or get_from_es(e["original"]["mention"]) # TODO: Try without ES

			for e in all_entities:
				if e["title"] is consider_title_entities: # 3) original mention, last resort - This line ensures title entities get processed in a second iteration

					if e["original"]["extref"] is None: # TODO: Enable this block later!
						#if consider_title_entities:
						#	e["original"]["extref"]="--NME--"
						#else:
						e["original"]["extref"]=e["original"]["nwr_extref"]

				
		used_ids = set()
		stored=0
		for e in all_entities:
			sextref=""
			mention=""
			single=True
			if "extended" in e and e["extended"]["extref"]:
				sextref=e["extended"]["extref"]
				mention=e["extended"]["mention"]
				er = sextref
				new_entity = Centity()
				new_id = get_id_not_used(used_ids)
				new_entity.set_id(new_id)
				used_ids.add(new_id)
				new_entity.set_comment(mention)
				
				ref = Creferences()
				ref.add_span(e["extended"]["terms"])
				new_entity.add_reference(ref)
				
				ext_ref = CexternalReference()
				ext_ref.set_resource("dbp")
				ext_ref.set_source("POCUS")
				ext_ref.set_reference(er)
				ext_ref.set_confidence("1.0")
				new_entity.add_external_reference(ext_ref)
				
				new_entity.set_source("POCUS")
				print file
				parser.add_entity(new_entity)
			elif sextref=="" and e["original"]["extref"]:
				sextref=e["original"]["extref"]
				mention=e["original"]["mention"]
							
				ext_ref = CexternalReference()
				ext_ref.set_resource("dbp")
				ext_ref.set_source("POCUS")
				ext_ref.set_reference(sextref)
				ext_ref.set_confidence("1.0")
				
				parser.add_external_reference_to_entity(e["eid"], ext_ref)

			

			
		parser.dump(out_file)
