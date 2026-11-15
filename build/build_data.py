"""Build the portal's open data from the project repositories (south-asia-smog, uib-snow-cover).

    python build/build_data.py

Smog: for every monthly grid a colour-mapped PNG for the map (EPSG:4326 bounds, a fixed colour range per layer so
months compare), and one CF-1.8 NetCDF per layer with all months, for download. Snow: change rasters as PNG and
GeoTIFF. Tables copied as CSV. A STAC 1.0 static catalogue describes every collection, and web/data/manifest.json
lists what the map shows. Incremental: existing PNGs are redrawn only for the last two months.
"""
import json
import shutil
from datetime import date
from pathlib import Path

import matplotlib
import numpy as np
import xarray as xr
from matplotlib import colors
from PIL import Image

DEV = Path(__file__).resolve().parents[2]
SMOG, SNOW = DEV / "south-asia-smog", DEV / "uib-snow-cover"
WEB = Path(__file__).resolve().parents[1] / "web"
D = WEB / "data"
W, E, S, N, RES = 60.0, 98.0, 5.0, 37.0, 0.1
BOUNDS = [[W, N], [E, N], [E, S], [W, S]]
import sys
REDRAW = "--redraw" in sys.argv
COP = "Copernicus Sentinel data, free and open"
# layer: (title, unit, vmin, vmax, colormap, source, licence)
LAYERS = {
    "no2": ("Tropospheric NO₂ column", "µmol m⁻²", 0, 120, "cividis", "Copernicus Sentinel-5P TROPOMI, OFFL L3", COP),
    "aod": ("Aerosol optical depth, 550 nm", "", 0, 1.2, "magma_r", "NASA MODIS MAIAC MCD19A2 v6.1", "NASA open data"),
    "uvai": ("UV absorbing aerosol index", "index", -1, 2, "PuOr_r", "Copernicus Sentinel-5P TROPOMI", COP),
    "so2": ("SO₂ column", "µmol m⁻²", 0, 300, "YlOrBr", "Copernicus Sentinel-5P TROPOMI", COP),
    "co": ("Carbon monoxide column", "mmol m⁻²", 25, 55, "BuPu", "Copernicus Sentinel-5P TROPOMI", COP),
    "hcho": ("Tropospheric formaldehyde", "µmol m⁻²", 0, 300, "YlGn", "Copernicus Sentinel-5P TROPOMI", COP),
    "o3": ("Total ozone column", "mmol m⁻²", 110, 140, "Blues", "Copernicus Sentinel-5P TROPOMI", COP),
    "fire": ("Active fire detections", "count per cell", 0, 50, "YlOrRd", "NASA FIRMS MODIS", "NASA open data"),
}


def png(a, vmin, vmax, cmap, path, alpha=230):
    norm = colors.Normalize(vmin, vmax, clip=True)
    rgba = (matplotlib.colormaps[cmap](norm(np.nan_to_num(a, nan=vmin))) * 255).astype(np.uint8)
    t = norm(np.nan_to_num(a, nan=vmin)).filled(0) if hasattr(norm(a), "filled") else norm(np.nan_to_num(a, nan=vmin))
    rgba[..., 3] = np.where(np.isfinite(a), (120 + (alpha - 120) * np.clip(t, 0, 1) ** 0.5).astype(np.uint8), 0)   # low values let the land show through
    Image.fromarray(rgba).save(path, optimize=True)


