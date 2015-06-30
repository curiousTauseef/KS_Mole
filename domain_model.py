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

##########################################################################################
#################################### Recognition #########################################
##########################################################################################

def extend_string_with_numbers_and_nnps(entity_string, terms, parser):
	sentence=term_sentences[terms[0]]
	begin=int(terms[0].replace("t",""))
	end=int(terms[len(terms)-1].replace("t", ""))
	new_terms=terms
	num_terms=len(term_sentences)
	# prepend
	ext_string=""
	"""
	temp=begin
	while True:
		temp-=1
		if temp<1:
			break
		new_term="t" + str(temp)
		try:
			addition, added_terms = get_terms_mention(parser, [new_term])
			if term_sentences[new_term]==sentence and (parser.get_term(new_term).get_pos() in ["NNP", "NNPS"] or (addition!="" and addition.isdigit())):
				ext_string = addition + " " + ext_string
				new_terms.append(new_term)
			else:
				break
		except KeyError: #out of bounds
			break
	"""
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
	extref=None
	for ent in all_entities:
		if e!=ent:
			if "extended" in ent and ent["extended"]["extref"]:
				ekey=ent["extended"]["mention"].lower()
				other_ref=ent["extended"]["extref"]
			elif ent["original"]["extref"]:
				ekey=ent["original"]["mention"].lower()
				other_ref=ent["original"]["extref"]
			#print entity_string, ekey
			if entity_string==ekey or (entity_string in ekey.split() and is_person(all_entities[ekey]["extref"])): 
				extref=other_ref
				print "D1", entity_string, ekey, extref
	return extref

def solve_initials_and_abbreviations(entity, entity_string, all_entities): #3
	#2 Initials and abbreviations
	extref=None
	for other_entity in all_entities:
		if other_entity!=entity:
			if "extended" in other_entity and other_entity["extended"]["extref"]:
				initials=ent["extended"]["initials"]
				other_ref=ent["extended"]["extref"]
			elif ent["original"]["extref"]:
				initials=ent["original"]["initials"]
				other_ref=ent["original"]["extref"]
			else:
				initials=ent["original"]["initials"]
				other_ref=ent["original"]["nwr_extref"]
		if entity_string==initials:
			extref=other_ref
			print "D2", entity_string, ekey, extref
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

def do_disambiguation(entity, entity_string, all_entities):
			
	extref=get_previous_occurrence(entity, all_entities, entity_string.lower()); #D1  Get previous occurrence

	if not extref:
		if len(entity_string.split())==1 and entity_string.isupper():
			extref = solve_initials_and_abbreviations(entity_string, all_entities)
		# or solve_initials_and_abbreviations_after(entity_string, terms[0].replace("t", ""), parser)
		#D2 Initials and abbreviations of occurred entities
		#D3 Initials and abbreviations explained afterwards
		
	return extref

def occurred_in_article(extname, all_entities):
	for ent in all_entities:
		if extname==ent["original"]["norm_name"]:
			return ent["original"]["nwr_extref"]
		
def get_from_es(t):
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

if __name__=="__main__":
	my_dbpedia = Cdbpedia_enquirer()
	path="dev_corpus/"
	#path="eval_corpus/"
	out_path="proc_dev_corpus/"
	count_all = 0
	count_dis=0
	for file in os.listdir(path):
		print file
		parser=KafNafParser(path + file)

		prestore_terms_and_tokens(parser)

		all_entities=[]

		for entity in parser.get_entities():
			entity_string, terms = get_entity_mention(parser, entity)
			if len(terms)==1 and entity_string.endswith("-based"):
				norm_entity_string=entity_string[:-6]
			else:
				norm_entity_string=entity_string
			ext_norm_entity_string, ext_terms=extend_string_with_numbers_and_nnps(norm_entity_string, terms, parser)
			
			istitle = (term_sentences[terms[0]]=="1")
			
			if ext_norm_entity_string==norm_entity_string:
				entity_entry = {"original": {"raw": entity_string, "mention": norm_entity_string, "terms": terms, "nwr_extref": get_most_confident_link(entity), "extref": None, "initials": get_initials(norm_entity_string)}, "title": istitle}
			else:
				entity_entry = {"original": {"raw": entity_string, "mention": norm_entity_string, "terms": terms, "nwr_extref": get_most_confident_link(entity), "extref": None, "initials": get_initials(entity_string)}, "extended": {"mention": ext_norm_entity_string, "terms": ext_terms }, "title": istitle, "extref": None, "initials": get_initials(ext_norm_entity_string)}
			all_entities.append(entity_entry)
			
			#print entity_string
		#print all_entities

		for consider_title_entities in [False, True]:
		
			for e in all_entities:
				if e["title"] is consider_title_entities:
					if "extended" in e: # 1) No title, extension; #3 Title, extension
						e["extended"]["extref"]=occurred_in_article(e["extended"]["mention"], all_entities) or get_from_es(e["extended"]["mention"]) or get_from_dbpedia(e["extended"]["mention"])
						print e["extended"]["extref"]
	
			for e in all_entities:
				if e["title"] is consider_title_entities: # 2) No title, not disambigated yet
					if len(e["original"]["mention"].split())==1 and len(e["extended"]["mention"].split("-"))>1:
						multi_extref=[]
						for m in e["original"]["mention"].split("-"):
							extref=do_disambiguation(e, m, all_entities) or get_from_es(m)
							if extref:
								multi_extref.append({"mention": m, "extref": extref})
						e["original"]["multi_extref"]=multi_extref
					elif len(e["original"]["mention"].split())==1 and len(e["extended"]["mention"].split("/"))>1:
						multi_extref=[]
						for m in e["original"]["mention"].split("/"):
							extref=do_disambiguation(e, m, all_entities) or get_from_es(m)
							if extref:
								multi_extref.append({"mention": m, "extref": extref})
						e["original"]["multi_extref"]=multi_extref
					else:
						e["original"]["extref"]=do_disambiguation(e, all_entities) or get_from_es(e["original"]["mention"])
						if e["original"]["extref"] is None:
							e["original"]["extref"]="--NME--" if consider_title_entities else e["original"]["nwr_extref"]
						

		"""

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
			all_entities[entity_string.lower()]={"extref": extref, "terms": terms, "initials": get_initials(entity_string)}

		# Now do the title
		for entity in title_entities:
			for ref in entity.get_references():
				terms=ref.get_span().get_span_ids()
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
				extref='-NAE-'
				entity=add_entity_extref(entity, extref)
		parser.dump(out_path + file)
	print count_all, count_dis
	"""