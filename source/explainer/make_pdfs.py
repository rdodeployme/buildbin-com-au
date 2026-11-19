"""Spec PDF (print of spec.html) and the drawing captures the explainer uses."""
import asyncio, sys
from playwright.async_api import async_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8766/"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errs = []
        pg = await b.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=2)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(BASE + "spec.html", wait_until="networkidle"); await pg.wait_for_timeout(500)
        for sel, f in [('#dSection', 'ga_section'), ('#dPod', 'ga_bin'), ('#dPlan', 'ga_plan')]:
            el = await pg.query_selector(sel); await el.screenshot(path=f"/home/claude/big/explainer/{f}.png")
        pp = await b.new_page(); pp.on("pageerror", lambda e: errs.append(str(e)))
        await pp.goto(BASE + "spec.html", wait_until="networkidle"); await pp.wait_for_timeout(400)
        await pp.emulate_media(media="print")
        await pp.pdf(path="/home/claude/big/out_spec.pdf", format="A4", landscape=True, print_background=True, prefer_css_page_size=True)
        print("errors:", errs)
        await b.close()
asyncio.run(main())
