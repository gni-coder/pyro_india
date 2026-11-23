"""Phase 1: burnable vegetation mask inside the study boundary (CEPF), 30 m.
Base: ESA WorldCover v200 (2021) tree/shrub/grass, majority-resampled 10 m -> 30 m.
Classes (band 'burnable'): 1 forest (tree cover; plantations NOT separable yet -> see 'plantation' TODO),
  2 shola grassland (grass, lat<13.5, elev>=1400 m), 3 hill grassland/savanna (other grass, elev<1400 m, lat<15 or elev>=1300),
  4 lateritic plateau grassland (grass, lat>=15, elev<1300 m), 5 shrub/scrub.
Subtype rules are elevation/latitude approximations, not mapped ecosystems. Band 'was_veg2001' flags MODIS 2001
forest/savanna/grass pixels (IGBP 1-5,8,9,10) so grassland later lost to other uses can be audited.
Usage: phase1_burnable_mask.py [export]"""
import sys, ee
ee.Initialize(project='pyro-india-515605')
BND = ee.FeatureCollection('projects/pyro-india-515605/assets/cepf_boundary')
GEOM = BND.geometry()
ASSET = 'projects/pyro-india-515605/assets/burnable_mask_30m'

def build():
    wc = ee.Image('ESA/WorldCover/v200/2021').select('Map')
    wc30 = wc.reduceResolution(ee.Reducer.mode(), maxPixels=64).reproject('EPSG:4326', None, 30)
    elev = ee.Image('USGS/SRTMGL1_003')
    lat = ee.Image.pixelLonLat().select('latitude')
    tree, shrub, grass = wc30.eq(10), wc30.eq(20), wc30.eq(30)
    shola = grass.And(lat.lt(13.5)).And(elev.gte(1400))
    later = grass.And(lat.gte(15)).And(elev.lt(1300)).And(shola.Not())
    hill = grass.And(shola.Not()).And(later.Not())
    cls = ee.Image(0).where(tree, 1).where(shrub, 5).where(hill, 3).where(later, 4).where(shola, 2)
    igbp = ee.ImageCollection('MODIS/061/MCD12Q1').filter(ee.Filter.calendarRange(2001, 2001, 'year')).first().select('LC_Type1')
    veg2001 = igbp.lte(5).Or(igbp.eq(8)).Or(igbp.eq(9)).Or(igbp.eq(10))
    return ee.Image.cat([cls.rename('burnable'), veg2001.rename('was_veg2001')]).byte().clip(GEOM).updateMask(cls.gt(0).Or(veg2001))
if __name__ == '__main__':
    img = build()
    if len(sys.argv) > 1 and sys.argv[1] == 'export':
        t = ee.batch.Export.image.toAsset(img, 'burnable_mask_30m', ASSET, region=GEOM, crs='EPSG:4326', scale=30, maxPixels=1e11,
                                           pyramidingPolicy={'.default': 'mode'})
        t.start(); print('started', t.id)
