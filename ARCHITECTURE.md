# Architecture: one atlas, many projects

The Third Pole Atlas is the shared spatial data infrastructure for the eco-socialist Third Pole and South Asia work. Projects
feed it; it feeds back to them and to the sister sites (azadi.asia map page, atmosphere atlas). Components are written once.

| Component | Lives in | Used by |
|---|---|---|
| Data build (grids → PNG, CF NetCDF, GeoTIFF; vectors → GeoJSON; STAC) | `build/build_data.py` | atlas; any project adds a function |
| Map shell (MapLibre, OpenFreeMap, graticule, legend, time bar, popups) | `web/app.js`, `web/style.css` | atlas; azadi.asia map page to reuse |
| Identity (computed mark, palette, type, social formats) | `build/build_brand.py`, `web/brand/` | atlas, azadi.asia, posts |
| Screenshots and design journal | `build/shoot.py`, `web/journal/` | all |
| Region outlines | `shared-geodata` | all |

Source projects: south-asia-smog (air), uib-snow-cover (snow), solar-wind-south-asia (energy).
Redundancy: every source repo keeps its own outputs; the atlas holds copies of published products, so either can rebuild the other.
