// Third Pole Atlas: MapLibre GL, static open data (manifest.json, PNG overlays, CF NetCDF and GeoTIFF downloads, STAC).
const $ = (id) => document.getElementById(id);
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
let M, CITIES, FIRST_LABEL, active = { kind: "smog", key: "no2" }, timer = null;

const map = new maplibregl.Map({
  container: "map",
  style: "https://tiles.openfreemap.org/styles/positron",
  center: [80, 25], zoom: 3.6, minZoom: 2, maxZoom: 10, hash: true,
});
map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");
map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

function graticule() {
  const f = [];
  for (let x = 50; x <= 110; x += 5) f.push({ type: "Feature", properties: { major: x % 10 === 0 }, geometry: { type: "LineString", coordinates: [[x, 0], [x, 45]] } });
  for (let y = 0; y <= 45; y += 5) f.push({ type: "Feature", properties: { major: y % 10 === 0 }, geometry: { type: "LineString", coordinates: [[50, y], [110, y]] } });
  return { type: "FeatureCollection", features: f };
}

const fmtMonth = (m) => { const [y, mo] = m.split("-"); return `${MONTHS[+mo - 1].slice(0, 3)} ${y}`; };

function legend() {
  const L = active.kind === "smog" ? M.smog[active.key] : M.snow[active.key];
  const ticks = [L.vmin, (L.vmin + L.vmax) / 2, L.vmax].map((v) => (Math.abs(v) < 10 ? +v.toFixed(2) : Math.round(v)));
  $("legend").innerHTML = `<div class="t">${L.title}</div><div class="bar" style="background:linear-gradient(90deg,${L.ramp.join(",")})"></div>
    <div class="ticks"><span>${active.kind === "smog" ? "≤ " : ""}${ticks[0]}</span><span>${ticks[1]}</span><span>${active.kind === "smog" ? "≥ " : ""}${ticks[2]}</span></div>
    <div>${L.unit || (active.kind === "snow" ? "change in snow-cover days" : "dimensionless")}</div>`;
}

function info() {
  if (active.kind === "smog") {
    const L = M.smog[active.key];
    $("infoTitle").textContent = L.title;
    $("infoBody").innerHTML = `<dl><dt>Source</dt><dd>${L.source}</dd><dt>Grid</dt><dd>0.1° (about 11 km), EPSG:4326</dd>
      <dt>Period</dt><dd>${fmtMonth(L.months[0])} – ${fmtMonth(L.months.at(-1))}, monthly</dd><dt>Unit</dt><dd>${L.unit || "–"}</dd>
      <dt>Licence</dt><dd>${L.licence}; atlas product CC BY 4.0</dd></dl>
      <a class="dl" href="${L.netcdf}" download>NetCDF, all months</a><a class="dl" href="data/smog/${active.key}/${L.months[$("month").value]}.png" download>Map image</a>
      <a class="dl" href="data/stac/smog-${active.key}.json">STAC metadata</a>
      <p class="note">Columns measure the whole air above the ground, not what people breathe at the surface. See <a href="method.html">Method</a>.</p>`;
  } else {
    const L = M.snow[active.key];
    $("infoTitle").textContent = L.title;
    $("infoBody").innerHTML = `<dl><dt>Source</dt><dd>NASA MODIS MOD10A1F, cloud-gap-filled daily snow</dd><dt>Period</dt><dd>Hydrological years 2001–2025</dd>
      <dt>Licence</dt><dd>NASA open data; atlas product CC BY 4.0</dd></dl>
      <a class="dl" href="${L.tif}" download>GeoTIFF</a><a class="dl" href="data/stac/snow-${active.key}.json">STAC metadata</a><a class="dl" href="data/snow/atlas_summary.csv" download>Range table (CSV)</a>`;
  }
}

