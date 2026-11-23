// Phase 0: load and display the study boundary (CEPF) (Code Editor).
var cfg = require('users/YOUR_USER/pyro-india:gee/config'); // adjust to your repo path
var wg = ee.FeatureCollection(cfg.BOUNDARY_ASSET);
Map.centerObject(wg, 6);
Map.addLayer(wg.style({color: 'red', fillColor: '00000000'}), {}, 'Study boundary (CEPF)');
print('Features', wg.size());
print('Area (km2)', wg.geometry().area({maxError: 100}).divide(1e6));
