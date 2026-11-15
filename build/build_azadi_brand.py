"""azadi.asia identity, generated from map data. Shared with the Third Pole Atlas (same projection logic, palette rules).

    python build/build_azadi_brand.py

Three marks, each a real map, each workable in one colour:

A  "world"   The whole Earth in an azimuthal equidistant projection centred on the Third Pole (88 E, 33 N). Every
             straight line from the centre is a true great circle and every ring a true distance: the region is the
             centre the world is seen from, not a periphery. Land from Natural Earth 110 m; rings at 5,000 km; a red
             five-pointed star at the centre.
B  "rivers"  The Third Pole domain drawn as contour rings, and the great rivers that rise on it (Indus, Ganges,
             Yarlung-Brahmaputra, Salween, Mekong, Yangtze, Yellow, Amu Darya, Tarim, Irrawaddy) running out in red,
             in a Lambert azimuthal equal-area projection. Water as a commons that crosses every border.
C  "star"    A five-pointed star filled with inward contour lines at equal steps: a mountain read as a map, a star read
             as a politics. Procedural (no data), so it stays legible at 16 px.

Palette from the azadi.asia theme: ink #0d0d0f, paper #f3eee2, red #a30f20. Wordmark: "AZADI" in spaced capitals and
آزادی in Nastaliq. Outputs in web/brand/azadi/: SVG for every mark (light, reverse, one-colour), lockups, favicon,
and PNGs (512 px marks, lockups, social formats) rendered with the web fonts.
"""
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import unary_union

DEV = Path(__file__).resolve().parents[2]
NE = DEV / "shared-geodata/data/natural_earth"
OUT = Path(__file__).resolve().parents[1] / "web/brand/azadi"
OUT.mkdir(parents=True, exist_ok=True)
INK, PAPER, RED = "#0d0d0f", "#f3eee2", "#a30f20"
LON0, LAT0 = 88, 33
RIVERS = {"Indus", "Ganges", "Brahmaputra", "Yarlung", "Dihang", "Salween", "Nu", "Mekong", "Lancang", "Chang Jiang", "Jinsha",
          "Tongtian", "Huang", "Amu  Darya", "Panj", "Tarim", "Yarkant", "Ayeyarwady", "Sutlej", "Yamuna", "Chenab"}


def d_poly(geom, tx):
    """SVG path data for polygons (all rings) after transform tx(x, y) -> (px, py)."""
    out = []
    polys = [geom] if isinstance(geom, Polygon) else list(getattr(geom, "geoms", []))
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = [tx(x, y) for x, y in ring.coords]
            out.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z")
    return "".join(out)


def d_line(geom, tx):
    lines = [geom] if isinstance(geom, LineString) else list(getattr(geom, "geoms", []))
    return "".join("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in (tx(x, y) for x, y in l.coords)) for l in lines if not l.is_empty)


def star_points(cx, cy, r, inner=0.382, rot=-90):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + i * 36)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def svg(size, body, bg=None, label="azadi.asia mark"):
    w, h = (size, size) if isinstance(size, int) else size
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">'
            + (f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else "") + body + "</svg>")


# A: the world from the Third Pole -------------------------------------------------------------------------------
def mark_world(S=512, ink=INK, red=RED):
    aeqd = f"+proj=aeqd +lon_0={LON0} +lat_0={LAT0} +datum=WGS84 +units=m"
    R = math.pi * 6371008.8                       # distance to the antipode: the edge of the disc
    land = gpd.read_file(NE / "ne_110m_land.geojson")
    # cut a sliver at the antipode meridian so polygons do not wrap across the disc edge
    anti = LON0 - 180
    cut = box(anti - 0.5, -90, anti + 0.5, 90)
    land = land.set_geometry(land.geometry.difference(cut)).explode(index_parts=False)
    land = land.set_geometry(land.geometry.segmentize(1.0)).to_crs(aeqd)
    land = land[land.geometry.is_valid & ~land.geometry.is_empty]
    disc = 0.46 * S
    k = disc / R
    tx = lambda x, y: (S / 2 + x * k, S / 2 - y * k)
    clip = Polygon([(R * 0.999 * math.cos(t), R * 0.999 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 361)])
    geom = unary_union([g.buffer(0) for g in land.geometry]).intersection(clip)
    b = [f'<circle cx="{S/2}" cy="{S/2}" r="{disc:.1f}" fill="none" stroke="{ink}" stroke-width="{S*0.014:.1f}"/>']
    for km in (5000, 10000, 15000):            # true distance rings from the Third Pole
        b.append(f'<circle cx="{S/2}" cy="{S/2}" r="{km*1000*k:.1f}" fill="none" stroke="{ink}" stroke-width="{S*0.003:.1f}" stroke-dasharray="{S*0.008:.1f} {S*0.010:.1f}" opacity="0.6"/>')
    for a in range(0, 360, 30):                 # azimuths: great circles out of the centre
        x, y = math.cos(math.radians(a)), math.sin(math.radians(a))
        b.append(f'<line x1="{S/2 + x*S*0.07:.1f}" y1="{S/2 + y*S*0.07:.1f}" x2="{S/2 + x*disc:.1f}" y2="{S/2 + y*disc:.1f}" stroke="{ink}" stroke-width="{S*0.002:.1f}" opacity="0.45"/>')
    b.append(f'<path d="{d_poly(geom, tx)}" fill="{ink}" fill-rule="evenodd"/>')
    st = star_points(S / 2, S / 2, S * 0.05)
    b.append(f'<path d="M{"L".join(f"{x:.1f},{y:.1f}" for x, y in st)}Z" fill="{red}" stroke="{PAPER}" stroke-width="{S*0.008:.1f}" stroke-linejoin="round"/>')
    return "".join(b)