function show() {
  ["smog", "snow"].forEach((k) => map.getLayer("ov-" + k) && map.removeLayer("ov-" + k));
  ["smog", "snow"].forEach((k) => map.getSource("ov-" + k) && map.removeSource("ov-" + k));
  let url, bounds;
  if (active.kind === "smog") {
    const L = M.smog[active.key], i = +$("month").value;
    url = `data/smog/${active.key}/${L.months[i]}.png`; bounds = L.bounds;
    $("monthLabel").textContent = fmtMonth(L.months[i]); $("timebar").style.visibility = "visible";
  } else {
    url = M.snow[active.key].png; bounds = M.snow[active.key].bounds; $("timebar").style.visibility = "hidden";
  }
  map.addSource("ov-" + active.kind, { type: "image", url, coordinates: bounds });
  map.addLayer({ id: "ov-" + active.kind, type: "raster", source: "ov-" + active.kind, paint: { "raster-resampling": "nearest", "raster-fade-duration": 0 } }, FIRST_LABEL);
  legend(); info();
}

function select(kind, key) {
  if (kind === "none") {
    ["smog", "snow"].forEach((k) => { map.getLayer("ov-" + k) && map.removeLayer("ov-" + k); map.getSource("ov-" + k) && map.removeSource("ov-" + k); });
    $("legend").style.display = "none"; $("timebar").style.visibility = "hidden"; return;
  }
  $("legend").style.display = "";
  active = { kind, key };
  if (kind === "smog") {
    const n = M.smog[key].months.length; const s = $("month");
    s.max = n - 1; if (+s.value > n - 1 || s.dataset.init !== "1") { s.value = n - 2; s.dataset.init = "1"; }
  } else if (map.getZoom() < 4.5) {
    const b = M.snow[key].bounds; map.fitBounds([b[3], b[1]], { padding: 40 });
  }
  show();
}

function chart(city) {
  const c = CITIES[city], key = active.kind === "smog" && c[active.key] ? active.key : "no2";
  const L = M.smog[key], v = c[key], n = v.length, W = 280, H = 150, p = 26;
  const ys = v.filter((x) => x !== null), lo = Math.min(0, ...ys), hi = Math.max(...ys);
  const X = (i) => p + (i / (n - 1)) * (W - p - 6), Y = (y) => H - 18 - ((y - lo) / (hi - lo || 1)) * (H - 30);
  let d = "", pen = false;
  v.forEach((y, i) => { if (y === null) { pen = false; return; } d += (pen ? "L" : "M") + X(i).toFixed(1) + "," + Y(y).toFixed(1); pen = true; });
  const years = [...new Set(c.months.map((m) => m.slice(0, 4)))];
  const ticks = years.map((y) => { const i = c.months.indexOf(y + "-01"); return i < 0 ? "" : `<line x1="${X(i)}" x2="${X(i)}" y1="${H - 18}" y2="${H - 14}" stroke="currentColor"/><text x="${X(i)}" y="${H - 4}" font-size="9" text-anchor="middle">${y.slice(2)}</text>`; }).join("");
  $("chart").innerHTML = `<h2>${city}</h2><p class="cap">${L.title}, monthly mean over the city (${L.unit || "dimensionless"}).</p>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${L.title} in ${city}, monthly">
      <line x1="${p}" x2="${W - 6}" y1="${H - 18}" y2="${H - 18}" stroke="currentColor" opacity=".4"/>
      <text x="${p - 4}" y="${Y(hi) + 3}" font-size="9" text-anchor="end">${+hi.toFixed(hi < 10 ? 2 : 0)}</text>
      <text x="${p - 4}" y="${Y(lo) + 3}" font-size="9" text-anchor="end">${+lo.toFixed(lo < 10 ? 2 : 0)}</text>
      ${ticks}<path d="${d}" fill="none" stroke="var(--accent)" stroke-width="1.4"/></svg>
    <a class="dl" href="data/tables/city_daily.csv" download>Daily city series (CSV)</a>`;
}

function step(k) {
  const s = $("month"); s.value = Math.min(+s.max, Math.max(0, +s.value + k)); show();
}

