"""Compare reconstructed WGEEP mask with the CEPF boundary (areas, overlap)."""
import ee
ee.Initialize(project='pyro-india-515605')
ROI = ee.Geometry.Rectangle([72.5, 7.8, 78.3, 21.3], geodesic=False)
mine = ee.Image('projects/pyro-india-515605/assets/wgeep_mask_1km').eq(1)
cepf = ee.Image().byte().paint(ee.FeatureCollection('projects/pyro-india-515605/assets/cepf_boundary'), 1).unmask(0).eq(1) \
    .reproject('EPSG:4326', None, 1000)
area = ee.Image.pixelArea().divide(1e6)
def km2(m): return round(list(m.multiply(area).reduceRegion(ee.Reducer.sum(), ROI, 1000, maxPixels=1e10, tileScale=4).getInfo().values())[0])
a, c, i = km2(mine), km2(cepf), km2(mine.And(cepf))
print('reconstruction', a, '| CEPF', c, '| intersection', i, '| union', a + c - i, '| IoU', round(i / (a + c - i), 3))
print('reconstruction outside CEPF', km2(mine.And(cepf.Not())), '| CEPF outside reconstruction', km2(cepf.And(mine.Not())))
