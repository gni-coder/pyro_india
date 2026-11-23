"""Phase 2 pilot: Bandipur fire, Feb 2019. Landsat 8 NBR pre (composite 2019-01-20..02-20) / post (2019-03-13), with unburned-reference offset
per Roy burnable class, perimeter from corrected dNBR threshold confined to the MODIS burned-area neighbourhood; Sentinel-2 cross-check.
Prints numbers; use phase2_bandipur_maps.py for figures."""
import sys; sys.path.insert(0, 'gee/py')
import ee, severity as sv
ee.Initialize(project='pyro-india-515605')
BOX = ee.Geometry.Rectangle([76.30, 11.55, 76.95, 12.05], geodesic=False)
KM2 = ee.Image.pixelArea().divide(1e6)
L8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2'); S2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
def l8day(d): return sv.day_mosaic(L8, d, sv.l8_nbr, BOX)
# pre = median of clear L8 observations 2019-01-20..02-20 (paths 144+145); post = 2019-03-13 (path 144, 0% cloud; before the Mar 19-27 fires)
pre, post = sv.composite(L8, '2019-01-20', '2019-02-21', sv.l8_nbr, BOX), l8day('2019-03-13')
dnbr, rbr = sv.severity(pre, post)
# MODIS burned-area for the pilot fire window (DOY 52-59 = Feb 21-28) and its 3 km neighbourhood
ba = ee.ImageCollection('MODIS/061/MCD64A1').filterDate('2019-01-01', '2019-06-01').select('BurnDate').max().unmask(0)
fire_modis = ba.gte(52).And(ba.lte(59))
near = fire_modis.focalMax(3000, 'circle', 'meters')
# any MODIS burning Jan-May (to exclude from the unburned reference)
anyburn = ba.gt(0).focalMax(1500, 'circle', 'meters')
roy = ee.Image('projects/pyro-india-515605/assets/burnable_roy_30m').select('burnable')
group = roy.unmask(0)
unb = anyburn.Not().And(pre.mask()).And(post.mask()).And(roy.gt(0))
off = sv.offset(dnbr, unb, group, BOX, 30, [1, 3, 5, 6, 7]).getInfo()
off = {int(k): v for k, v in off.items() if v is not None}
print('unburned dNBR offset per Roy class (leaf-fall/phenology bias):', {k: round(v, 3) for k, v in off.items()})
dnbr_c = sv.apply_offset(dnbr, group, off).rename('dNBRc')
rbr_c = dnbr_c.divide(pre.add(1.001)).rename('RBRc')
for name, img in (('uncorrected dNBR', dnbr), ('corrected dNBR', dnbr_c)):
    s = img.updateMask(near.And(roy.gt(0))).reduceRegion(ee.Reducer.percentile([5, 25, 50, 75, 95]), BOX, 30, maxPixels=1e10).getInfo()
    print(name, 'percentiles inside MODIS-near burnable:', {k.split('_')[-1]: round(v, 3) for k, v in s.items() if v is not None})
for thr in (0.10, 0.15, 0.20, 0.27):
    per = dnbr_c.gte(thr).And(near).And(roy.gt(0))
    a = KM2.updateMask(per).reduceRegion(ee.Reducer.sum(), BOX, 30, maxPixels=1e10).getInfo()['area']
    print(f'perimeter area with corrected dNBR >= {thr}: {a:.1f} km2')
print('MODIS pilot-fire area km2:', round(KM2.updateMask(fire_modis).reduceRegion(ee.Reducer.sum(), BOX, 500, maxPixels=1e9).getInfo()['area'], 1))
