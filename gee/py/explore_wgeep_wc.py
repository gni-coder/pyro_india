"""Prototype: WGEEP-rule reconstruction. Prints areas for sanity checks."""
import ee
ee.Initialize(project='pyro-india-515605')
ROI = ee.Geometry.Rectangle([72.5, 7.8, 78.3, 21.3], geodesic=False)
SCALE = 1000

dem = ee.Image('USGS/SRTMGL1_003')
hansen = ee.Image('UMD/hansen/global_forest_change_2023_v1_11')
forest30 = hansen.select('treecover2000').gte(30)
# forest fraction and mean elevation at 1 km
forest_frac_h = forest30.reduceResolution(ee.Reducer.mean(), maxPixels=4096).reproject('EPSG:4326', None, SCALE)
elev = dem.reduceResolution(ee.Reducer.mean(), maxPixels=4096).reproject('EPSG:4326', None, SCALE)

# west/east side from main-basin sink longitude (HydroSHEDS)
b = ee.FeatureCollection('WWF/HydroSHEDS/v1/Basins/hybas_7').filterBounds(ROI)
mains = b.aggregate_array('MAIN_BAS').distinct().getInfo()
sinks = ee.FeatureCollection('WWF/HydroSHEDS/v1/Basins/hybas_7').filter(ee.Filter.inList('HYBAS_ID', mains))
sink_lon = {int(f['properties']['HYBAS_ID']): f['properties']['lon'] for f in
            sinks.map(lambda f: f.set('lon', f.geometry().centroid(100).coordinates().get(0))).select(['HYBAS_ID','lon']).getInfo()['features']}
print(len(mains), 'main basins')
def side(f):
    return f.set('west', ee.Number(ee.Dictionary(sink_lon_ee).get(ee.String(ee.Number(f.get('MAIN_BAS')).format('%d')))).lt(77.7))
sink_lon_ee = ee.Dictionary({str(k): v for k, v in sink_lon.items()})
b = b.map(side)
west = ee.Image().byte().paint(b.filter(ee.Filter.eq('west', 1)), 1).unmask(0).eq(1)


wc = ee.Image('ESA/WorldCover/v100/2020').select('Map')
def frac(classes):
    m = wc.remap(classes, [1]*len(classes), 0)
    return m.reduceResolution(ee.Reducer.mean(), maxPixels=16384).reproject('EPSG:4326', None, SCALE)
tree = frac([10]); natural = frac([10, 20, 30, 90, 95])
area = ee.Image.pixelArea().divide(1e6)
def km2(img, name):
    v = img.unmask(0).multiply(area).reduceRegion(ee.Reducer.sum(), ROI, SCALE, maxPixels=1e10, tileScale=4).getInfo()
    print(name, round(list(v.values())[0]), flush=True)
elev_rule = west.And(elev.gte(150)).Or(west.Not().And(elev.gte(500)))
for nm, f in (('tree', tree), ('tree+shrub+grass', natural)):
    for thr in (0.3, 0.5):
        m = f.gte(thr).And(elev_rule)
        for r in (0, 3):
            mm = m if r == 0 else m.focalMax(r, 'circle', 'pixels').focalMin(r, 'circle', 'pixels')
            km2(mm, f'WC {nm}>={thr} close r={r}km')
