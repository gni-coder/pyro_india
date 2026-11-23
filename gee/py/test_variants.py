"""Fast WGEEP variant areas from the exported 1 km layer asset. Usage: test_variants.py <asset> <band1,band2,...>"""
import sys, ee
ee.Initialize(project='pyro-india-515605')
ROI = ee.Geometry.Rectangle([72.5, 7.8, 78.3, 21.3], geodesic=False)
L = ee.Image(sys.argv[1]); bands = sys.argv[2].split(',')
area = ee.Image.pixelArea().divide(1e6)
elev, west = L.select('elev'), L.select('west').eq(1)
rule = west.And(elev.gte(150)).Or(west.Not().And(elev.gte(500)))
def km2(m):
    return round(list(m.unmask(0).multiply(area).reduceRegion(ee.Reducer.sum(), ROI, 1000, maxPixels=1e10, tileScale=4).getInfo().values())[0])
print('target 129037')
print('elevation rule only', km2(rule), flush=True)
for b in bands:
    for thr in (0.1, 0.3, 0.5):
        m = L.select(b).gte(thr).And(rule)
        row = [km2(m)]
        for r in (3, 6, 10):
            row.append(km2(m.focalMax(r, 'circle', 'pixels').focalMin(r, 'circle', 'pixels')))
        print(f'{b}>={thr}: none/3/6/10 km close =', row, flush=True)
