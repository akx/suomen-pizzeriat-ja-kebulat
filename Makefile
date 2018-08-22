.PHONY: data.csv

data.csv: kebulat.osm-json
	python3 process.py > data.csv

kebulat.osm-json:
	curl -vo $@ --data @query.txt 'http://overpass-api.de/api/interpreter'