"""Render candidate WGEEP reconstruction (hansen10>=10% cells, elevation/drainage rule, 6 km closing) over terrain."""
import sys, io, urllib.request, ee
ee.Initialize(project='pyro-india-515605')
ASSET = 'projects/pyro-india-515605/assets/wgeep_layers_1km_core'
L = ee.Image(ASSET)
elev, west = L.select('elev'), L.select('west').eq(1)
rule = west.And(elev.gte(150)).Or(west.Not().And(elev.gte(500)))
m = L.select('hansen10').gte(0.1).And(rule)
cand = m.focalMax(6, 'circle', 'pixels').focalMin(6, 'circle', 'pixels').selfMask()
dem = ee.Image('USGS/SRTMGL1_003')
hs = ee.Terrain.hillshade(dem.reproject('EPSG:4326', None, 500)).visualize(min=100, max=255, palette=['333333', 'ffffff'])
fill = cand.visualize(palette=['d62728'], opacity=0.45)
edge = cand.focalMax(1).subtract(cand.unmask(0).focalMin(1)).selfMask().visualize(palette=['000000'])
coast = ee.Image(0)  # placeholder keeps compositing simple
img = ee.ImageCollection([hs, fill, edge]).mosaic()
bands = [(7.8, 12.0), (12.0, 16.5), (16.5, 21.3)]
for i, (a, b) in enumerate(bands):
    reg = ee.Geometry.Rectangle([72.5, a, 78.3, b], geodesic=False)
    url = img.getThumbURL({'region': reg, 'dimensions': 1100, 'format': 'png'})
    open(f'analysis/figs/wgeep_candidate_{i+1}.png', 'wb').write(urllib.request.urlopen(url).read())
    print('saved', i + 1, flush=True)
