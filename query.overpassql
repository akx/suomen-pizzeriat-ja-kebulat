[out:json];
area["ISO3166-1"="FI"][admin_level=2] -> .fi;
rel[admin_level=8](area.fi); (._;>;); out body qt;

(
  node[amenity~"restaurant|fast_food"](area.fi);
  node[cuisine~"kebab|kebap|pizza|doner|gyros|shawarma"](area.fi);
  node[name~"kebab|kebap|pizz|doner|gyros|shawarma",i](area.fi);
);
out body qt;

(
  rel[amenity~"restaurant|fast_food"](area.fi);
  rel[cuisine~"kebab|kebap|pizza|doner|gyros|shawarma"](area.fi);  
  rel[name~"kebab|kebap|pizz|doner|gyros|shawarma",i](area.fi);
  way[amenity~"restaurant|fast_food"](area.fi);
  way[cuisine~"kebab|kebap|pizza|doner|gyros|shawarma"](area.fi);
  way[name~"kebab|kebap|pizz|doner|gyros|shawarma",i](area.fi);
);
(._;>;);
out body qt;
