"""Screenshots for the design journal: python build/shoot.py <out-dir> [url]"""
import sys
from playwright.sync_api import sync_playwright
out, url = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8765/")
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vw, vh, scheme in (("desktop", 1440, 900, "light"), ("desktop-dark", 1440, 900, "dark"), ("phone", 390, 844, "light")):
        pg = b.new_page(viewport={"width": vw, "height": vh}, color_scheme=scheme)
        errs = []; pg.on("console", lambda m: m.type == "error" and errs.append(m.text)); pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url); pg.wait_for_timeout(5000)
        pg.screenshot(path=f"{out}/{name}.png", full_page=(name == "phone"))
        print(name, "errors:", errs[:3])
    b.close()
