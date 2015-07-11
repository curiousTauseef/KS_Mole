import json

fname="lemma.json"

f=open(fname, "r")

for line in f:
	j=json.loads(line)
	print j["Arizona"]
