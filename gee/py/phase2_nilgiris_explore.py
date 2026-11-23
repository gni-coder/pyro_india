"""Find candidate shola-grassland fires on the Nilgiris plateau: MODIS MCD64A1 burned area per year on Roy shola/hill-grass ground."""
import ee
ee.Initialize(project='pyro-india-515605')
BOX = ee.Geometry.Rectangle([76.35, 11.15, 76.90, 11.60], geodesic=False)
roy = ee.Image('projects/pyro-india-515605/assets/burnable_roy_30m').select('burnable').unmask(0)
grass = roy.eq(2).Or(roy.eq(3)).reduceResolution(ee.Reducer.mean(), maxPixels=1024).reproject('EPSG:4326', None, 500)
shola = roy.eq(2).reduceResolution(ee.Reducer.mean(), maxPixels=1024).reproject('EPSG:4326', None, 500)
K = ee.Image.pixelArea().divide(1e6)
print('shola-class area in box km2:', round(K.multiply(roy.eq(2)).reduceRegion(ee.Reducer.sum(), BOX, 60, maxPixels=1e10, tileScale=4).getInfo()['area'], 1))
def per_year(y):
    y = ee.Number(y)
    ba = ee.ImageCollection('MODIS/061/MCD64A1').filterDate(ee.Date.fromYMD(y, 1, 1), ee.Date.fromYMD(y, 12, 31)).select('BurnDate').max().unmask(0).reproject('EPSG:4326', None, 500)
    b = ba.gt(0)
    a_all = K.updateMask(b).reduceRegion(ee.Reducer.sum(), BOX, 500, maxPixels=1e9).get('area')
    a_gr = K.multiply(grass.gte(0.3)).updateMask(b).reduceRegion(ee.Reducer.sum(), BOX, 500, maxPixels=1e9).get('area')
    a_sh = K.multiply(shola.gte(0.2)).updateMask(b).reduceRegion(ee.Reducer.sum(), BOX, 500, maxPixels=1e9).get('area')
    doy = ba.updateMask(b).reduceRegion(ee.Reducer.median(), BOX, 500, maxPixels=1e9).get('BurnDate')
    return ee.Feature(None, {'y': y, 'all': a_all, 'grass': a_gr, 'shola': a_sh, 'doy': doy})
rows = ee.FeatureCollection(ee.List.sequence(2001, 2024).map(per_year)).getInfo()['features']
print('year  burned_all  on_grass(>=30%)  on_shola(>=20%)  median_burn_DOY  (km2)')
for f in rows:
    p = f['properties']; print(int(p['y']), *[f'{(p[k] or 0):8.1f}' for k in ('all', 'grass', 'shola')], int(p['doy'] or 0))
