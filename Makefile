.PHONY: data.csv

data.csv: kebulat.osm-json process.py
	python3 process.py

kebulat.osm-json: query.overpassql
	curl -vo $@ --data @query.overpassql 'http://overpass-api.de/api/interpreter'