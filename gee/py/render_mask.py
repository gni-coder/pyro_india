"""Render the exported WGEEP mask asset over terrain. Usage: render_mask.py <prefix>"""
import sys, urllib.request, ee
ee.Initialize(project='pyro-india-515605')
final = ee.Image('projects/pyro-india-515605/assets/wgeep_mask_1km').eq(1).selfMask()
hs = ee.Terrain.hillshade(ee.Image('USGS/SRTMGL1_003').reproject('EPSG:4326', None, 500)).visualize(min=100, max=255, palette=['333333', 'ffffff'])
fill = final.visualize(palette=['d62728'], opacity=0.45)
edge = final.focalMax(1).subtract(final.unmask(0).focalMin(1)).selfMask().visualize(palette=['000000'])
img = ee.ImageCollection([hs, fill, edge]).mosaic()
for i, (a, b) in enumerate([(7.8, 12.0), (12.0, 16.5), (16.5, 21.3)]):
    reg = ee.Geometry.Rectangle([72.5, a, 78.3, b], geodesic=False)
    url = img.getThumbURL({'region': reg, 'dimensions': 1100, 'format': 'png'})
    open(f'analysis/figs/{sys.argv[1]}_{i+1}.png', 'wb').write(urllib.request.urlopen(url).read())
    print('saved', i + 1, flush=True)
