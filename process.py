from operator import itemgetter
from shapely.geometry import Point, Polygon
import csv
import pyproj
import sys
import tqdm
import ujson


p1 = pyproj.Proj(init='EPSG:4326')  # WGS:84
p2 = pyproj.Proj(init='EPSG:3067')  # ETRS-TM35FIN

def to_etrs(*, lat, lon):
	return pyproj.transform(p1, p2, lat, lon)



with open('kebulat.osm-json', 'rb') as infp:
    elements = ujson.load(infp)['elements']

nodes = {n['id']: n for n in elements if n['type'] == 'node'}
ways = {n['id']: n for n in elements if n['type'] == 'way'}

bounds = {}
restaurants = {}

for el in tqdm.tqdm(elements, desc='parsing elements'):
	tags = el.get('tags', {})
	if el['type'] == 'node' and tags.get('cuisine'):
		x, y = to_etrs(lat=el['lat'], lon=el['lon'])
		restaurants[el['id']] = {
			'_orig': el,
			'name': tags.get('name'),
			'pt': Point([x, y]),
		}
		continue
	if el['type'] == 'relation' and tags.get('admin_level') == '8':
		points = []
		population = None
		admin_centre = None
		for memb in el['members']:
			if memb['type'] == 'way' and memb['role'] == 'outer':
				way = ways[memb['ref']]
				points.extend((
					to_etrs(lat=n['lat'], lon=n['lon'])
					for n
					in [nodes[id] for id in way['nodes']]
				))
			if memb['role'] == 'admin_centre' or memb['role'] == 'label':
				admin_centre = nodes[memb['ref']]
				population = (admin_centre.get('tags', {}).get('population') or population)

		bounds[el['id']] = {
			'_orig': el,
			'name': tags.get('name'),
			'poly': Polygon(points),
			'pop': population,
		}

for bound in tqdm.tqdm(bounds.values(), desc='determining containment'):
	poly = bound['poly']
	matches = []
	for restaurant in restaurants.values():
		if poly.contains(restaurant['pt']):
			matches.append(restaurant)
			#print(bound['name'], restaurant['name'])
	bound['restaurants'] = matches


cw = csv.writer(sys.stdout)

for bound in sorted(bounds.values(), key=itemgetter('name')):
	cw.writerow((
		bound['name'],
		bound['pop'],
		len(bound['restaurants']),
	))