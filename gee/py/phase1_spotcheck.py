"""Phase 1 spot-check: stratified random points (10 per class) with Sentinel-2 RGB chips (dry season 2021, ~2.5 km window).
Writes analysis/figs/spotcheck_<class>.png contact sheets (5 x 2 chips) and analysis/spotcheck_points.csv. Usage: phase1_spotcheck.py"""
import io, csv, urllib.request, ee
from PIL import Image, ImageDraw
ee.Initialize(project='pyro-india-515605')
MASK = ee.Image('projects/pyro-india-515605/assets/burnable_roy_30m').select('burnable')
BND = ee.FeatureCollection('projects/pyro-india-515605/assets/cepf_boundary').geometry()
CLASSES = {1: 'forest', 2: 'shola grassland', 3: 'hill grassland-savanna', 4: 'lateritic grassland', 6: 'forest plantation'}
pts = MASK.stratifiedSample(numPoints=0, classBand='burnable', region=BND, scale=120, seed=7, classValues=list(CLASSES), classPoints=[10] * len(CLASSES),
                            geometries=True, tileScale=8)
feats = pts.getInfo()['features']
s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterDate('2021-01-15', '2021-04-15').filterBounds(BND)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)).median())
rows = []
for c, name in CLASSES.items():
    sheet = Image.new('RGB', (5 * 360, 2 * 380), 'white'); d = ImageDraw.Draw(sheet)
    sel = [f for f in feats if f['properties']['burnable'] == c]
    for i, f in enumerate(sel):
        lon, lat = f['geometry']['coordinates']; rows.append([name, i + 1, round(lat, 5), round(lon, 5)])
        reg = ee.Geometry.Point([lon, lat]).buffer(1250).bounds()
        url = s2.visualize(bands=['B4', 'B3', 'B2'], min=0, max=3000).getThumbURL({'region': reg, 'dimensions': 350, 'format': 'png'})
        try: im = Image.open(io.BytesIO(urllib.request.urlopen(url).read())).convert('RGB')
        except Exception as e: im = Image.new('RGB', (350, 350), 'grey'); print('chip fail', name, i, e)
        x, y = (i % 5) * 360, (i // 5) * 380
        sheet.paste(im, (x + 5, y + 25)); dd = ImageDraw.Draw(sheet)
        dd.ellipse([x + 5 + 175 - 5, y + 25 + 175 - 5, x + 5 + 175 + 5, y + 25 + 175 + 5], outline='red', width=2)
        dd.text((x + 8, y + 6), f'{name} #{i + 1}  {lat:.3f},{lon:.3f}', fill='black')
    sheet.save(f'analysis/figs/spotcheck_{name.replace(" ", "_")}.png'); print('saved', name, len(sel), flush=True)
csv.writer(open('analysis/spotcheck_points.csv', 'w', newline='')).writerows([['class', 'n', 'lat', 'lon']] + rows)
