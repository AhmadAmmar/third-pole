"""azadi.asia social kit, generated from map data: profile mark, Facebook and Instagram formats, post and story templates,
highlight covers.

    python build/build_azadi_social.py            # everything
    python build/build_azadi_social.py posts.json # also render posts written in a JSON file (see TEMPLATE below)

The profile mark keeps the idea of the current avatar (a red South Asia, mountains, a star) and makes it a true map:
- Land from Natural Earth 50 m in a Lambert azimuthal equal-area projection centred on 80 E, 24 N, so South Asia has its
  real shape and area, clipped by a circle 2,700 km in radius (a view of the globe, not a box).
- No national borders: one landmass from Iran to Myanmar, the Pamirs to Sri Lanka ("borderless socialist internationalism").
- The Third Pole (shared-geodata domain) drawn as contour rings in paper colour over the red land; an ink star at its centre.
- Built to survive a 110 px circular crop: one shape, three colours, nothing thinner than 1 % of the width.
Fonts: Cormorant Garamond (headlines), Source Sans 3 (text), Noto Nastaliq Urdu, rendered by Chromium with Google Fonts.
Outputs: web/brand/azadi/social/.
"""
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from build_azadi_brand import DEV, INK, NE, PAPER, RED, d_line, d_poly, render_png, star_points, svg  # noqa: E402

VERSION = sys.argv[sys.argv.index("--version") + 1] if "--version" in sys.argv else "v1"
OUT = Path(__file__).resolve().parents[1] / "web/brand/azadi" / ("social" if VERSION == "v1" else f"social-{VERSION}")
RIVERS_ON = VERSION != "v1"      # v2: the rivers that leave the Third Pole, drawn into every mark
OUT.mkdir(parents=True, exist_ok=True)
LAEA = "+proj=laea +lon_0=80 +lat_0=24 +datum=WGS84 +units=m"
RADIUS = 2_700_000


def _geoms():
    land = gpd.read_file(NE / "ne_50m_land.geojson").cx[30:130, -15:60].to_crs(LAEA)
    disc = Point(0, 0).buffer(RADIUS, 256)
    land = unary_union(list(land.geometry)).intersection(disc).simplify(4000)
    dom = gpd.read_file(DEV / "shared-geodata/data/third_pole/domain_variants/third_pole_domain_balanced_contiguous.geojson").to_crs(LAEA)
    dom = dom.union_all().simplify(15000)
    riv = gpd.read_file(NE / "ne_50m_rivers_lake_centerlines.geojson")
    keep = ("Indus", "Ganges", "Brahmaputra", "Yarlung", "Dihang", "Sutlej", "Chenab", "Yamuna", "Ayeyarwady", "Salween", "Nu",
            "Mekong", "Lancang", "Amu  Darya", "Panj", "Helmand", "Narmada", "Krishna", "Tarim", "Yarkant", "Chang Jiang", "Jinsha", "Tongtian")
    riv = riv[riv.name.isin(keep) | riv.name.fillna("").str.startswith(("God", "Mah"))].to_crs(LAEA)
    rivers = unary_union(list(riv.geometry)).intersection(land).simplify(3000)
    return land, dom, rivers


LAND, DOM, RIVERS = _geoms()


