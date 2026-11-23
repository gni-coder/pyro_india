"""Bandipur 2019 pilot statistics from the exported asset."""
import ee
ee.Initialize(project='pyro-india-515605')
BOX = ee.Geometry.Rectangle([76.30, 11.55, 76.95, 12.05], geodesic=False)
I = ee.Image('projects/pyro-india-515605/assets/bandipur_2019_sev')
K = ee.Image.pixelArea().divide(1e6)
roy = I.select('roy'); burnable = roy.gt(0)
doy = I.select('modis_doy'); fire = doy.gte(52).And(doy.lte(59)); near = I.select('modis_near').eq(1)
d, dc, rbr = I.select('dNBR'), I.select('dNBRc'), I.select('RBRc')
def km2(m, scale=30): return round(K.updateMask(m).reduceRegion(ee.Reducer.sum(), BOX, scale, maxPixels=1e10, tileScale=4).getInfo()['area'], 1)
print('valid (pre&post) burnable area in box km2:', km2(burnable.And(dc.mask())))
print('MODIS pilot-fire (DOY 52-59) km2 @500m:', km2(fire, 500))
inside = dc.updateMask(fire.And(burnable)).reduceRegion(ee.Reducer.percentile([5, 25, 50, 75, 95]), BOX, 30, maxPixels=1e10, tileScale=4).getInfo()
outside = dc.updateMask(near.Not().And(burnable)).reduceRegion(ee.Reducer.percentile([5, 25, 50, 75, 95]), BOX, 30, maxPixels=1e10, tileScale=4).getInfo()
print('corrected dNBR percentiles (5/25/50/75/95) inside MODIS fire :', [round(v, 3) for v in inside.values()])
print('corrected dNBR percentiles (5/25/50/75/95) far from fire     :', [round(v, 3) for v in outside.values()])
print('uncorrected dNBR median far from fire:', round(d.updateMask(near.Not().And(burnable)).reduceRegion(ee.Reducer.median(), BOX, 30, maxPixels=1e10, tileScale=4).getInfo()['dNBR'], 3))
for thr in (0.10, 0.15, 0.20, 0.27):
    per = dc.gte(thr).And(near).And(burnable)
    print(f'perimeter (corrected dNBR>={thr}, within 3 km of MODIS fire): {km2(per)} km2 | overlap with MODIS pixels {km2(per.And(fire))} km2')
per = dc.gte(0.15).And(near).And(burnable)
print('severity classes within perimeter (corrected dNBR, km2): unchanged-low 0.15-0.27', km2(per.And(dc.lt(0.27))), '| moderate 0.27-0.44', km2(per.And(dc.gte(0.27)).And(dc.lt(0.44))),
      '| high 0.44-0.66', km2(per.And(dc.gte(0.44)).And(dc.lt(0.66))), '| very high >=0.66', km2(per.And(dc.gte(0.66))))
