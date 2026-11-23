"""Area (km2) per burnable class per state inside the study boundary, from the exported 30 m class map.
Runs as a batch export to an EE table asset (interactive reduction times out). Usage: phase1_state_areas.py start | read"""
import sys, ee
ee.Initialize(project='pyro-india-515605')
MASK = ee.Image('projects/pyro-india-515605/assets/burnable_roy_30m')
OUT = 'projects/pyro-india-515605/assets/burnable_roy_state_areas'
BND = ee.FeatureCollection('projects/pyro-india-515605/assets/cepf_boundary').geometry()
states = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM0_NAME', 'India')).filterBounds(BND)
def per_state(f):
    g = f.geometry().intersection(BND, 100)
    img = ee.Image.pixelArea().divide(1e6).addBands(MASK.unmask(0).rename('cls'))
    r = img.reduceRegion(ee.Reducer.sum().group(1, 'cls'), g, 30, maxPixels=1e12, tileScale=16)
    return ee.Feature(None, {'state': f.get('ADM1_NAME'), 'groups': r.get('groups')})
if sys.argv[1] == 'start':
    t = ee.batch.Export.table.toAsset(states.map(per_state), 'burnable_roy_state_areas', OUT); t.start(); print('started', t.id)
else:
    names = {0: 'not burnable', 1: 'forest', 2: 'shola grassland', 3: 'hill grassland/savanna', 4: 'lateritic grassland', 5: 'scrub',
             6: 'forest plantation', 7: 'tree crop/orchard', 8: 'degraded forest'}
    rows = ee.FeatureCollection(OUT).getInfo()['features']
    print('state'.ljust(18), *[names[k][:12].rjust(13) for k in range(1, 9)], 'burnable'.rjust(10))
    tot = {k: 0 for k in range(1, 9)}
    for f in rows:
        g = {int(x['cls']): x['sum'] for x in f['properties']['groups']}
        print(f['properties']['state'].ljust(18), *[f'{g.get(k, 0):13.0f}' for k in range(1, 9)], f'{sum(g.get(k, 0) for k in range(1, 9)):10.0f}')
        for k in tot: tot[k] += g.get(k, 0)
    print('TOTAL'.ljust(18), *[f'{tot[k]:13.0f}' for k in range(1, 9)], f'{sum(tot.values()):10.0f}')
