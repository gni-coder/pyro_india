# pyro-india

Burn severity and pyrodiversity across the Western Ghats, 2001–present, and the drivers of pyrodiversity.
Adapts Steel et al. (2021, *Proc. R. Soc. B*, "Quantifying pyrodiversity and its drivers"; code: https://github.com/zacksteel/pyrodiversity).

## Design decisions
- **Area:** Western Ghats, CEPF ecosystem-profile boundary (CEPF 2007; Conservation Biology Institute, Data Basin, CC BY 3.0; 6 polygons, ~109,000 km²). Chosen over the WGEEP (Gadgil 2011) boundary, whose shapefile is not publicly downloadable. A WGEEP-rule reconstruction (`gee/py/wgeep_reconstruct.py`, ~114,800 km², overlap with CEPF 0.68) is kept as a sensitivity check.
- **Vegetation:** forest, all grassland types (shola, hill grasslands/savanna, northern lateritic plateau grasslands), plantations as a separate class.
- **Period:** 2001–present.
- **Fire perimeters:** derived from Landsat dNBR, confirmed and dated with MODIS MCD64A1 / active fire and VIIRS.
- **Severity:** continuous RBR/RdNBR (spectral severity; no field CBI).
- **Units:** equal-area hexagons (~25 km², sensitivity at 10 and 100 km²) plus a moving-window FDis map. PA status and vegetation type are predictors/groups.
- **Tools:** GEE Code Editor (JavaScript), R (terra, sf, FD, brms).
- **Pilots:** Bandipur Feb 2019; one shola-grassland fire (TBD).

## Layout
- `gee/` Earth Engine JavaScript. `gee/lib/` holds pure functions that run in Node and the Code Editor; Map/ui/print code stays in top-level scripts.
- `R/` reusable R functions; `analysis/` analysis scripts.
- `data/` local data (gitignored).

## Setup
1. Study boundary asset: `projects/pyro-india-515605/assets/cepf_boundary` (set in `gee/config.js`; created by `gee/py/upload_cepf.py` from the Data Basin shapefile, which is not stored in the repo). Cite: CEPF 2007, Conservation Biology Institute (Data Basin).
2. R: `install.packages("renv"); renv::init()` then install terra, sf, FD, brms.

## Known risks
Leaf fall and fast recovery in the Feb–May fire season; MCD64A1 misses small grassland fires; Landsat 7 SLC-off gaps (2003+, and 2012 sole-Landsat year); severity differs in meaning between forest and grassland; grasslands converted to plantations since 2001.
