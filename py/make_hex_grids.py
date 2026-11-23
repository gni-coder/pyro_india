"""Equal-area hexagon grids (10, 25, 100 km2) clipped to the study boundary (CEPF, shapefile in UTM 43N).
Projection: Albers equal-area (WGS84, lat_1=10, lat_2=18, lat_0=14, lon_0=76). Keep hexes with >=50% inside boundary.
Writes data/hex/hex_<A>km2.geojson (WGS84) and prints counts. Usage: make_hex_grids.py <shapefile prefix> <outdir>"""
import sys, json, math, os, shapefile
import numpy as np
from shapely.geometry import Polygon, mapping
from shapely.ops import transform, unary_union
from shapely import prepared
from pyproj import Transformer
AEA = '+proj=aea +lat_1=10 +lat_2=18 +lat_0=14 +lon_0=76 +datum=WGS84 +units=m'
to_aea = Transformer.from_crs('EPSG:32643', AEA, always_xy=True).transform
aea_to_ll = Transformer.from_crs(AEA, 'EPSG:4326', always_xy=True).transform
r = shapefile.Reader(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
polys = []
for s in r.shapes():
    parts = list(s.parts) + [len(s.points)]
    ring = [s.points[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
    polys.append(Polygon(ring[0], ring[1:]).buffer(0))
bnd = transform(to_aea, unary_union(polys))
print('boundary area km2 (Albers):', round(bnd.area / 1e6))
pb = prepared.prep(bnd); minx, miny, maxx, maxy = bnd.bounds
for A in (10, 25, 100):
    s = math.sqrt(2 * A * 1e6 / (3 * math.sqrt(3)))          # side length (m); flat-top hexagons
    w, h = 3 * s, math.sqrt(3) * s                            # column spacing 1.5 s; row spacing h
    feats = []; i = 0
    for ci, cx in enumerate(np.arange(minx - s, maxx + s, 1.5 * s)):
        off = (h / 2) if ci % 2 else 0
        for cy in np.arange(miny - h + off, maxy + h, h):
            hexa = Polygon([(cx + s * math.cos(math.radians(60 * k)), cy + s * math.sin(math.radians(60 * k))) for k in range(6)])
            if not pb.intersects(hexa): continue
            frac = hexa.intersection(bnd).area / hexa.area
            if frac < 0.5: continue
            i += 1
            feats.append({'type': 'Feature', 'properties': {'hex_id': f'h{A}_{i}', 'hex_km2': A, 'frac_in': round(frac, 3)},
                          'geometry': mapping(transform(aea_to_ll, hexa))})
    json.dump({'type': 'FeatureCollection', 'features': feats}, open(f'{out}/hex_{A}km2.geojson', 'w'))
    print(A, 'km2 hexes:', len(feats), '| hex area check km2:', round(Polygon([(s*math.cos(math.radians(60*k)), s*math.sin(math.radians(60*k))) for k in range(6)]).area / 1e6, 3), flush=True)
