"""Reproject the CEPF Western Ghats boundary (Data Basin, CC BY 3.0) to WGS84 and upload as an EE asset.
Usage: upload_cepf.py <shapefile prefix without extension>"""
import sys, json, shapefile, ee
from pyproj import Transformer
ee.Initialize(project='pyro-india-515605')
tr = Transformer.from_crs('EPSG:32643', 'EPSG:4326', always_xy=True)
r = shapefile.Reader(sys.argv[1])
feats, total = [], 0.0
for sr in r.shapeRecords():
    pts = sr.shape.points; parts = list(sr.shape.parts) + [len(pts)]
    rings = [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
    area = 0.0
    for ring in rings:  # planar UTM area (shoelace), km2
        a = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])) / 2
        area += a
    total += abs(area) / 1e6
    coords = [[list(tr.transform(x, y)) for x, y in ring] for ring in rings]
    feats.append(ee.Feature(ee.Geometry.Polygon(coords, proj='EPSG:4326', geodesic=False), {'rec_num': int(sr.record[0])}))
print('UTM planar area km2:', round(total))
fc = ee.FeatureCollection(feats)
t = ee.batch.Export.table.toAsset(fc, 'cepf_boundary', 'projects/pyro-india-515605/assets/cepf_boundary')
t.start(); print('started', t.id)
