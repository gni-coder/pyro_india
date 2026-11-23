"""Phase 2 pilot exploration: Bandipur Feb 2019. MODIS burned area (MCD64A1) dates/area and active-fire days in a box around Bandipur."""
import ee
ee.Initialize(project='pyro-india-515605')
BOX = ee.Geometry.Rectangle([76.30, 11.55, 76.95, 12.05], geodesic=False)   # Bandipur TR + surroundings
ba = ee.ImageCollection('MODIS/061/MCD64A1').filterDate('2019-01-01', '2019-06-01').select('BurnDate').max().clip(BOX)
area = ee.Image.pixelArea().divide(1e6)
burned = ba.gt(0)
print('MCD64A1 burned area km2 (Jan-May 2019):', round(area.updateMask(burned).reduceRegion(ee.Reducer.sum(), BOX, 500, maxPixels=1e9).getInfo()['area'], 1))
h = ba.updateMask(burned).reduceRegion(ee.Reducer.frequencyHistogram(), BOX, 500, maxPixels=1e9).getInfo()['BurnDate']
print('burn day-of-year histogram:', dict(sorted((int(float(k)), int(v)) for k, v in h.items())))
fires = ee.ImageCollection('FIRMS').filterDate('2019-01-01', '2019-06-01').filterBounds(BOX)
n = fires.map(lambda i: i.select('T21').gt(0).rename('hot').set('d', i.date().format('YYYY-MM-dd'))).filter(ee.Filter.notNull(['d']))
def day_count(i):
    c = i.select('hot').reduceRegion(ee.Reducer.sum(), BOX, 1000, maxPixels=1e9).get('hot')
    return ee.Feature(None, {'d': i.get('d'), 'n': c})
rows = [f['properties'] for f in n.map(day_count).filter(ee.Filter.gt('n', 0)).getInfo()['features']]
print('MODIS active-fire pixels per day (Feb-Mar 2019 in box):', {r['d']: int(r['n']) for r in rows if '2019-02' <= r['d'] <= '2019-03-31'})
