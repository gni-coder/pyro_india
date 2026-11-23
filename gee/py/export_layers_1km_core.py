"""Export 1 km layers used for WGEEP reconstruction as a single EE asset (core: Hansen + elevation + drainage side; WorldCover is in export_layers_1km.py)."""
import ee
ee.Initialize(project='pyro-india-515605')
ROI = ee.Geometry.Rectangle([72.5, 7.8, 78.3, 21.3], geodesic=False)
SCALE = 1000
ASSET = 'projects/pyro-india-515605/assets/wgeep_layers_1km_core'

def mean_at_1km(img, mp):
    return img.reduceResolution(ee.Reducer.mean(), maxPixels=mp).reproject('EPSG:4326', None, SCALE)

dem = ee.Image('USGS/SRTMGL1_003')
hansen = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
wc = ee.Image('ESA/WorldCover/v100/2020').select('Map')
def wc_frac(classes):
    return mean_at_1km(wc.remap(classes, [1] * len(classes), 0), 16384)

# west/east side from main-basin sink longitude (HydroSHEDS level 7)
B = 'WWF/HydroSHEDS/v1/Basins/hybas_7'
b = ee.FeatureCollection(B).filterBounds(ROI)
mains = b.aggregate_array('MAIN_BAS').distinct().getInfo()
sinks = ee.FeatureCollection(B).filter(ee.Filter.inList('HYBAS_ID', mains)).map(
    lambda f: f.set('lon', f.geometry().centroid(100).coordinates().get(0))).select(['HYBAS_ID', 'lon'])
lon = ee.Dictionary({str(int(f['properties']['HYBAS_ID'])): f['properties']['lon'] for f in sinks.getInfo()['features']})
b = b.map(lambda f: f.set('west', ee.Number(lon.get(ee.Number(f.get('MAIN_BAS')).format('%d'))).lt(77.7)))
west = ee.Image().byte().paint(b.filter(ee.Filter.eq('west', 1)), 1).unmask(0)

layers = ee.Image.cat([
    mean_at_1km(hansen.select('treecover2000').gte(30), 4096).rename('hansen30'),
    mean_at_1km(hansen.select('treecover2000').gte(10), 4096).rename('hansen10'),
    mean_at_1km(dem, 4096).rename('elev'),
    west.rename('west'),
]).float()
task = ee.batch.Export.image.toAsset(image=layers, description='wgeep_layers_1km_core', assetId=ASSET,
                                     region=ROI, crs='EPSG:4326', scale=SCALE, maxPixels=1e10)
task.start()
print('started', task.id)
