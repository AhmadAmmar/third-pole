"""Programmatic identity: the logo is drawn from data, not by hand.

    python build/build_brand.py

Mark: the Third Pole domain (shared-geodata, balanced contiguous variant) in an azimuthal equal-area projection centred
on the plateau (88 E, 33 N), so the shape is the true shape and areas are honest. Inside it, inward buffers at equal
steps read as contour lines: the plateau as a rising mass, the "pole" of the world's third ice store. A graticule
circle frames it as a polar view. One colour, so it prints, embroiders and stencils.
Outputs web/brand/: mark.svg, mark-mono.svg, logo.svg (mark + wordmark), favicon.svg, PNGs at icon sizes, and social
formats (Instagram post 1080x1080, story 1080x1920, Facebook cover 1640x624, Open Graph 1200x630).
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon

DEV = Path(__file__).resolve().parents[2]
B = Path(__file__).resolve().parents[1] / "web" / "brand"
B.mkdir(parents=True, exist_ok=True)
INK, PAPER, SNOW, RED = "#1d2a33", "#f6f1e7", "#ffffff", "#a8322d"
AEA = "+proj=laea +lon_0=88 +lat_0=33 +datum=WGS84 +units=m"


def mark_paths(size=512, pad=0.10, rings=6):
    g = gpd.read_file(DEV / "shared-geodata/data/third_pole/domain_variants/third_pole_domain_balanced_contiguous.geojson").to_crs(AEA)
    geom = g.union_all().simplify(15000)
    minx, miny, maxx, maxy = geom.bounds
    span = max(maxx - minx, maxy - miny)
    s = size * (1 - 2 * pad) / span
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2

    def path(poly):
        out = []
        polys = [poly] if isinstance(poly, Polygon) else list(getattr(poly, "geoms", []))
        for p in polys:
            if p.is_empty or p.area < (span * 0.01) ** 2:
                continue
            xy = np.asarray(p.exterior.coords)
            pts = [(size / 2 + (x - cx) * s, size / 2 - (y - cy) * s) for x, y in xy]
            out.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z")
        return " ".join(out)
    step = (span / 2) / (rings * 3.2)
    paths = [path(geom.buffer(-i * step).simplify(8000)) for i in range(rings)]
    return [p for p in paths if p]


def mark_svg(size=512, ink=INK, bg=None, accent=RED):
    paths = mark_paths(size)
    r = size * 0.47
    body = [f'<rect width="{size}" height="{size}" fill="{bg}"/>' if bg else ""]
    body.append(f'<circle cx="{size/2}" cy="{size/2}" r="{r:.1f}" fill="none" stroke="{ink}" stroke-width="{size*0.012:.1f}"/>')
    for a in (r * 0.72, r * 0.42):          # graticule: parallels of a polar view
        body.append(f'<circle cx="{size/2}" cy="{size/2}" r="{a:.1f}" fill="none" stroke="{ink}" stroke-width="{size*0.003:.1f}" stroke-dasharray="{size*0.01:.1f} {size*0.012:.1f}" opacity="0.55"/>')
    for i, d in enumerate(paths):
        w = size * (0.010 if i == 0 else 0.005)
        fill = ink if i == len(paths) - 1 else "none"
        body.append(f'<path d="{d}" fill="{fill}" stroke="{ink}" stroke-width="{w:.1f}" stroke-linejoin="round"/>')
    body.append(f'<circle cx="{size/2}" cy="{size*0.032 + size/2 - r:.1f}" r="{size*0.018:.1f}" fill="{accent}"/>')  # north: the pole star
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" aria-label="Third Pole mark">' + "".join(body) + "</svg>"


def logo_svg(ink=INK, bg=None, sub="Open data for the Third Pole and South Asia"):
    m = mark_svg(512, ink, None).split(">", 1)[1].rsplit("</svg>", 1)[0]
    w, h = 1800, 512
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Third Pole">'
            + (f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else "")
            + f'<g>{m}</g>'
            + f'<text x="580" y="290" font-family="EB Garamond, Garamond, Georgia, serif" font-size="196" fill="{ink}" letter-spacing="2">Third Pole</text>'
            + f'<text x="586" y="380" font-family="Source Sans 3, Helvetica, Arial, sans-serif" font-size="46" fill="{ink}" letter-spacing="6">{sub.upper()}</text>'
            + "</svg>")


def social(w, h, title, kicker, name):
    m = mark_svg(512, PAPER, None).split(">", 1)[1].rsplit("</svg>", 1)[0]
    ms = min(w, h) * 0.42
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="{INK}"/>'
            f'<g transform="translate({w*0.07:.0f},{h*0.08:.0f}) scale({ms/512:.3f})">{m}</g>'
            f'<text x="{w*0.07:.0f}" y="{h*0.08 + ms + h*0.09:.0f}" font-family="Source Sans 3, Arial, sans-serif" font-size="{min(w,h)*0.035:.0f}" fill="{PAPER}" letter-spacing="4">{kicker.upper()}</text>'
            f'<text x="{w*0.07:.0f}" y="{h*0.08 + ms + h*0.09 + min(w,h)*0.09:.0f}" font-family="EB Garamond, Georgia, serif" font-size="{min(w,h)*0.075:.0f}" fill="{PAPER}">{title}</text>'
            f'<rect x="{w*0.07:.0f}" y="{h - h*0.07:.0f}" width="{w*0.86:.0f}" height="2" fill="{PAPER}" opacity="0.4"/>'
            f'<text x="{w*0.07:.0f}" y="{h - h*0.035:.0f}" font-family="Source Sans 3, Arial, sans-serif" font-size="{min(w,h)*0.028:.0f}" fill="{PAPER}" opacity="0.8">ahmadammar.github.io/third-pole</text>'
            "</svg>")


def png(svg_path, out, w, h):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(svg_path.resolve().as_uri()); pg.wait_for_timeout(400)
        pg.screenshot(path=str(out), omit_background=True); b.close()


if __name__ == "__main__":
    (B / "mark.svg").write_text(mark_svg(), encoding="utf-8")
    (B / "mark-paper.svg").write_text(mark_svg(512, INK, PAPER), encoding="utf-8")
    (B / "mark-reverse.svg").write_text(mark_svg(512, PAPER, INK), encoding="utf-8")
    (B / "favicon.svg").write_text(mark_svg(64), encoding="utf-8")
    (B / "logo.svg").write_text(logo_svg(), encoding="utf-8")
    (B / "logo-reverse.svg").write_text(logo_svg(PAPER, INK), encoding="utf-8")
    formats = {"instagram-post": (1080, 1080), "instagram-story": (1080, 1920), "facebook-cover": (1640, 624), "og-image": (1200, 630)}
    for name, (w, h) in formats.items():
        (B / f"{name}.svg").write_text(social(w, h, "Who breathes what", "South Asia air, open data", name), encoding="utf-8")
    try:
        for name, (w, h) in {"mark": (512, 512), "mark-paper": (512, 512), "logo": (1800, 512), **formats}.items():
            png(B / f"{name}.svg", B / f"{name}.png", w, h)
        print("pngs done")
    except Exception as e:
        print("png step skipped:", e)
