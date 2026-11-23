"""Render Bandipur 2019 pilot maps: (a) corrected dNBR severity, (b) Sentinel-2 post-fire SWIR false colour (B12,B8,B4, 2019-03-13..18) and pre-fire; perimeter outline (corrected dNBR>=0.15 within 3 km of MODIS fire)."""
import io, urllib.request, ee
ee.Initialize(project='pyro-india-515605')
BOX = ee.Geometry.Rectangle([76.30, 11.55, 76.95, 12.05], geodesic=False)
I = ee.Image('projects/pyro-india-515605/assets/bandipur_2019_sev')
roy = I.select('roy'); dc = I.select('dNBRc'); doy = I.select('modis_doy')
near = I.select('modis_near').eq(1); fire = doy.gte(52).And(doy.lte(59))
per = dc.gte(0.15).And(near).And(roy.gt(0)).selfMask()
edge = per.focalMax(1).subtract(per.unmask(0)).selfMask().visualize(palette=['00ffff'])
modis = fire.selfMask().reproject('EPSG:4326', None, 500)
modis_edge = modis.focalMax(1).subtract(modis).selfMask().visualize(palette=['ffffff'])
s2 = lambda a, b: ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(BOX).filterDate(a, b).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).median()
fc = lambda im: im.visualize(bands=['B12', 'B8', 'B4'], min=[200, 800, 100], max=[3500, 4500, 1800])
sev = dc.updateMask(roy.gt(0)).visualize(min=-0.1, max=0.9, palette=['2b83ba', 'ffffbf', 'fdae61', 'd7191c', '67001f'])
panels = {'a_severity_dNBRc': ee.ImageCollection([sev, edge]).mosaic(),
          'b_S2_pre': ee.ImageCollection([fc(s2('2019-02-13', '2019-02-19')), edge]).mosaic(),
          'c_S2_post': ee.ImageCollection([fc(s2('2019-03-08', '2019-03-19')), edge]).mosaic()}
for k, im in panels.items():
    url = im.getThumbURL({'region': BOX, 'dimensions': 1100, 'format': 'png'})
    open(f'analysis/figs/bandipur_{k}.png', 'wb').write(urllib.request.urlopen(url).read()); print('saved', k, flush=True)