def mark_southasia(S=512, land_col=RED, sea=PAPER, ink=INK, contours=PAPER, ring=True, rings=4):
    k = (0.47 * S) / RADIUS
    tx = lambda x, y: (S / 2 + x * k, S / 2 - y * k + S * 0.02)
    b = [f'<circle cx="{S/2}" cy="{S/2}" r="{0.47*S + S*0.012:.1f}" fill="{sea}"/>' if ring else ""]
    b.append(f'<path d="{d_poly(LAND, tx)}" fill="{land_col}" fill-rule="evenodd"/>')
    span = math.sqrt(DOM.area)
    for i in range(rings):
        g = DOM.buffer(-i * span * 0.09).simplify(8000)
        if g.is_empty:
            break
        w = S * (0.010 if i == 0 else 0.0065)
        col = (ink if contours == PAPER else contours) if RIVERS_ON else contours   # v2: mountains dark, rivers light
        b.append(f'<path d="{d_poly(g, tx)}" fill="none" stroke="{col}" stroke-width="{w:.1f}" stroke-linejoin="round" opacity="{(0.9 if i == 0 else 0.6) if RIVERS_ON else (1 if i == 0 else 0.85)}"/>')
    if RIVERS_ON:   # rivers in paper over the red land: water leaving the mountains, across every border
        b.append(f'<path d="{d_line(RIVERS, tx)}" fill="none" stroke="{sea}" stroke-width="{S*0.0075:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    c = DOM.representative_point()
    cx, cy = tx(c.x, c.y)
    st = star_points(cx, cy, S * 0.06)
    b.append(f'<path d="M{"L".join(f"{x:.1f},{y:.1f}" for x, y in st)}Z" fill="{ink}" stroke="{sea}" stroke-width="{S*0.008:.1f}" stroke-linejoin="round"/>')
    if ring:
        b.append(f'<circle cx="{S/2}" cy="{S/2}" r="{0.47*S + S*0.006:.1f}" fill="none" stroke="{ink}" stroke-width="{S*0.012:.1f}"/>')
    return "".join(b)


def inner(svg_text):
    return svg_text.split(">", 1)[1].rsplit("</svg>", 1)[0]


def fonts_note():
    return "'Cormorant Garamond', 'EB Garamond', Georgia, serif"


SERIF, SANS, URDU = fonts_note(), "'Source Sans 3', Inter, Arial, sans-serif", "'Noto Nastaliq Urdu', serif"


def wrap(text, n):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + ([cur] if cur else [])


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def facebook_cover(w=1640, h=624):
    """Facebook shows 820x312 on desktop and crops the sides to about 640x360 on phones: content sits in the centre
    safe area; the map runs off the right edge as a field, not as content."""
    k = (h * 1.7) / (2 * RADIUS)
    tx = lambda x, y: (w * 1.08 + x * k, h * 0.62 - y * k)
    span = math.sqrt(DOM.area)
    field = [f'<path d="{d_poly(LAND, tx)}" fill="{RED}" opacity="0.85"/>']
    for i in range(6):
        g = DOM.buffer(-i * span * 0.07).simplify(8000)
        if not g.is_empty:
            field.append(f'<path d="{d_poly(g, tx)}" fill="none" stroke="{PAPER}" stroke-width="{2.6 if i == 0 else 1.6}" stroke-linejoin="round"/>')
    if RIVERS_ON:
        field.append(f'<path d="{d_line(RIVERS, tx)}" fill="none" stroke="{PAPER}" stroke-width="2.2" stroke-linecap="round" opacity="0.9"/>')
    graticule = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="{PAPER}" stroke-width="0.6" opacity="0.12"/>' for x in range(0, w, 82))
    m = 230
    body = (graticule + "".join(field) +
            f'<g transform="translate({w*0.5 - 560:.0f},{(h-m)/2:.0f}) scale({m/512:.3f})">{mark_southasia(512)}</g>'
            f'<text x="{w*0.5 - 300:.0f}" y="{h*0.47:.0f}" font-family="{SERIF}" font-weight="600" font-size="112" letter-spacing="14" fill="{PAPER}">AZADI</text>'
            f'<text x="{w*0.5 + 210:.0f}" y="{h*0.47:.0f}" font-family="{URDU}" font-size="60" fill="{PAPER}">آزادی</text>'
            f'<text x="{w*0.5 - 296:.0f}" y="{h*0.47 + 58:.0f}" font-family="{SANS}" font-size="27" letter-spacing="6" fill="{PAPER}" opacity="0.9">SOUTH ASIAN SOCIALIST SOLIDARITIES</text>'
            f'<text x="{w*0.5 - 296:.0f}" y="{h*0.47 + 100:.0f}" font-family="{SANS}" font-size="24" letter-spacing="3" fill="{RED}">AZADI.ASIA</text>')
    return svg((w, h), body, INK, "azadi.asia cover")


def post_card(kicker, headline, deck="", source="", n=1, of=1, w=1080, h=1350, theme="ink"):
    """Instagram 4:5 headline card. Grid crops to 3:4 in the profile view: keep headline inside y 90..1260."""
    bg, fg, acc = (INK, PAPER, RED) if theme == "ink" else (PAPER, INK, RED)
    hl = wrap(headline, 18)[:6]
    dk = wrap(deck, 46)[:6]
    y0 = 300
    t = [f'<g transform="translate({w-620},{h-640}) scale({760/512:.3f})" opacity="0.16">{mark_southasia(512, land_col=acc, sea=bg, contours=bg, ink=fg, ring=False)}</g>',
         f'<rect x="64" y="64" width="{w-128}" height="{h-128}" fill="none" stroke="{fg}" stroke-width="2" opacity="0.35"/>',
         f'<g transform="translate(88,92) scale({90/512:.3f})">{mark_southasia(512, sea=bg if theme == "paper" else PAPER)}</g>',
         f'<text x="196" y="150" font-family="{SANS}" font-size="30" letter-spacing="6" fill="{acc}">{esc(kicker.upper())}</text>']
    t += [f'<text x="96" y="{y0 + 112*i:.0f}" font-family="{SERIF}" font-weight="600" font-size="104" fill="{fg}">{esc(l)}</text>' for i, l in enumerate(hl)]
    yd = y0 + 112 * len(hl) + 40
    t.append(f'<rect x="96" y="{yd - 18}" width="120" height="6" fill="{acc}"/>')
    t += [f'<text x="96" y="{yd + 40 + 44*i:.0f}" font-family="{SANS}" font-size="34" fill="{fg}" opacity="0.92">{esc(l)}</text>' for i, l in enumerate(dk)]
    t.append(f'<text x="96" y="{h-104}" font-family="{SANS}" font-size="24" fill="{fg}" opacity="0.7">{esc(source)}</text>')
    t.append(f'<text x="{w-96}" y="{h-104}" text-anchor="end" font-family="{SANS}" font-size="24" letter-spacing="4" fill="{fg}" opacity="0.85">AZADI.ASIA{f"  ·  {n}/{of}" if of > 1 else ""}</text>')
    return svg((w, h), "".join(t), bg, "azadi.asia post")


def story(kicker, headline, w=1080, h=1920):
    hl = wrap(headline, 18)[:6]
    t = [f'<g transform="translate({(w-560)/2:.0f},250) scale({560/512:.3f})">{mark_southasia(512)}</g>',
         f'<text x="{w/2}" y="960" text-anchor="middle" font-family="{SANS}" font-size="34" letter-spacing="8" fill="{RED}">{esc(kicker.upper())}</text>']
    t += [f'<text x="{w/2}" y="{1070 + 100*i}" text-anchor="middle" font-family="{SERIF}" font-weight="600" font-size="92" fill="{PAPER}">{esc(l)}</text>' for i, l in enumerate(hl)]
    t.append(f'<text x="{w/2}" y="{h-190}" text-anchor="middle" font-family="{SANS}" font-size="30" letter-spacing="6" fill="{PAPER}" opacity="0.8">AZADI.ASIA</text>')
    return svg((w, h), "".join(t), INK, "azadi.asia story")


# highlight covers: one procedural glyph each, on the ink circle the app crops to
def glyph(name, c=PAPER, r=RED):
    s = 1080
    g = {
        "essays": f'<rect x="420" y="360" width="240" height="320" fill="none" stroke="{c}" stroke-width="16"/><line x1="460" y1="440" x2="620" y2="440" stroke="{c}" stroke-width="12"/><line x1="460" y1="500" x2="620" y2="500" stroke="{c}" stroke-width="12"/><line x1="460" y1="560" x2="580" y2="560" stroke="{r}" stroke-width="12"/>',
        "kashmir": f'<path d="M340,700 L470,470 L540,560 L620,420 L760,700 Z" fill="none" stroke="{c}" stroke-width="16" stroke-linejoin="round"/><path d="M590,470 L620,420 L650,470" fill="{r}"/>',
        "labour": f'<circle cx="540" cy="540" r="150" fill="none" stroke="{c}" stroke-width="16"/>' + "".join(f'<rect x="525" y="350" width="30" height="60" fill="{c}" transform="rotate({a} 540 540)"/>' for a in range(0, 360, 45)) + f'<circle cx="540" cy="540" r="50" fill="{r}"/>',
        "climate": "".join(f'<path d="M330,{y} q70,-40 140,0 t140,0 t140,0" fill="none" stroke="{c if i else r}" stroke-width="16"/>' for i, y in enumerate((460, 540, 620))),
        "energy": f'<circle cx="540" cy="540" r="90" fill="{r}"/>' + "".join(f'<line x1="540" y1="380" x2="540" y2="320" stroke="{c}" stroke-width="16" transform="rotate({a} 540 540)"/>' for a in range(0, 360, 45)),
        "air": "".join(f'<circle cx="{x}" cy="{y}" r="{rr}" fill="{c}" opacity="{o}"/>' for x, y, rr, o in ((450, 520, 70, .9), (560, 480, 90, .7), (650, 560, 60, .9), (520, 610, 50, .6))) + f'<circle cx="610" cy="430" r="22" fill="{r}"/>',
        "solidarity": "".join(f'<circle cx="{540 + 150*math.cos(math.radians(a))}" cy="{540 + 150*math.sin(math.radians(a))}" r="46" fill="{c if a % 144 else r}"/>' for a in range(-90, 270, 72)) + f'<circle cx="540" cy="540" r="150" fill="none" stroke="{c}" stroke-width="6" opacity="0.6"/>',
        "maps": f'<g transform="translate(240,240) scale({600/512:.3f})">{mark_southasia(512, sea=INK, contours=INK, ink=PAPER, ring=False)}</g>',
    }[name]
    return svg((s, s), f'<circle cx="540" cy="540" r="540" fill="{INK}"/>{g}', None, f"highlight {name}")


EXAMPLES = [  # layout examples only; replace with each post's own text through posts.json
    {"kicker": "Kashmir", "headline": "Power to the people's committees", "deck": "How the Awami Action Committees grew from the price of flour and electricity into a movement for self-rule.", "source": "Sources: listed in the caption", "theme": "ink"},
    {"kicker": "Labour · Sialkot", "headline": "Who is paid what for a world-cup football", "deck": "Workshop wages against world-market prices, in rupees and dollars.", "source": "Reference rate in the caption", "theme": "paper"},
]

if __name__ == "__main__":
    files = []

    def put(name, text, w, h):
        f = OUT / f"{name}.svg"; f.write_text(text, encoding="utf-8"); files.append((f, w, h))

    put("profile-instagram", svg(1080, f'<g transform="scale({1080/512:.4f})">{mark_southasia(512)}</g>', PAPER, "azadi.asia"), 1080, 1080)
    put("profile-facebook", svg(720, f'<g transform="scale({720/512:.4f})">{mark_southasia(512)}</g>', PAPER, "azadi.asia"), 720, 720)
    put("profile-reverse", svg(1080, f'<g transform="scale({1080/512:.4f})">{mark_southasia(512, sea=INK, contours=INK, ink=PAPER)}</g>', INK, "azadi.asia"), 1080, 1080)
    put("mark-southasia", svg(512, mark_southasia(512, ring=False)), 512, 512)
    put("facebook-cover", facebook_cover(), 1640, 624)
    put("facebook-event-cover", facebook_cover(1920, 1005), 1920, 1005)
    put("story-template", story("South Asian socialist solidarities", "Headline of the story in two lines"), 1080, 1920)
    for i, e in enumerate(EXAMPLES, 1):
        put(f"post-template-{e['theme']}", post_card(e["kicker"], e["headline"], e["deck"], e["source"], theme=e["theme"]), 1080, 1350)
    for g in ("essays", "kashmir", "labour", "climate", "energy", "air", "solidarity", "maps"):
        put(f"highlight-{g}", glyph(g), 1080, 1080)
    args = [a for a in sys.argv[1:] if not a.startswith('--') and a != VERSION]
    if args:      # posts.json: [{"slug": "...", "kicker": "...", "headline": "...", "deck": "...", "source": "...", "theme": "ink"}]
        posts = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        for p in posts:
            put(f"post-{p['slug']}", post_card(p["kicker"], p["headline"], p.get("deck", ""), p.get("source", ""), theme=p.get("theme", "ink")), 1080, 1350)
    for f, w, h in files:
        render_png(f, f.with_suffix(".png"), w, h)
    print(len(files), "rendered to", OUT)
