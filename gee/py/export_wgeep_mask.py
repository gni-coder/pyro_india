"""Export the reconstructed WGEEP 1 km mask (byte, 1 = inside) as an EE asset."""
import ee, sys
sys.path.insert(0, 'gee/py')
import wgeep_reconstruct as w
t = ee.batch.Export.image.toAsset(image=w.final.unmask(0).byte().rename('wgeep'),
    description='wgeep_mask_1km', assetId='projects/pyro-india-515605/assets/wgeep_mask_1km',
    region=w.ROI, crs='EPSG:4326', scale=1000, maxPixels=1e10)
t.start(); print('started', t.id)
