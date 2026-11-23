"""Phase 2 pilot: Bandipur fire, Feb 2019. Landsat 8 NBR pre (composite 2019-01-20..02-20, paths 144+145) / post (2019-03-13, path 144),
unburned-reference offset per Roy burnable class (leaf fall/phenology), RBR, MODIS (MCD64A1) fire window DOY 52-59.
Usage: phase2_bandipur.py export   -> asset projects/pyro-india-515605/assets/bandipur_2019_sev (bands pre, post, dNBR, dNBRc, RBRc, modis_doy, modis_near, roy)"""
import sys; sys.path.insert(0, 'gee/py')
import ee, severity as sv
ee.Initialize(project='pyro-india-515605')
BOX = ee.Geometry.Rectangle([76.30, 11.55, 76.95, 12.05], geodesic=False)
ASSET = 'projects/pyro-india-515605/assets/bandipur_2019_sev'
CLASSES = [1, 3, 5, 6, 7]
L8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')

def build():
    pre = sv.composite(L8, '2019-01-20', '2019-02-21', sv.l8_nbr, BOX)
    post = sv.day_mosaic(L8, '2019-03-13', sv.l8_nbr, BOX)
    dnbr, _ = sv.severity(pre, post)
    ba = ee.ImageCollection('MODIS/061/MCD64A1').filterDate('2019-01-01', '2019-06-01').select('BurnDate').max().unmask(0)
    ba30 = ba.reproject('EPSG:4326', None, 500)                      # keep native 500 m grid for focal ops (cheap)
    fire = ba30.gte(52).And(ba30.lte(59))
    near = fire.focalMax(6, 'circle', 'pixels')                      # ~3 km
    anyburn = ba30.gt(0).focalMax(3, 'circle', 'pixels')              # ~1.5 km
    roy = ee.Image('projects/pyro-india-515605/assets/burnable_roy_30m').select('burnable').unmask(0)
    unb = anyburn.Not().And(pre.mask()).And(post.mask()).And(roy.gt(0))
    off = sv.offset(dnbr, unb, roy, BOX, 30, CLASSES)
    vals = [ee.Number(off.get(str(k), 0)) for k in CLASSES]
    dnbr_c = dnbr.subtract(roy.remap(CLASSES, vals, 0)).rename('dNBRc')
    rbr_c = dnbr_c.divide(pre.add(1.001)).rename('RBRc')
    return ee.Image.cat([pre.rename('pre'), post.rename('post'), dnbr, dnbr_c, rbr_c, ba.rename('modis_doy'), near.rename('modis_near'), roy.rename('roy')]).float()
if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'export':
    t = ee.batch.Export.image.toAsset(build(), 'bandipur_2019_sev', ASSET, region=BOX, crs='EPSG:4326', scale=30, maxPixels=1e10)
    t.start(); print('started', t.id)
