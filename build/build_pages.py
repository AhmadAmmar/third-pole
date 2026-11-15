"""Reading pages of the atlas (Data, Method, Design, About), built from Markdown-like Python strings into the site's
shell so all pages share one header and style.

    python build/build_pages.py
"""
import json
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web"
NAV = [("./", "Map"), ("data.html", "Data"), ("method.html", "Method"), ("design.html", "Design"), ("about.html", "About")]


def shell(slug, title, body, desc):
    nav = "".join(f'<a href="{h}"{" aria-current=page" if h == slug else ""}>{t}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Third Pole Atlas</title><meta name="description" content="{desc}">
<meta property="og:title" content="{title} · Third Pole Atlas"><meta property="og:image" content="brand/og-image.png">
<link rel="icon" href="brand/favicon.svg" type="image/svg+xml">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<link href="style.css" rel="stylesheet"></head><body>
<header class="masthead"><a class="brand" href="./"><img src="brand/mark.svg" alt="" width="40" height="40"><span><b>Third Pole Atlas</b><i>air and snow, across borders</i></span></a><nav>{nav}</nav></header>
<article class="page">{body}</article></body></html>"""


def data_page():
    m = json.loads((WEB / "data/manifest.json").read_text(encoding="utf-8"))
    rows = "".join(f"<tr><td>{L['title']}</td><td>{L['source']}</td><td>{L['months'][0]} to {L['months'][-1]}</td><td>{L['unit'] or '–'}</td>"
                   f"<td><a href='{L['netcdf']}' download>NetCDF</a> · <a href='data/stac/smog-{k}.json'>STAC</a></td></tr>" for k, L in m["smog"].items())
    snow = "".join(f"<tr><td>{L['title']}</td><td>MODIS MOD10A1F</td><td>2001–2025</td><td>days</td><td><a href='{L['tif']}' download>GeoTIFF</a> · <a href='data/stac/snow-{k}.json'>STAC</a></td></tr>" for k, L in m["snow"].items())
    tabs = sorted(p.name for p in (WEB / "data/tables").glob("*.csv"))
    tl = "".join(f"<li><a href='data/tables/{t}' download>{t}</a></li>" for t in tabs)
    return f"""<h1>Data</h1><p class="lede">Every layer on the map can be downloaded, cited and reused under CC BY 4.0. Last built {m['built']}.</p>
<h2>Gridded layers</h2><table><tr><th>Layer</th><th>Source</th><th>Period</th><th>Unit</th><th>Files</th></tr>{rows}{snow}</table>
<h2>Tables</h2><ul>{tl}</ul>
<h2>Catalogue and standards</h2>
<p>The whole collection is described by a static <a href="data/catalog.json">STAC 1.0 catalogue</a>, readable by QGIS (STAC plugin),
pystac, rstac and any STAC browser. Grids are CF-1.8 NetCDF (int16 packed, zlib), on WGS 84 (EPSG:4326) at 0.1°; rasters are GeoTIFF.
Tables are UTF-8 CSV with ISO 8601 dates. Page metadata follows schema.org <code>DataCatalog</code> so search engines index it.</p>
<h2>Reading the files</h2>
<pre><code>import xarray as xr
ds = xr.open_dataset("no2_monthly.nc")          # decoded to µmol m-2
ds.no2.sel(time="2024-11").plot()</code></pre>
<p>In QGIS: Layer → Add Raster Layer → the NetCDF; each band is one month.</p>
<h2>How to cite</h2><p>Ammar, A. ({m['built'][:4]}). <i>Third Pole Atlas: open data on air and snow</i>. https://ahmadammar.github.io/third-pole/ (accessed date). Please also cite the original data providers listed above.</p>"""


METHOD = """<h1>Method</h1><p class="lede">How each layer is made, what it shows and what it cannot show.</p>
<h2>Air</h2>
<p><b>Retrievals.</b> Sentinel-5P TROPOMI offline Level-3 products (NO₂, SO₂, CO, HCHO, O₃, UV aerosol index) as ingested by Google Earth
Engine, with its quality screening; MODIS MAIAC aerosol optical depth at 550 nm (MCD19A2 v6.1, 1 km); FIRMS MODIS active fires
(confidence ≥ 50). Region 60–98° E, 5–37° N.</p>
<p><b>Aggregation.</b> Each day is averaged first and the month is the mean of daily means, so days with two overpasses do not count twice. The
number of valid days per cell is kept in the source grids. Cells are 0.1° (about 11 km), close to TROPOMI's 5.5 × 3.5 km pixels.
The latest month is partial until it ends; it is redrawn at each update.</p>
<p><b>Columns are not breathing air.</b> A column counts all molecules between ground and space. Winter NO₂ columns rise partly because
the shallow winter boundary layer traps emissions, and haze can hide the surface from the sensor. For surface PM2.5 the atlas uses ground
monitors (OpenAQ) and a calibrated model; a daily 1 km surface PM2.5 and population exposure layer is in preparation.</p>
<p><b>Colour.</b> Fixed ranges per layer so months can be compared; perceptually uniform, colour-blind safe maps (cividis, magma, ColorBrewer);
low values fade so the land stays readable; cells with no valid retrieval are transparent, not zero.</p>
<h2>Snow</h2>
<p>MODIS MOD10A1F cloud-gap-filled daily snow cover, hydrological years 2001–2025; Sen slopes of snow-cover days with Mann–Kendall
tests and false discovery rate control, by range and elevation band. Change classes per pixel. Full method in the
<a href="https://github.com/AhmadAmmar/uib-snow-cover">uib-snow-cover</a> repository.</p>
<h2>Updates</h2>
<p>The source repositories run incremental downloads to the present day (only new and the last two months are fetched again), then
<code>build/build_data.py</code> redraws the newest maps, rewrites the NetCDF and STAC files, and the site is redeployed. Every step is logged.</p>
<h2>Code</h2><p>All code is open: <a href="https://github.com/AhmadAmmar/third-pole">third-pole</a> (this atlas),
<a href="https://github.com/AhmadAmmar/south-asia-smog">south-asia-smog</a>, <a href="https://github.com/AhmadAmmar/uib-snow-cover">uib-snow-cover</a>.</p>"""


def design_page():
    shots = sorted(p for p in (WEB / "journal").rglob("*.png"))
    by_v = {}
    for p in shots:
        by_v.setdefault(p.parent.name, []).append(p)
    figs = "".join(f"<h3>{v}</h3>" + "".join(f'<figure><img src="journal/{v}/{p.name}" alt="{v} {p.stem}" loading="lazy"><figcaption>{v}, {p.stem.replace("-", " ")}</figcaption></figure>' for p in ps)
                   for v, ps in sorted(by_v.items()))
    log = (WEB / "journal/log.html").read_text(encoding="utf-8") if (WEB / "journal/log.html").exists() else ""
    return f"""<h1>Design</h1><p class="lede">The reasoning behind the look, and every version as it was.</p>
<h2>Principles</h2>
<ul><li><b>Map first, ink second.</b> Paper ground, one dark ink, one red accent. Ornament only where it carries information: the graticule,
the scale bar, the legend.</li>
<li><b>Classical type.</b> EB Garamond (Garamond's 1592 specimen) for titles and reading; Source Sans 3 for numbers, labels and controls,
where a sans reads faster at small sizes. Small capitals for field names, as in printed atlases.</li>
<li><b>Honest colour.</b> Perceptually uniform, colour-blind safe ramps; fixed ranges across time; no-data is transparent.</li>
<li><b>Borders drawn lightly.</b> Air and snow cross borders; the basemap's boundaries are kept faint and names appear in local scripts.</li>
<li><b>Responsive and accessible.</b> One column on phones, map first; keyboard controls; text alternatives for charts; dark mode follows the
reader's system.</li></ul>
<h2>The mark</h2>
<figure><img src="brand/mark-paper.png" alt="Third Pole mark" style="max-width:320px"><figcaption>The mark is computed, not drawn:
the Third Pole domain in a Lambert azimuthal equal-area projection centred on 88° E, 33° N, with inward contours at equal steps, framed by
parallels of a polar view, a red point at north. One colour, so it can be stencilled, printed or embroidered.
Source: <code>build/build_brand.py</code>.</figcaption></figure>
<p>Brand files: <a href="brand/logo.svg">logo (SVG)</a> · <a href="brand/mark.svg">mark</a> · <a href="brand/instagram-post.png">Instagram post</a>
· <a href="brand/instagram-story.png">story</a> · <a href="brand/facebook-cover.png">Facebook cover</a> · <a href="brand/og-image.png">link preview</a>.</p>
<h2>Journal</h2>{log}{figs}"""


ABOUT = """<h1>About</h1><p class="lede">An open atlas of air and snow for the Third Pole and South Asia.</p>
<p>Air pollution and melting snow do not stop at borders drawn across the Indus and the Ganges, and neither should the data about them.
The Third Pole, the Hindu Kush–Karakoram–Himalaya and the Tibetan Plateau, stores the largest mass of ice outside the poles and feeds rivers
that nearly two billion people depend on. The plains below breathe some of the dirtiest air on Earth each winter. This atlas makes both
visible from open satellite data, for anyone, on any side of any border, with every number downloadable.</p>
<h2>Commitments</h2>
<ul><li><b>Open by default</b>: data CC BY 4.0, code open, methods written down; FAIR principles (findable, accessible, interoperable, reusable).</li>
<li><b>Standards</b>: STAC, CF conventions, OGC-readable formats, ISO 8601 time, EPSG codes, schema.org metadata; built with free and
open-source software (MapLibre, OpenFreeMap, GDAL, xarray, Python).</li>
<li><b>Shared across the region</b>: compatible with regional and international data infrastructures so that agencies, researchers and
citizens in every country can use the same layers.</li>
<li><b>Updated</b>: series run to the present and are refreshed regularly.</li></ul>
<h2>Who</h2><p>Ahmad Ammar, Ulster University. Contributions, corrections and questions are welcome through the
<a href="https://github.com/AhmadAmmar/third-pole/issues">issue tracker</a>.</p>"""

if __name__ == "__main__":
    pages = {"data.html": ("Data", data_page(), "Download the atlas data: NetCDF, GeoTIFF, CSV and a STAC catalogue."),
             "method.html": ("Method", METHOD, "How the atlas layers are made, and their limits."),
             "design.html": ("Design", design_page(), "Design principles, the computed mark, and the design journal with every version."),
             "about.html": ("About", ABOUT, "An open atlas of air and snow for the Third Pole and South Asia.")}
    for f, (t, b, d) in pages.items():
        (WEB / f).write_text(shell(f, t, b, d), encoding="utf-8")
    print("pages", list(pages))