def smog():
    man, today = {}, date.today()
    for k, (title, unit, vmin, vmax, cmap, src, lic) in LAYERS.items():
        g = SMOG / "data/grids" / k
        if not g.exists():
            continue
        out = D / "smog" / k
        out.mkdir(parents=True, exist_ok=True)
        months, stack = [], []
        for f in sorted(g.glob("*.npz")):
            a = np.load(f)["mean"].astype("float32")
            a[~np.isfinite(a)] = np.nan
            if k == "fire":
                a[a <= 0] = np.nan
            m = f.stem
            months.append(m); stack.append(a)
            p = out / f"{m}.png"
            y, mo = map(int, m.split("-"))
            if not p.exists() or (today.year * 12 + today.month) - (y * 12 + mo) <= 2 or REDRAW:
                png(a, vmin, vmax, cmap, p)
        ny, nx = stack[0].shape
        lat = N - RES / 2 - RES * np.arange(ny)
        lon = W + RES / 2 + RES * np.arange(nx)
        ds = xr.Dataset(
            {k: (("time", "lat", "lon"), np.stack(stack), {"long_name": title, "units": unit or "1"})},
            coords={"time": [np.datetime64(m + "-01") for m in months],
                    "lat": ("lat", lat, {"units": "degrees_north", "standard_name": "latitude"}),
                    "lon": ("lon", lon, {"units": "degrees_east", "standard_name": "longitude"})},
            attrs={"Conventions": "CF-1.8", "title": f"Monthly {title}, South Asia, 0.1 degree",
                   "institution": "Third Pole open data", "source": src, "license": f"{lic}; derived product CC BY 4.0",
                   "history": f"built {today}", "comment": "Monthly mean of daily means; the latest month may be partial."})
        ds.to_netcdf(out / f"{k}_monthly.nc", encoding={k: {"zlib": True, "complevel": 6, "dtype": "int16", "_FillValue": -32768,
                                                    "scale_factor": (vmax - vmin) / 6000, "add_offset": vmin + (vmax - vmin) / 2}})
        man[k] = {"title": title, "unit": unit, "vmin": vmin, "vmax": vmax, "source": src, "licence": lic,
                  "months": months, "bounds": BOUNDS, "netcdf": f"data/smog/{k}/{k}_monthly.nc",
                  "ramp": [colors.to_hex(matplotlib.colormaps[cmap](x)) for x in np.linspace(0, 1, 9)]}
        print(k, len(months), "months", flush=True)
    (D / "tables").mkdir(exist_ok=True)
    for t in ("city_daily.csv", "city_season_summary.csv", "hotspots_no2.csv", "hotspots_so2.csv", "openaq_daily.csv",
              "openaq_sensors.csv", "power_plants.csv", "punjab_fires_daily.csv", "pm25_estimate_daily.csv"):
        if (SMOG / "outputs" / t).exists():
            shutil.copy(SMOG / "outputs" / t, D / "tables" / t)
    return man


def snow():
    import rasterio
    out = D / "snow"
    out.mkdir(parents=True, exist_ok=True)
    man = {}
    for f in sorted((SNOW / "data").glob("change_*.tif")):
        with rasterio.open(f) as r:
            a = r.read(1).astype("float32"); nod = r.nodata; b = r.bounds
        if nod is not None:
            a[a == nod] = np.nan
        lo, hi = float(np.nanmin(a)), float(np.nanmax(a))
        png(a, lo, hi, "RdBu", out / f"{f.stem}.png")
        shutil.copy(f, out / f.name)
        man[f.stem] = {"title": "Snow cover change, " + f.stem.replace("change_", "").replace("_", " ").title(),
                       "vmin": lo, "vmax": hi, "ramp": [colors.to_hex(matplotlib.colormaps["RdBu"](x)) for x in np.linspace(0, 1, 9)],
                       "bounds": [[b.left, b.top], [b.right, b.top], [b.right, b.bottom], [b.left, b.bottom]],
                       "png": f"data/snow/{f.stem}.png", "tif": f"data/snow/{f.name}"}
    for t in ("atlas_summary.csv", "band_trends.csv", "attribution.csv", "glofas_year.csv"):
        if (SNOW / "outputs" / t).exists():
            shutil.copy(SNOW / "outputs" / t, out / t)
    return man


