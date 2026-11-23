"""Phase 1 (v2): burnable vegetation classes from the Roy et al. vegetation type map (uploaded asset), inside the CEPF boundary.
Roy 'Value' codes come from VegAttributes.csv (data/ref/roy_VegAttributes.csv, gitignored).
Burnable classes (band 'burnable'):
  1 forest (natural types incl. swamp/riverine/sholas/mangrove; codes 11-32, 36-54, 58, 63, 66-87 except 87)
  2 shola grassland   = Roy grassland, lat<13.5, elev>=1400 m           (approximation by elevation/latitude)
  3 hill grassland/savanna = other Roy grassland (135-149), Kans (87), woodland/savanna (115-117)
  4 lateritic plateau grassland = Roy grassland, lat>=15, elev<1300 m   (approximation by elevation/latitude)
  5 scrub (120-134)
  6 forest plantation (90-103)
  7 tree crops/orchards/tea/coconut/etc (150-163)
  8 degraded forest (106)
Everything else (agriculture, water, settlement, barren, jhum, etc.) is not burnable.
Usage: phase1_burnable_roy.py [export]"""
import sys, ee
ee.Initialize(project='pyro-india-515605')
ROY = 'projects/pyro-india-515605/assets/VegetationTypeMap_India'
GEOM = ee.FeatureCollection('projects/pyro-india-515605/assets/cepf_boundary').geometry()
ASSET = 'projects/pyro-india-515605/assets/burnable_roy_30m'

def codes(*ranges):
    out = []
    for r in ranges: out += list(range(r[0], r[1] + 1)) if isinstance(r, tuple) else [r]
    return out
FOREST = [c for c in codes((11, 32), (36, 54), 58, 63, (66, 86)) if c not in (56, 57, 64)]
GRASS = codes((135, 149)); SAVANNA = codes((115, 117)); HILL_EXTRA = [87] + SAVANNA
SCRUB = codes((120, 134)); PLANT = codes((90, 103)); CROP = codes((150, 163)); DEGR = [106]

def build():
    roy = ee.Image(ROY).select(0).rename('v')
    inl = lambda l: roy.remap(l, [1] * len(l), 0).eq(1)
    elev = ee.Image('USGS/SRTMGL1_003'); lat = ee.Image.pixelLonLat().select('latitude')
    grass = inl(GRASS)
    shola = grass.And(lat.lt(13.5)).And(elev.gte(1400))
    later = grass.And(lat.gte(15)).And(elev.lt(1300)).And(shola.Not())
    hill = grass.And(shola.Not()).And(later.Not()).Or(inl(HILL_EXTRA))
    cls = (ee.Image(0).where(inl(FOREST), 1).where(inl(DEGR), 8).where(inl(CROP), 7).where(inl(PLANT), 6)
           .where(inl(SCRUB), 5).where(hill, 3).where(later, 4).where(shola, 2))
    return cls.rename('burnable').byte().clip(GEOM).selfMask()
if __name__ == '__main__':
    img = build()
    if len(sys.argv) > 1 and sys.argv[1] == 'export':
        # mode-resample to the 30 m Landsat grid
        img30 = img.reduceResolution(ee.Reducer.mode(), maxPixels=64).reproject('EPSG:4326', None, 30)
        t = ee.batch.Export.image.toAsset(img30, 'burnable_roy_30m', ASSET, region=GEOM, crs='EPSG:4326', scale=30,
                                           maxPixels=1e11, pyramidingPolicy={'.default': 'mode'})
        t.start(); print('started', t.id)