map.on("load", async () => {
  FIRST_LABEL = map.getStyle().layers.find((l) => l.type === "symbol").id;
  map.addLayer({ id: "relief", type: "raster", source: "ne2_shaded", paint: { "raster-opacity": 0.35, "raster-saturation": -0.7 } }, map.getStyle().layers[1].id);
  map.addSource("grat", { type: "geojson", data: graticule() });
  map.addLayer({ id: "grat", type: "line", source: "grat", paint: { "line-color": "#7a6f5d", "line-width": ["case", ["get", "major"], 0.6, 0.3], "line-opacity": 0.5 } }, FIRST_LABEL);
  M = await (await fetch("data/manifest.json")).json();
  CITIES = await (await fetch("data/cities.json")).json();
  $("built").textContent = `Last built ${M.built}.`;
  $("air").innerHTML = `<li><label><input type="radio" name="layer" value="none:none"> No overlay</label></li>` + Object.entries(M.smog).map(([k, L]) => `<li><label><input type="radio" name="layer" value="smog:${k}" ${k === "no2" ? "checked" : ""}> ${L.title}</label></li>`).join("");
  $("snow").innerHTML = Object.entries(M.snow).map(([k, L]) => `<li><label><input type="radio" name="layer" value="snow:${k}"> ${L.title.replace("Snow cover change, ", "")}</label></li>`).join("");
  document.querySelectorAll("input[name=layer]").forEach((r) => r.addEventListener("change", (e) => { const [a, b] = e.target.value.split(":"); select(a, b); }));
  const fc = { type: "FeatureCollection", features: Object.entries(CITIES).map(([n, c]) => ({ type: "Feature", properties: { name: n }, geometry: { type: "Point", coordinates: [c.lon, c.lat] } })) };
  map.addSource("cities", { type: "geojson", data: fc });
  map.addLayer({ id: "cities", type: "circle", source: "cities", paint: { "circle-radius": 5, "circle-color": "#f6f1e7", "circle-stroke-color": "#1d2a33", "circle-stroke-width": 1.6 } });
  map.on("click", "cities", (e) => chart(e.features[0].properties.name));
  map.on("mouseenter", "cities", () => (map.getCanvas().style.cursor = "pointer"));
  map.on("mouseleave", "cities", () => (map.getCanvas().style.cursor = ""));
  $("showCities").addEventListener("change", (e) => map.setLayoutProperty("cities", "visibility", e.target.checked ? "visible" : "none"));
  $("month").addEventListener("input", show);
  $("prev").onclick = () => step(-1); $("next").onclick = () => step(1);
  $("play").onclick = () => {
    if (timer) { clearInterval(timer); timer = null; $("play").textContent = "▶"; return; }
    $("play").textContent = "❚❚";
    timer = setInterval(() => { const s = $("month"); s.value = (+s.value + 1) % (+s.max + 1); show(); }, 700);
  };
  const yr = ["interpolate", ["linear"], ["coalesce", ["get", "year"], 2018], 2017, "#d9c9a3", 2020, "#d08c3a", 2024, "#7a2e12"];
  map.addSource("solar", { type: "geojson", data: "data/energy/solar_farms.geojson" });
  map.addLayer({ id: "solar", type: "circle", source: "solar", layout: { visibility: "none" },
    paint: { "circle-color": yr, "circle-stroke-color": "#1d2a33", "circle-stroke-width": 0.5,
             "circle-radius": ["interpolate", ["linear"], ["sqrt", ["get", "area_ha"]], 0, 2, 10, 5, 60, 14] } }, FIRST_LABEL);
  map.addSource("wind", { type: "geojson", data: "data/energy/wind_turbines.geojson" });
  map.addLayer({ id: "wind", type: "circle", source: "wind", layout: { visibility: "none" },
    paint: { "circle-color": "#2f5d73", "circle-radius": ["interpolate", ["linear"], ["zoom"], 3, 1, 9, 3.5], "circle-opacity": 0.8 } }, FIRST_LABEL);
  $("showSolar").addEventListener("change", (e) => map.setLayoutProperty("solar", "visibility", e.target.checked ? "visible" : "none"));
  $("showWind").addEventListener("change", (e) => map.setLayoutProperty("wind", "visibility", e.target.checked ? "visible" : "none"));
  map.on("click", "solar", (e) => { const p = e.features[0].properties;
    new maplibregl.Popup().setLngLat(e.lngLat).setHTML(`<b>Solar farm</b><br>${p.country}<br>${p.area_ha} ha, built ${p.year ?? "before 2018"}<br><small>Global Renewables Watch</small>`).addTo(map); });
  select("smog", "no2");
  chart("Lahore");
});
