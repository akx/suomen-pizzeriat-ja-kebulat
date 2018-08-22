.PHONY: data.csv

data.csv: kebulat.osm-json process.py
	python3 process.py

kebulat.osm-json: query.txt
	curl -vo $@ --data @query.txt 'http://overpass-api.de/api/interpreter'