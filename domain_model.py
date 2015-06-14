from KafNafParserPy import *
import os


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
		if e.get_resource()=="spotlight_v1" and float(ref.get_confidence())>maxconf:
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

if __name__=="__main__":
	print "Welcome"
	path="corpus/"
	for file in os.listdir(path):
		print file
		parser=KafNafParser(path + file)

		term_start = get_start_term(parser)

		all_entities={}
		for entity in parser.get_entities():
			if entity.get_id()[0]=="g":
				continue
			for ref in entity.get_references():
				terms=ref.get_span().get_span_ids()
			if int(terms[0].replace("t", ""))<term_start:
				continue
			
			entity_string = get_entity_mention(parser, terms)
			print entity_string
			extref=None
			for ekey in all_entities:
				if entity_string in ekey.split() and is_person(all_entities[ekey]["extref"]):
					extref=entity.get_id() + ": " + entity_string + " is " + ekey
			if not extref:
				extref=get_most_confident_link(entity)
			all_entities[entity_string]={"extref": extref, "terms": terms}

		break
