"""Check Landsat-only burn candidates (Nilgiris 2017): 10 random candidate pixels -> Sentinel-2 SWIR false-colour chips before/after (1.8 km window)."""
import io, urllib.request, ee
from PIL import Image, ImageDraw
ee.Initialize(project='pyro-india-515605')
BOX = ee.Geometry.Rectangle([76.35, 11.15, 76.90, 11.60], geodesic=False)
I = ee.Image('projects/pyro-india-515605/assets/nilgiris_2017_sev')
roy = I.select('roy'); dc = I.select('dNBRc'); doy = I.select('modis_doy')
anymodis = doy.gt(0).reproject('EPSG:4326', None, 500).focalMax(3, 'circle', 'pixels')
cand = dc.gte(0.20).And(roy.gt(0)).And(anymodis.Not()).selfMask().connectedPixelCount(100).gte(25).selfMask()
pts = cand.rename('c').reduceToVectors(geometry=BOX, scale=30, geometryType='centroid', eightConnected=True, maxPixels=1e9, tileScale=8, reducer=ee.Reducer.countEvery())
feats = pts.sort('count', False).limit(60).getInfo()['features']    # 60 biggest clusters
import random; random.seed(5); random.shuffle(feats)
# keep points >= 1.5 km apart
sel = []
for f in feats:
    x, y = f['geometry']['coordinates']
    if all(((x - a) * 111 * 0.98) ** 2 + ((y - b) * 111) ** 2 > 1.5 ** 2 for a, b in sel): sel.append((x, y))
    if len(sel) == 10: break
s2 = lambda a, b: ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(BOX).filterDate(a, b).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)).median()
vis = lambda im: im.visualize(bands=['B12', 'B8', 'B4'], min=[200, 800, 100], max=[3500, 4500, 1800])
pre, post = vis(s2('2017-02-01', '2017-02-12')), vis(s2('2017-03-20', '2017-04-01'))
W = 330; sheet = Image.new('RGB', (5 * (W + 8), 4 * (W + 28)), 'white'); d = ImageDraw.Draw(sheet)
for i, (x, y) in enumerate(sel):
    reg = ee.Geometry.Point([x, y]).buffer(900).bounds(); col, row = i % 5, (i // 5) * 2
    for k, (im, lab) in enumerate(((pre, 'pre'), (post, 'post'))):
        try: ch = Image.open(io.BytesIO(urllib.request.urlopen(im.getThumbURL({'region': reg, 'dimensions': W, 'format': 'png'})).read())).convert('RGB')
        except Exception as e: ch = Image.new('RGB', (W, W), 'grey'); print('fail', i, lab, e)
        ox, oy = col * (W + 8), (row + k) * (W + 28)
        sheet.paste(ch, (ox, oy + 18)); d.text((ox + 3, oy + 3), f'#{i + 1} {lab} {y:.3f},{x:.3f}', fill='black')
        c = W // 2; d.ellipse([ox + c - 4, oy + 18 + c - 4, ox + c + 4, oy + 18 + c + 4], outline='yellow', width=2)
sheet.save('analysis/figs/nilgiris2017_candidates_check.png'); print('saved', len(sel))
