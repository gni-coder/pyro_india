"""Phase 2 pilot pipeline (configurable). Landsat 8 NBR pre/post, unburned-reference offset per Roy burnable class (leaf fall/phenology),
corrected dNBR / RBR, MODIS MCD64A1 fire window. Exports a 30 m asset.
Usage: phase2_pilot.py <bandipur2019|nilgiris2017> export"""
import sys; sys.path.insert(0, 'gee/py')
import ee, severity as sv
ee.Initialize(project='pyro-india-515605')
CONFIG = {
    'bandipur2019': dict(box=[76.30, 11.55, 76.95, 12.05], pre=('2019-01-20', '2019-02-21'), post=('2019-03-13', '2019-03-14'),
                         doy=(52, 59), year=2019, classes=[1, 3, 5, 6, 7], asset='bandipur_2019_sev'),
    'nilgiris2017': dict(box=[76.35, 11.15, 76.90, 11.60], pre=('2017-02-03', '2017-02-04'), post=('2017-03-23', '2017-03-24'),
                         doy=(50, 72), year=2017, classes=[1, 2, 3, 5, 6, 7], asset='nilgiris_2017_sev'),
}
L8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')

def build(c):
    box = ee.Geometry.Rectangle(c['box'], geodesic=False)
    pre = sv.composite(L8, *c['pre'], sv.l8_nbr, box); post = sv.composite(L8, *c['post'], sv.l8_nbr, box)
    dnbr, _ = sv.severity(pre, post)
    y = c['year']
    ba = ee.ImageCollection('MODIS/061/MCD64A1').filterDate(f'{y}-01-01', f'{y}-06-01').select('BurnDate').max().unmask(0)
    ba5 = ba.reproject('EPSG:4326', None, 500)
    fire = ba5.gte(c['doy'][0]).And(ba5.lte(c['doy'][1]))
    near = fire.focalMax(6, 'circle', 'pixels')                      # ~3 km
    anyburn = ba5.gt(0).focalMax(3, 'circle', 'pixels')              # ~1.5 km
    roy = ee.Image('projects/pyro-india-515605/assets/burnable_roy_30m').select('burnable').unmask(0)
    unb = anyburn.Not().And(pre.mask()).And(post.mask()).And(roy.gt(0))
    off = sv.offset(dnbr, unb, roy, box, 30, c['classes'])
    vals = [ee.Number(off.get(str(k), 0)) for k in c['classes']]
    dnbr_c = dnbr.subtract(roy.remap(c['classes'], vals, 0)).rename('dNBRc')
    rbr_c = dnbr_c.divide(pre.add(1.001)).rename('RBRc')
    return ee.Image.cat([pre.rename('pre'), post.rename('post'), dnbr, dnbr_c, rbr_c, ba.rename('modis_doy'), near.rename('modis_near'), roy.rename('roy')]).float(), box, off
if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[2] == 'export':
    c = CONFIG[sys.argv[1]]; img, box, off = build(c)
    print('unburned dNBR offsets by Roy class:', {k: (round(v, 3) if v is not None else None) for k, v in off.getInfo().items()})
    t = ee.batch.Export.image.toAsset(img, c['asset'], f"projects/pyro-india-515605/assets/{c['asset']}", region=box, crs='EPSG:4326', scale=30, maxPixels=1e10)
    t.start(); print('started', t.id)
