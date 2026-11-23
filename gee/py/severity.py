"""Spectral burn-severity helpers (Earth Engine, Python). Reused by the pilot and the scale-up.
NBR = (NIR - SWIR2) / (NIR + SWIR2); dNBR = NBR_pre - NBR_post; RBR = dNBR / (NBR_pre + 1.001) (Parks et al. 2014).
Leaf-fall / phenology offset: subtract the median dNBR of unburned pixels of the same vegetation class (Parks et al. 2018 style)."""
import ee

def l8_nbr(img):
    """Landsat 8 C2 L2 -> NBR band (scaled surface reflectance), cloud/shadow/snow-masked via QA_PIXEL."""
    qa = img.select('QA_PIXEL')
    clear = qa.bitwiseAnd(0b11111).eq(0)                      # fill, dilated cloud, cirrus, cloud, shadow all clear
    sr = img.select(['SR_B5', 'SR_B7']).multiply(0.0000275).add(-0.2)
    return sr.normalizedDifference(['SR_B5', 'SR_B7']).rename('NBR').updateMask(clear)

def s2_nbr(img):
    """Sentinel-2 SR harmonised -> NBR (B8, B12), masked with SCL (vegetation/bare/soil classes only)."""
    scl = img.select('SCL'); ok = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)).Or(scl.eq(11))
    return img.select(['B8', 'B12']).normalizedDifference(['B8', 'B12']).rename('NBR').updateMask(ok)

def day_mosaic(col, date, nbr_fn, region):
    d = ee.Date(date)
    return nbr_fn_mosaic(col.filterBounds(region).filterDate(d, d.advance(1, 'day')), nbr_fn)

def nbr_fn_mosaic(col, nbr_fn):
    return col.map(nbr_fn).mosaic()

def composite(col, start, end, nbr_fn, region):
    """Median NBR of all clear observations in [start, end) (use when adjacent Landsat paths cover the region on different dates)."""
    return col.filterBounds(region).filterDate(start, end).map(nbr_fn).median()

def severity(pre, post):
    """pre, post: single-band NBR images -> dNBR, RBR (uncorrected)."""
    dnbr = pre.subtract(post).rename('dNBR')
    rbr = dnbr.divide(pre.add(1.001)).rename('RBR')
    return dnbr, rbr

def offset(band, unburned_mask, group, region, scale, classes):
    """Median of `band` over unburned pixels, per class value in `classes`. Returns ee.Dictionary {str(class): median} (null if no pixels).
    (Looped reduceRegion calls: Reducer.group() returned empty medians on this data.)"""
    out = {}
    for k in classes:
        r = band.updateMask(unburned_mask.And(group.eq(k))).reduceRegion(ee.Reducer.median(), region, scale, maxPixels=1e10, tileScale=4)
        out[str(k)] = r.get(band.bandNames().get(0))
    return ee.Dictionary(out)

def apply_offset(band, group, table):
    """table: dict {class_value: offset}. Returns band - offset(class)."""
    keys = list(table); vals = [table[k] for k in keys]
    return band.subtract(group.remap(keys, vals, 0))
