from KafNafParserPy import *
import sys, getopt, os

if len(sys.argv)<2:
	print "No filename supplied"
	sys.exit()
else:
	folder = sys.argv[1]
	print "Folder is " + folder

path='/scratch/fii800/mole_cars/' + folder
print path
w=open("results.csv", "a")
for root, dirs, files in os.walk(path):

    for inputfile in files:
        filename=root + "/" + inputfile
        try:
                my_parser = KafNafParser(filename)
        except:
                print 'problem with the file ' + filename + "\n"
                continue

        # Iterate over the predicates and check for ESO predicates in the external references
        for entity in my_parser.get_entities():
		max_ref=""
		max_conf=-0.1
        	for ext_ref in entity.get_external_references():
			if ext_ref.get_resource()=="spotlight_v1" and float(ext_ref.get_confidence())>max_conf:
				max_conf=float(ext_ref.get_confidence())
				max_ref=ext_ref.get_reference()
		if max_ref!="":
		        for ref in entity.get_references():
				target_ids = ref.get_span().get_span_ids()
				lemma=""
				for tid in target_ids:
					lemma+=my_parser.get_term(tid).get_lemma() + " "
				w.write("%s===%s\n" % (max_ref.encode('utf-8'), lemma.encode('utf-8')))

w.close()