# B: the rivers of the Third Pole ---------------------------------------------------------------------------------
def mark_rivers(S=512, ink=INK, red=RED, rings=5):
    laea = f"+proj=laea +lon_0={LON0} +lat_0={LAT0} +datum=WGS84 +units=m"
    dom = gpd.read_file(DEV / "shared-geodata/data/third_pole/domain_variants/third_pole_domain_balanced_contiguous.geojson").to_crs(laea)
    dom = dom.union_all().simplify(12000)
    riv = gpd.read_file(NE / "ne_50m_rivers_lake_centerlines.geojson")
    riv = riv[riv.name.isin(RIVERS)].to_crs(laea)
    land = gpd.read_file(NE / "ne_50m_land.geojson").cx[55:125, 0:50].to_crs(laea)
    half = 2_900_000                               # metres from centre to the frame edge
    k = (0.46 * S) / half
    tx = lambda x, y: (S / 2 + x * k, S / 2 - y * k)
    circle = Polygon([(half * math.cos(t), half * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 361)])
    coast = unary_union(list(land.geometry)).intersection(circle).boundary.intersection(circle.buffer(-2000))
    b = [f'<circle cx="{S/2}" cy="{S/2}" r="{0.46*S:.1f}" fill="none" stroke="{ink}" stroke-width="{S*0.014:.1f}"/>',
         f'<path d="{d_line(coast, tx)}" fill="none" stroke="{ink}" stroke-width="{S*0.003:.1f}" opacity="0.55"/>']
    span = math.sqrt(dom.area)
    for i in range(rings):
        g = dom.buffer(-i * span * 0.075).simplify(6000)
        if g.is_empty:
            break
        b.append(f'<path d="{d_poly(g, tx)}" fill="{ink if i == rings - 1 else "none"}" stroke="{ink}" stroke-width="{S*(0.009 if i == 0 else 0.0045):.1f}" stroke-linejoin="round"/>')
    rv = unary_union(list(riv.geometry)).intersection(circle)
    b.append(f'<path d="{d_line(rv, tx)}" fill="none" stroke="{red}" stroke-width="{S*0.0085:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    return "".join(b)


# C: the contour star ---------------------------------------------------------------------------------------------
def mark_star(S=512, ink=INK, red=RED, steps=6):
    st = Polygon(star_points(S / 2, S * 0.53, S * 0.46))
    b = [f'<path d="M{"L".join(f"{x:.1f},{y:.1f}" for x, y in st.exterior.coords)}Z" fill="{red}"/>']
    for i in range(1, steps):
        g = st.buffer(-i * S * 0.022, join_style="mitre", mitre_limit=10)
        if g.is_empty:
            break
        b.append(f'<path d="{d_poly(g, lambda x, y: (x, y))}" fill="none" stroke="{PAPER}" stroke-width="{S*0.007:.1f}" stroke-linejoin="miter"/>')
    return "".join(b)


MARKS = {"world": mark_world, "rivers": mark_rivers, "star": mark_star}


def lockup(mark_body, ink=INK, bg=None, red=RED):
    W, H = 1700, 512
    return svg((W, H), f'<g>{mark_body}</g>'
               f'<text x="570" y="300" font-family="Cormorant Garamond, EB Garamond, Georgia, serif" font-weight="600" font-size="230" letter-spacing="28" fill="{ink}">AZADI</text>'
               f'<text x="1665" y="285" text-anchor="end" font-family="Noto Nastaliq Urdu, serif" font-size="104" fill="{red}">آزادی</text>'
               f'<text x="578" y="395" font-family="&apos;Source Sans 3&apos;, Inter, Arial, sans-serif" font-size="40" letter-spacing="10" fill="{ink}" opacity="0.8">ASIA · THE THIRD POLE · THE WORLD</text>',
               bg, "azadi.asia")


def social(mark_body, w, h, title, kicker):
    u = min(w, h)
    m = u * (0.46 if h >= w else 0.78)
    if h >= w:                                   # square and tall: mark above, text below
        mx, my, tx, ty = (w - m) / 2 if h > w else w * 0.06, h * 0.08, w * 0.06, h * 0.08 + m + h * 0.10
    else:                                        # wide: mark left, text right
        mx, my, tx, ty = w * 0.05, (h - m) / 2, w * 0.05 + m + w * 0.05, h * 0.38
    lines = "".join(f'<text x="{tx:.0f}" y="{ty + u*0.10*(i+1):.0f}" font-family="Cormorant Garamond, Georgia, serif" font-weight="600" '
                    f'font-size="{u*0.085:.0f}" fill="{PAPER}">{t}</text>' for i, t in enumerate(title.split("|")))
    return svg((w, h), f'<g transform="translate({mx:.0f},{my:.0f}) scale({m/512:.3f})">{mark_body}</g>'
               f'<text x="{tx:.0f}" y="{ty:.0f}" font-family="&apos;Source Sans 3&apos;, Arial, sans-serif" font-size="{u*0.034:.0f}" letter-spacing="5" fill="{RED}">{kicker.upper()}</text>'
               + lines +
               f'<text x="{tx:.0f}" y="{h-h*0.05:.0f}" font-family="&apos;Source Sans 3&apos;, Arial, sans-serif" font-size="{u*0.034:.0f}" letter-spacing="4" fill="{PAPER}" opacity="0.8">AZADI.ASIA</text>', INK)


def render_png(svg_file, png_file, w, h):
    from playwright.sync_api import sync_playwright
    html = ('<html><head><link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Noto+Nastaliq+Urdu&family=Source+Sans+3&display=block" rel="stylesheet">'
            f'<style>html,body{{margin:0;background:transparent}}</style></head><body>{svg_file.read_text(encoding="utf-8")}</body></html>')
    tmp = svg_file.with_suffix(".render.html"); tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(tmp.resolve().as_uri()); pg.wait_for_timeout(2500)
        pg.screenshot(path=str(png_file), omit_background=True); b.close()
    tmp.unlink()


if __name__ == "__main__":
    made = []
    for name, fn in MARKS.items():
        variants = {"": (INK, None, RED), "-paper": (INK, PAPER, RED), "-reverse": (PAPER, INK, RED), "-mono": (INK, None, INK)}
        for suf, (ink, bg, red) in variants.items():
            f = OUT / f"azadi-{name}{suf}.svg"
            f.write_text(svg(512, fn(512, ink, red), bg), encoding="utf-8"); made.append((f, 512, 512))
        f = OUT / f"azadi-{name}-lockup.svg"; f.write_text(lockup(fn(512), INK, PAPER), encoding="utf-8"); made.append((f, 1700, 512))
        f = OUT / f"azadi-{name}-lockup-reverse.svg"; f.write_text(lockup(fn(512, PAPER), PAPER, INK), encoding="utf-8"); made.append((f, 1700, 512))
    (OUT / "favicon.svg").write_text(svg(64, mark_star(64)), encoding="utf-8")
    for nm, (w, h) in {"instagram-post": (1080, 1080), "instagram-story": (1080, 1920), "facebook-cover": (1640, 624), "og-image": (1200, 630)}.items():
        f = OUT / f"azadi-{nm}.svg"; f.write_text(social(mark_world(512, PAPER), w, h, "Freedom, seen|from the Third Pole", "Asia · the Third Pole · the world"), encoding="utf-8")
        made.append((f, w, h))
    for f, w, h in made:
        render_png(f, f.with_suffix(".png"), w, h)
    print(len(made), "files rendered to", OUT)
