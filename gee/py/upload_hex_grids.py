"""Upload hexagon grids (data/hex/*.geojson from py/make_hex_grids.py) as EE table assets."""
import json, ee
ee.Initialize(project='pyro-india-515605')
for A in (10, 25, 100):
    gj = json.load(open(f'data/hex/hex_{A}km2.geojson'))
    fc = ee.FeatureCollection(gj)
    t = ee.batch.Export.table.toAsset(fc, f'hex_{A}km2', f'projects/pyro-india-515605/assets/hex_{A}km2')
    t.start(); print('started', A, t.id, flush=True)
