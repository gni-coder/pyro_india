"""WGEEP-rule reconstruction of the Western Ghats boundary (1 km).
Steps: forest-like cells (Hansen tree cover >=10% in >=10% of cell) AND elevation rule
(>=150 m west of the main drainage divide, >=500 m east) -> 6 km closing -> keep pieces
connected to seed points in the main chain -> fill small holes. Prints area after each step.
Usage: wgeep_reconstruct.py [render]"""
import sys, urllib.request, ee
ee.Initialize(project='pyro-india-515605')
ASSET = 'projects/pyro-india-515605/assets/wgeep_layers_1km_core'
ROI = ee.Geometry.Rectangle([72.5, 7.8, 78.3, 21.3], geodesic=False)
CLOSE_KM, HOLE_KM2, TARGET = 6, 256, 129037
SEEDS = {'Agasthyamalai': (77.2, 8.7), 'Anamalai/Palani': (77.2, 10.3), 'Nilgiris': (76.6, 11.4),
         'Coorg': (75.7, 12.4), 'Kudremukh': (75.2, 13.2), 'Goa': (74.2, 15.4), 'Koyna': (73.8, 17.4),
         'Nashik/Igatpuri': (73.7, 19.7)}
L = ee.Image(ASSET)
elev, west = L.select('elev'), L.select('west').eq(1)
rule = west.And(elev.gte(150)).Or(west.Not().And(elev.gte(500)))
area = ee.Image.pixelArea().divide(1e6)
def km2(m):
    return round(list(m.unmask(0).multiply(area).reduceRegion(ee.Reducer.sum(), ROI, 1000, maxPixels=1e10, tileScale=4).getInfo().values())[0])

raw = L.select('hansen10').gte(0.1).And(rule)
closed0 = raw.focalMax(CLOSE_KM, 'circle', 'pixels').focalMin(CLOSE_KM, 'circle', 'pixels')
# Palghat gap: report leaves it out. Inside this box keep only high ground (>=500 m) so the low pass is cut.
GAP_BOX = ee.Geometry.Rectangle([76.35, 10.55, 77.05, 11.0], geodesic=False)
in_gap = ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(GAP_BOX)]), 1).unmask(0).eq(1)
closed1 = closed0.And(in_gap.Not().Or(elev.gte(500)))
# Biligirirangan range: report includes it up to the Nilgiri Biosphere Reserve / Chamarajanagar east edge
# (Kollegal-Satyamangalam highway). Approximated by this box (no official polygon available): forest cells >=150 m.
BR_BOX = ee.Geometry.Rectangle([76.9, 11.45, 77.75, 12.3], geodesic=False)
in_br = ee.Image().byte().paint(ee.FeatureCollection([ee.Feature(BR_BOX)]), 1).unmask(0).eq(1)
br_add = in_br.And(L.select('hansen10').gte(0.1)).And(elev.gte(150))
closed = closed1.Or(br_add)
seed_fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point(p), {'n': n}) for n, p in SEEDS.items()])
seed_in = closed.reduceRegions(seed_fc, ee.Reducer.first(), 1000).getInfo()['features']
print('seeds inside mask:', {f['properties']['n']: f['properties'].get('first') for f in seed_in}, flush=True)
seed_img = ee.Image().byte().paint(seed_fc.filter(ee.Filter.eq('n', 'Nilgiris')).merge(seed_fc), 1).updateMask(closed)
cost = closed.selfMask().rename('c')
reach = cost.cumulativeCost(source=seed_img.selfMask(), maxDistance=3e6).lt(3e6).selfMask()
conn = reach.unmask(0).And(closed)
# fill small holes: background components under HOLE_KM2 pixels that are enclosed by the mask
bg = conn.Not().selfMask()
bgcc = bg.connectedComponents(ee.Kernel.plus(1), 256)
size = bgcc.select('labels').connectedPixelCount(256)
small_hole = bg.And(size.lt(HOLE_KM2)).unmask(0)
final = conn.Or(small_hole).selfMask()
if __name__ == '__main__':
    print('target', TARGET)
    for n, m in (('raw (forest AND elevation rule)', raw), (f'closed {CLOSE_KM} km', closed0), ('Palghat gap cut', closed1), ('+ Biligirirangan box', closed), ('connected to main chain', conn), ('holes filled', final)):
        print(n, km2(m), flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == 'render':
        dem = ee.Image('USGS/SRTMGL1_003')
        hs = ee.Terrain.hillshade(dem.reproject('EPSG:4326', None, 500)).visualize(min=100, max=255, palette=['333333', 'ffffff'])
        fill = final.visualize(palette=['d62728'], opacity=0.45)
        edge = final.focalMax(1).subtract(final.unmask(0).focalMin(1)).selfMask().visualize(palette=['000000'])
        img = ee.ImageCollection([hs, fill, edge]).mosaic()
        for i, (a, b) in enumerate([(7.8, 12.0), (12.0, 16.5), (16.5, 21.3)]):
            reg = ee.Geometry.Rectangle([72.5, a, 78.3, b], geodesic=False)
            url = img.getThumbURL({'region': reg, 'dimensions': 1100, 'format': 'png'})
            open(f'analysis/figs/wgeep_v2_{i+1}.png', 'wb').write(urllib.request.urlopen(url).read())
            print('saved', i + 1, flush=True)
