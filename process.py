from operator import itemgetter
from shapely.geometry import Point, Polygon
import argparse
import csv
import pyproj
import sys
import tqdm
import ujson

wgs_to_etrs_xform = pyproj.Transformer.from_crs(
    "EPSG:4326", "EPSG:3067",  # WGS:84  # ETRS-TM35FIN
)


def to_etrs(*, lat, lon):
    return wgs_to_etrs_xform.transform(lat, lon)


def get_name(tags):
    if "name" in tags:
        return tags["name"]
    for tag, value in tags.items():
        if tag.startswith("name:"):
            return value


def node_list_to_poly(nodes, node_id_list):
    return [
        to_etrs(lat=n["lat"], lon=n["lon"]) for n in [nodes[id] for id in node_id_list]
    ]


ACCEPTED_WORDS = {"pizza", "pizze", "kebap", "kebab"}


def is_restaurant(tags):
    for s in (
        (tags.get("cuisine") or "").lower(),
        (get_name(tags) or "").lower(),
    ):
        for word in ACCEPTED_WORDS:
            if word in s:
                return True
    return False


def get_poly_center(coords):  # hardly accurate
    x_sum = y_sum = 0
    for x, y in coords:
        x_sum += x
        y_sum += y
    return (x_sum / len(coords), y_sum / len(coords))


def read_bounds_and_restaurants():

    with open("kebulat.osm-json", "rb") as infp:
        elements = ujson.load(infp)["elements"]

    nodes = {n["id"]: n for n in elements if n["type"] == "node"}
    ways = {n["id"]: n for n in elements if n["type"] == "way"}

    bounds = {}
    restaurants = {}

    for el in tqdm.tqdm(elements, desc="parsing elements"):
        tags = el.get("tags", {})
        if is_restaurant(tags):
            if el["type"] == "node":
                x, y = to_etrs(lat=el["lat"], lon=el["lon"])
                latlon = (el["lat"], el["lon"])
            else:
                coords = node_list_to_poly(nodes, el["nodes"])
                x, y = get_poly_center(coords)
                latlon = None

            restaurants[el["id"]] = {
                "_orig": el,
                "id": el["id"],
                "latlon": latlon,
                "name": get_name(tags),
                "pt": Point([x, y]),
            }
            continue
        if el["type"] == "relation" and tags.get("admin_level") == "8":
            points = []
            population = None
            admin_centre = None
            for memb in el["members"]:
                if memb["type"] == "way" and memb["role"] == "outer":
                    way = ways[memb["ref"]]
                    points.extend(node_list_to_poly(nodes, way["nodes"]))
                if memb["role"] == "admin_centre" or memb["role"] == "label":
                    admin_centre = nodes[memb["ref"]]
                    population = (
                        admin_centre.get("tags", {}).get("population") or population
                    )

            bounds[el["id"]] = {
                "_orig": el,
                "name": get_name(tags),
                "poly": Polygon(points),
                "pop": population,
            }

    for bound in tqdm.tqdm(bounds.values(), desc="determining containment"):
        poly = bound["poly"]
        matches = []
        for restaurant in restaurants.values():
            if poly.contains(restaurant["pt"]):
                matches.append(restaurant)
                # print(bound['name'], restaurant['name'])
        bound["restaurants"] = matches

    return (bounds, restaurants)


def main():
    ap = argparse.ArgumentParser()
    args = ap.parse_args()
    bounds, restaurants = read_bounds_and_restaurants()

    with open("data.csv", "w") as outf:
        cw = csv.writer(outf)
        for bound in sorted(bounds.values(), key=itemgetter("name")):
            cw.writerow((bound["name"], bound["pop"], len(bound["restaurants"]),))

    with open("answer.csv", "w") as outf:
        cw = csv.writer(outf)
        for bound in sorted(
            bounds.values(), key=lambda b: int(b.get("pop") or 0), reverse=True
        ):
            if (
                bound["pop"]
                and int(bound["pop"]) > 1000
                and len(bound["restaurants"]) == 0
            ):
                cw.writerow((bound["name"], bound["pop"], len(bound["restaurants"]),))

    with open("full.csv", "w") as outf:
        cw = csv.writer(outf)
        for bound in sorted(bounds.values(), key=itemgetter("name")):
            for restaurant in bound["restaurants"]:
                latlon = restaurant["latlon"]
                cw.writerow(
                    (
                        bound["name"],
                        restaurant["name"] or restaurant["id"],
                        (latlon[0] if latlon else None),
                        (latlon[1] if latlon else None),
                    )
                )


if __name__ == "__main__":
    main()