def stac(man):
    (D / "stac").mkdir(exist_ok=True)
    cat = {"type": "Catalog", "stac_version": "1.0.0", "id": "third-pole", "title": "Third Pole open data",
           "description": "Air quality over South Asia and snow over the Third Pole, from open satellite data. CC BY 4.0.",
           "links": [{"rel": "root", "href": "./catalog.json"}, {"rel": "self", "href": "./catalog.json"}]}
    for k, m in man["smog"].items():
        col = {"type": "Collection", "stac_version": "1.0.0", "id": f"smog-{k}", "title": m["title"],
               "description": f"Monthly {m['title']}, 0.1 degree grid, from {m['source']}.", "license": "CC-BY-4.0",
               "extent": {"spatial": {"bbox": [[W, S, E, N]]},
                          "temporal": {"interval": [[m["months"][0] + "-01T00:00:00Z", m["months"][-1] + "-28T00:00:00Z"]]}},
               "providers": [{"name": m["source"], "roles": ["producer", "licensor"]},
                             {"name": "Third Pole open data", "roles": ["processor", "host"]}],
               "assets": {"netcdf": {"href": f"../{k}.nc".replace(f"../{k}.nc", f"../smog/{k}/{k}_monthly.nc"),
                                     "type": "application/x-netcdf", "roles": ["data"]}},
               "links": [{"rel": "root", "href": "../catalog.json"}, {"rel": "parent", "href": "../catalog.json"}]}
        (D / "stac" / f"smog-{k}.json").write_text(json.dumps(col, indent=1, ensure_ascii=False), encoding="utf-8")
        cat["links"].append({"rel": "child", "href": f"./stac/smog-{k}.json", "title": m["title"]})
    for k, m in man["snow"].items():
        col = {"type": "Collection", "stac_version": "1.0.0", "id": f"snow-{k}", "title": m["title"],
               "description": "Change in snow cover days from MODIS MOD10A1F, from the uib-snow-cover study.", "license": "CC-BY-4.0",
               "extent": {"spatial": {"bbox": [[m["bounds"][0][0], m["bounds"][2][1], m["bounds"][1][0], m["bounds"][0][1]]]},
                          "temporal": {"interval": [["2000-10-01T00:00:00Z", "2025-09-30T00:00:00Z"]]}},
               "assets": {"geotiff": {"href": f"../snow/{k}.tif", "type": "image/tiff; application=geotiff", "roles": ["data"]}},
               "links": [{"rel": "root", "href": "../catalog.json"}, {"rel": "parent", "href": "../catalog.json"}]}
        (D / "stac" / f"snow-{k}.json").write_text(json.dumps(col, indent=1, ensure_ascii=False), encoding="utf-8")
        cat["links"].append({"rel": "child", "href": f"./stac/snow-{k}.json", "title": m["title"]})
    (D / "catalog.json").write_text(json.dumps(cat, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    man = {"built": date.today().isoformat(), "smog": smog(), "snow": snow()}
    stac(man)
    (D / "manifest.json").write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    print("manifest written")


def city_monthly():
    """Monthly city means for the map's city charts (web/data/cities.json)."""
    import pandas as pd
    import sys
    sys.path.insert(0, str(SMOG / "src"))
    import smoglib
    d = pd.read_csv(SMOG / "outputs/city_daily.csv", parse_dates=["date"])
    d["month"] = d.date.dt.strftime("%Y-%m")
    m = d.groupby(["city", "month"])[["no2", "aod", "uvai", "so2", "co", "boundary_layer_height"]].mean().round(3).reset_index()
    out = {c: {"lon": smoglib.CITIES[c][0], "lat": smoglib.CITIES[c][1], "months": g.month.tolist(),
               **{k: [None if pd.isna(v) else v for v in g[k]] for k in ["no2", "aod", "uvai", "so2", "co", "boundary_layer_height"]}}
           for c, g in m.groupby("city")}
    (D / "cities.json").write_text(json.dumps(out), encoding="utf-8")
    print("cities", len(out))


if __name__ == "__main__":
    city_monthly()
