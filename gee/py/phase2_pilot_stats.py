"""Pilot statistics + maps from the exported asset. Usage: phase2_pilot_stats.py <nilgiris2017|bandipur2019> [maps]"""
import sys, urllib.request, ee
ee.Initialize(project='pyro-india-515605')
CFG = {'nilgiris2017': dict(box=[76.35, 11.15, 76.90, 11.60], asset='nilgiris_2017_sev', doy=(50, 72), s2pre=('2017-02-01', '2017-02-12'), s2post=('2017-03-20', '2017-04-01')),
       'bandipur2019': dict(box=[76.30, 11.55, 76.95, 12.05], asset='bandipur_2019_sev', doy=(52, 59), s2pre=('2019-02-13', '2019-02-19'), s2post=('2019-03-08', '2019-03-19'))}
c = CFG[sys.argv[1]]; name = sys.argv[1]
BOX = ee.Geometry.Rectangle(c['box'], geodesic=False)
I = ee.Image(f"projects/pyro-india-515605/assets/{c['asset']}")
K = ee.Image.pixelArea().divide(1e6)
roy = I.select('roy'); burnable = roy.gt(0); doy = I.select('modis_doy')
fire = doy.gte(c['doy'][0]).And(doy.lte(c['doy'][1])); near = I.select('modis_near').eq(1)
d, dc = I.select('dNBR'), I.select('dNBRc')
def km2(m, s=30): return round(K.updateMask(m).reduceRegion(ee.Reducer.sum(), BOX, s, maxPixels=1e10, tileScale=4).getInfo()['area'], 1)
def pct(img, m):
    r = img.updateMask(m).reduceRegion(ee.Reducer.percentile([5, 25, 50, 75, 95]), BOX, 30, maxPixels=1e10, tileScale=4).getInfo()
    return {k.split('_')[-1]: round(v, 3) for k, v in sorted(r.items(), key=lambda x: int(x[0].split('_p')[-1]) if '_p' in x[0] else 0)}
if len(sys.argv) < 3:
    print('MODIS fire-window km2 @500m:', km2(fire, 500))
    print('corrected dNBR pct inside MODIS fire :', pct(dc, fire.And(burnable)))
    print('corrected dNBR pct far from fire     :', pct(dc, near.Not().And(burnable)))
    print('uncorrected dNBR median far from fire:', round(d.updateMask(near.Not().And(burnable)).reduceRegion(ee.Reducer.median(), BOX, 30, maxPixels=1e10, tileScale=4).getInfo()['dNBR'], 3))
    for thr in (0.10, 0.15, 0.20, 0.27):
        per = dc.gte(thr).And(near).And(burnable)
        print(f'perimeter (corrected dNBR>={thr}, within 3 km of MODIS fire): {km2(per)} km2 | on MODIS pixels {km2(per.And(fire))} km2')
    per = dc.gte(0.15).And(near).And(burnable)
    print('perimeter(>=0.15) area by Roy class: ', {k: km2(per.And(roy.eq(k))) for k in (1, 2, 3, 5, 6, 7)})
    print('severity classes in perimeter(>=0.15): low 0.15-0.27', km2(per.And(dc.lt(0.27))), '| moderate 0.27-0.44', km2(per.And(dc.gte(0.27)).And(dc.lt(0.44))), '| high 0.44-0.66', km2(per.And(dc.gte(0.44)).And(dc.lt(0.66))), '| very high >=0.66', km2(per.And(dc.gte(0.66))))
else:
    per = dc.gte(0.15).And(near).And(roy.gt(0)).selfMask()
    edge = per.focalMax(1).subtract(per.unmask(0)).selfMask().visualize(palette=['00ffff'])
    # Landsat-only candidates: corrected dNBR >= 0.20, clusters >= 25 px, > 1.5 km from any MODIS burn (yellow)
    anymodis = doy.gt(0).reproject('EPSG:4326', None, 500).focalMax(3, 'circle', 'pixels')
    cand = dc.gte(0.20).And(roy.gt(0)).And(anymodis.Not()).selfMask().connectedPixelCount(100).gte(25).selfMask()
    edge = ee.ImageCollection([cand.focalMax(1).subtract(cand.unmask(0)).selfMask().visualize(palette=['ffff00']), edge]).mosaic()
    s2 = lambda a, b: ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(BOX).filterDate(*a if False else (a, b)).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25)).median()
    fc = lambda im: im.visualize(bands=['B12', 'B8', 'B4'], min=[200, 800, 100], max=[3500, 4500, 1800])
    sev = dc.updateMask(roy.gt(0)).visualize(min=-0.1, max=0.9, palette=['2b83ba', 'ffffbf', 'fdae61', 'd7191c', '67001f'])
    for k, im in {'a_severity_dNBRc': ee.ImageCollection([sev, edge]).mosaic(), 'b_S2_pre': ee.ImageCollection([fc(s2(*c['s2pre'])), edge]).mosaic(),
                  'c_S2_post': ee.ImageCollection([fc(s2(*c['s2post'])), edge]).mosaic()}.items():
        open(f'analysis/figs/{name}_{k}.png', 'wb').write(urllib.request.urlopen(im.getThumbURL({'region': BOX, 'dimensions': 1100, 'format': 'png'})).read()); print('saved', k, flush=True)
