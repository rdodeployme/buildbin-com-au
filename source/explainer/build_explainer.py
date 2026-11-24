"""BuildersBins Rev B explainer: easy-to-view landscape PDF with every angle."""
import json, os, asyncio
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "model", "out")
IMG = os.path.join(HERE, "img"); os.makedirs(IMG, exist_ok=True)
model = json.load(open("/home/claude/big-com-au/data/model.json"))
bays = json.load(open("/home/claude/big-com-au/data/bays.json"))["bays"]
S = {s["id"]: s for s in model["streams"]}

def jpg(name, bg=None, crop=None, w=1800):
    im = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
    if bg:
        base = Image.new("RGBA", im.size, bg); base.alpha_composite(im); im = base
    if crop:
        W, H = im.size; im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    im = im.convert("RGB")
    if im.width > w: im = im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
    p = os.path.join(IMG, name + (f"_c" if crop else "") + ".jpg"); im.save(p, quality=84, optimize=True)
    return "img/" + os.path.basename(p)

NIGHT = (14, 17, 20, 255); STEEL = (28, 33, 38, 255)
img = {
    "hero": jpg("hero"), "rear34": jpg("rear34"), "flap": jpg("flap"), "door": jpg("door"),
    "tip": jpg("tip"), "signs": jpg("signs"),
    "plan": jpg("plan", bg=NIGHT, crop=(0.05, 0.2, 0.95, 0.8), w=2000),
    "sideA": jpg("sideA", bg=(236, 239, 241, 255), crop=(0.0, 0.22, 1.0, 0.84), w=2000),
    "sideB": jpg("side", bg=(236, 239, 241, 255), crop=(0.0, 0.22, 1.0, 0.84), w=2000),
    "hookend": jpg("hookend", bg=(236, 239, 241, 255), crop=(0.08, 0.04, 0.92, 0.96)),
    "rearend": jpg("rearend", bg=(236, 239, 241, 255), crop=(0.08, 0.04, 0.92, 0.96)),
}

# plan labels from the Blender bay geometry (plan render: 7.4 m across, centred)
pw, ph = 2400, 1488; pxm = pw / 7.4
labels = ""
for b in bays:
    s = S[b["id"]]; cx = b["x0"] + b["len"] / 2; cy = 0.6 if b["side"] == "A" else -0.6
    left = ((pw / 2 + cx * pxm) / pw - 0.05) / 0.90 * 100; top = ((ph / 2 - cy * pxm) / ph - 0.2) / 0.6 * 100
    labels += f'<div class="pl" style="left:{left:.2f}%;top:{top:.2f}%"><b>{s["n"]:02d}</b><span>{s["name"] if b["len"] > 1 else s["name"].split(" ")[0]}</span></div>'

order = ["timber", "general", "card", "plaster", "plastic", "eps", "rubble", "steel"]
GOES = {"plastic": "Wrap, film, strapping, pipe offcuts", "timber": "Framing offcuts, pallets, formwork", "plaster": "Clean offcuts, broken sheets",
        "card": "Boxes and packaging, flattened", "eps": "White packaging, clean offcuts", "rubble": "Bricks, concrete, tiles, pavers",
        "general": "Mixed offcuts, sweepings", "steel": "Offcuts, mesh, flashing, copper"}
rows = "".join(f'<tr><td class="n">{S[k]["n"]:02d}</td><td><b>{S[k]["name"]}</b><small>{GOES[k]}</small></td><td>{S[k]["side"]}</td><td>{S[k]["fillsPerHome"]:.1f}</td><td style="white-space:nowrap">{S[k]["lengthMm"]:,}</td><td>{S[k]["usableM3"]:.1f} m³</td><td>{S[k]["volume"]:.0f}%</td></tr>' for k in order)
net = model["stationUsableM3"]
tare = sum(s["tareKg"] for s in model["streams"])

LOGO = '<svg class="logo" viewBox="0 0 44 26" aria-hidden="true"><g fill="none" stroke="#C2804F" stroke-width="2"><rect x="1" y="1" width="42" height="24" rx="2.5"/><line x1="1" y1="13" x2="43" y2="13"/><line x1="19.2" y1="1" x2="19.2" y2="13"/><line x1="25.9" y1="1" x2="25.9" y2="13"/><line x1="29.7" y1="1" x2="29.7" y2="13"/><line x1="27.2" y1="13" x2="27.2" y2="25"/><line x1="31.3" y1="13" x2="31.3" y2="25"/><line x1="35.5" y1="13" x2="35.5" y2="25"/></g></svg>'
def foot(n): return f'<footer>{LOGO}<b>Builders<i>Bins</i></b><span>Station Rev B · concept design · 24 November 2026</span><em>{n}</em></footer>'

html = f'''<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><title>BuildersBins station — Rev B explainer</title>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,500..900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
@page {{ size: 297mm 210mm; margin: 0 }}
:root {{ --night:#0E1114; --steel:#14181C; --steel2:#1C2126; --steel3:#2A3036; --text:#EEF1F3; --muted:rgba(238,241,243,.72); --dim:rgba(238,241,243,.5); --line:rgba(238,241,243,.14); --cu:#C2804F; --cu3:#5E3A22; --con:#ECEFF1; --ink:#0E1114 }}
* {{ box-sizing:border-box; margin:0; padding:0 }}
html, body {{ background:var(--night); color:var(--text); font:400 12.5pt/1.45 Inter, sans-serif; -webkit-print-color-adjust:exact; print-color-adjust:exact }}
h1, h2, h3, b.big {{ font-family:Archivo, sans-serif; font-weight:800; letter-spacing:-.01em; line-height:1 }}
.page {{ width:297mm; height:210mm; position:relative; overflow:hidden; page-break-after:always; padding:15mm 16mm 18mm; display:flex; flex-direction:column }}
.page:last-child {{ page-break-after:auto }}
.kick {{ font:600 10.5pt Inter; color:var(--cu); letter-spacing:.06em; text-transform:uppercase; margin-bottom:3mm }}
h2 {{ font-size:30pt; font-stretch:112%; margin-bottom:5mm }}
h3 {{ font-size:15pt; font-stretch:108%; margin-bottom:2mm }}
p {{ color:var(--muted) }} p strong {{ color:var(--text); font-weight:600 }}
footer {{ position:absolute; left:16mm; right:16mm; bottom:7mm; display:flex; align-items:center; gap:3mm; font-size:9pt; color:var(--dim); border-top:1px solid var(--line); padding-top:2.5mm }}
footer .logo {{ width:9mm; height:5.4mm }} footer b {{ font:900 11pt Archivo; font-stretch:118%; color:var(--text) }} footer b i {{ font-style:normal; color:var(--cu) }}
footer em {{ margin-left:auto; font-style:normal; font-weight:600 }}
.fig {{ border-radius:3mm; overflow:hidden; background:var(--steel); position:relative }}
.fig img {{ width:100%; height:100%; object-fit:cover; display:block }}
.cap {{ position:absolute; left:0; right:0; bottom:0; padding:3mm 4mm; background:linear-gradient(transparent, rgba(14,17,20,.92)); font-size:10.5pt; color:var(--text) }}
.cap b {{ color:var(--cu); font-weight:700; margin-right:2mm }}
.light {{ background:var(--con); color:var(--ink) }} .light p {{ color:#3a4148 }} .light footer {{ color:#59626a; border-color:rgba(14,17,20,.14) }} .light footer b {{ color:var(--ink) }}
.light .kick {{ color:var(--cu3) }}
/* cover */
.cover {{ padding:0 }} .cover img.bg {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:50% 60% }}
.cover::after {{ content:""; position:absolute; inset:0; background:linear-gradient(180deg, rgba(14,17,20,.85) 0%, rgba(14,17,20,0) 38%, rgba(14,17,20,0) 62%, rgba(14,17,20,.95) 100%) }}
.cover .top, .cover .stats {{ position:absolute; left:16mm; right:16mm; z-index:2 }}
.cover .top {{ top:14mm }} .cover .brand {{ display:flex; align-items:center; gap:3mm }} .cover .brand .logo {{ width:15mm; height:9mm }}
.cover .brand b {{ font:900 24pt Archivo; font-stretch:118% }} .cover .brand b i {{ font-style:normal; color:var(--cu) }}
.cover h1 {{ font-size:46pt; font-stretch:120%; margin-top:6mm; letter-spacing:-.03em }} .cover h1 span {{ color:var(--cu) }}
.cover .byline {{ margin-top:5mm; font:800 18pt Archivo; font-stretch:112% }} .cover .byline span {{ color:var(--cu) }}
.cover .sub {{ margin-top:3mm; font-size:14pt; color:var(--muted); max-width:150mm }}
.cover .stats {{ bottom:12mm; display:grid; grid-template-columns:repeat(4, 1fr); gap:6mm }}
.stat b {{ display:block; font:800 22pt/1 Archivo; font-stretch:112%; color:var(--text) }} .stat span {{ font-size:10.5pt; color:var(--muted) }}
/* grids */
.row {{ display:grid; gap:6mm; flex:1; min-height:0 }}
.c2 {{ grid-template-columns:1fr 1fr }} .c3 {{ grid-template-columns:1fr 1fr 1fr }} .c4 {{ grid-template-columns:repeat(4, 1fr) }}
.r2 {{ grid-template-rows:1fr 1fr }}
.steps .fig {{ height:86mm }} .step h3 {{ margin-top:4mm }} .step h3 span {{ color:var(--cu); margin-right:2mm }} .step p {{ font-size:11pt }}
.pl {{ position:absolute; transform:translate(-50%, -50%); text-align:center; background:rgba(14,17,20,.82); border-radius:2mm; padding:1.2mm 2.4mm; white-space:nowrap }}
.pl b {{ display:block; font:800 15pt/1 Archivo; color:var(--cu) }} .pl span {{ font-size:8.5pt; font-weight:600 }}
.elev {{ background:var(--con); border-radius:3mm; overflow:hidden; position:relative }} .elev img {{ width:100%; display:block }}
.elev .tag {{ position:absolute; top:3mm; left:4mm; font:700 10pt Inter; color:var(--ink); letter-spacing:.04em; text-transform:uppercase }}
.notes {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:5mm; margin-top:5mm }} .notes div {{ border-top:2px solid var(--cu); padding-top:2mm; font-size:10.5pt }} .notes b {{ display:block; font:800 13pt Archivo; margin-bottom:1mm }}
table {{ width:100%; border-collapse:collapse; font-size:10pt }} th {{ text-align:left; font:700 8.5pt Inter; letter-spacing:.05em; text-transform:uppercase; color:#59626a; padding:2mm; border-bottom:2px solid var(--ink) }}
td {{ padding:1.3mm 2mm; border-bottom:1px solid rgba(14,17,20,.12); vertical-align:top }} td.n {{ font:800 14pt Archivo; color:var(--cu3) }} td small {{ display:block; color:#59626a; font-size:9pt }}
.card {{ background:#fff; border-radius:3mm; padding:4mm; display:flex; align-items:center; justify-content:center }} .card img {{ max-width:100%; max-height:100%; display:block }}
.big2 {{ font:800 34pt/1 Archivo; font-stretch:112% }} .big2 small {{ font:600 11pt Inter; color:#59626a; display:block; margin-top:1mm }}
ul.ticks {{ list-style:none }} ul.ticks li {{ padding:2.4mm 0 2.4mm 7mm; border-top:1px solid var(--line); position:relative; color:var(--muted) }} ul.ticks li::before {{ content:""; position:absolute; left:0; top:4.1mm; width:3mm; height:3mm; background:var(--cu); border-radius:1px }}
ul.ticks li b {{ color:var(--text) }}
.pill {{ display:inline-block; background:var(--cu); color:var(--ink); font:700 9.5pt Inter; padding:1mm 2.5mm; border-radius:5mm; margin-right:2mm }}
</style></head><body>

<section class="page cover">
  <img class="bg" src="{img['hero']}" alt="">
  <div class="top">
    <div class="brand">{LOGO}<b>Builders<i>Bins</i></b></div>
    <p class="byline"><span>B</span>uild. <span>I</span>nnovate. <span>G</span>ain.</p>
    <h1>The station, <span>Rev B.</span></h1>
    <p class="sub">Eight lidded steel bins on one hook-lift skid. Every material sorted on site, emptied by forklift without opening a lid.</p>
  </div>
  <div class="stats">
    <div class="stat"><b>6 × 2.45 m</b><span>footprint, 2.5 m high max</span></div>
    <div class="stat"><b>8 bins</b><span>4 a side, sized by the data</span></div>
    <div class="stat"><b>~{net:.0f} m³</b><span>sorted, per change-over</span></div>
    <div class="stat"><b>4 mm steel</b><span>every side, lid, flap and door</span></div>
  </div>
</section>

<section class="page">
  <p class="kick">What it is</p>
  <h2>One skid. Eight bins. Nothing mixed.</h2>
  <div class="row" style="grid-template-columns:92mm 1fr;align-items:center">
    <div>
      <p style="font-size:13pt">A low hook-lift skid drops on the lot at slab and stays until handover. It carries <strong>eight separate steel bins, four a side</strong>, one for each material a new home throws out.</p>
      <p style="margin-top:4mm">Each bin is sized by how much <strong>space</strong> its material takes up, not its weight. General rubbish and timber get the biggest bins, plastics and plasterboard 1,230, and cardboard, bricks, steel and polystyrene 1,000.</p>
      <ul class="ticks" style="margin-top:6mm">
        <li><b>Roof peaks in the middle</b> with a copper ridge line, sloping down and away so rain runs straight off</li>
        <li><b>Drop-down front flap</b> from 1.2 m to a 2 m dump height</li>
        <li><b>Trap door</b> on the right side for emptying</li>
        <li><b>Fork pockets</b> framed in copper, so it's obvious where the forks go</li>
      </ul>
    </div>
    <div class="fig" style="background:var(--night);aspect-ratio:2160/893"><img src="{img['plan']}" style="object-fit:fill" alt="Plan from above, lids off">{labels}</div>
  </div>
  <p style="margin-top:-6mm;margin-left:98mm;font-size:10pt;color:var(--dim)"><b style="color:var(--cu)">From above, lids off.</b> Side A at the top, side B below, hook end on the right.</p>
  {foot(2)}
</section>

<section class="page">
  <p class="kick">How it works</p>
  <h2>Drop it, load it, lock it, empty it.</h2>
  <div class="row c4 steps" style="flex:none">
    <div class="step"><div class="fig"><img src="{img['hero']}" style="object-position:55% 55%" alt=""></div><h3><span>1</span>Drop it on the lot</h3><p>A hook-lift truck sets the skid down at slab. One footprint for every stream, all build long.</p></div>
    <div class="step"><div class="fig"><img src="{img['flap']}" alt=""></div><h3><span>2</span>Load it</h3><p>Each trade drops the flap on the right bin and loads it. The flap sits level as a ledge for sheets.</p></div>
    <div class="step"><div class="fig"><img src="{img['signs']}" style="object-position:70% 50%" alt=""></div><h3><span>3</span>Lock it</h3><p>Big numbered signs say what goes in. One tap on a phone locks all eight; an alarm and lights cover after hours.</p></div>
    <div class="step"><div class="fig"><img src="{img['tip']}" alt=""></div><h3><span>4</span>Empty it</h3><p>At the facility a forklift lifts each bin off and tips it right. The trap door opens and the load slides out.</p></div>
  </div>
  <p style="margin-top:7mm;font-size:13pt;max-width:230mm">Every bin is weighed as it's emptied, so the builder gets a real recycling figure by material for every home, not a guess.</p>
  {foot(3)}
</section>

<section class="page">
  <p class="kick">Every angle</p>
  <h2>Front, back and both ends.</h2>
  <div class="row c2 r2" style="gap:5mm">
    <div class="fig"><img src="{img['hero']}" alt=""><div class="cap"><b>Front quarter</b>Side B with flaps down, hook end on the right</div></div>
    <div class="fig"><img src="{img['rear34']}" alt=""><div class="cap"><b>Rear quarter</b>Side A and the rear post with its light and sign</div></div>
    <div class="fig" style="background:var(--con)"><img src="{img['hookend']}" style="object-fit:contain" alt=""><div class="cap"><b>Hook end</b>Hook frame, sensor lights, lock and alarm controller, siren</div></div>
    <div class="fig" style="background:var(--con)"><img src="{img['rearend']}" style="object-fit:contain" alt=""><div class="cap"><b>Rear end</b>Rollers, rear post, light and sign. Roof peaks in the middle</div></div>
  </div>
  {foot(4)}
</section>

<section class="page light">
  <p class="kick">Both sides</p>
  <h2>What each trade sees.</h2>
  <div style="display:grid;gap:4mm;flex:1;min-height:0;grid-template-rows:1fr 1fr">
    <div class="elev"><img src="{img['sideA']}" alt=""><span class="tag">Side A · general, plastics, polystyrene, cardboard</span></div>
    <div class="elev"><img src="{img['sideB']}" alt=""><span class="tag">Side B · timber, bricks, steel, plasterboard</span></div>
  </div>
  {foot(5)}
</section>

<section class="page">
  <p class="kick">Loading</p>
  <h2>Signed so nobody has to guess.</h2>
  <div class="row c2">
    <div class="fig"><img src="{img['flap']}" alt=""><div class="cap"><b>Drop-down flap</b>Hinged at 1.2 m, closes at 2 m under a fixed panel, sits level as a loading ledge</div></div>
    <div class="fig"><img src="{img['signs']}" alt=""><div class="cap"><b>Sign plates</b>Number, material, what goes in and what stays out</div></div>
  </div>
  <div class="notes">
    <div><b>Big numbers</b>Every bin is numbered 01 to 08 on its sign and on its flap.</div>
    <div><b>Yes and no</b>Each plate lists what goes in and what doesn't.</div>
    <div><b>Easy reach</b>Flaps open from 1.2 m to 2 m. Nothing lifted above 2 m, no steps, no climbing.</div>
    <div><b>No hazardous waste</b>No asbestos, chemicals or gas bottles, signed on the skid.</div>
  </div>
  {foot(6)}
</section>

<section class="page">
  <p class="kick">Emptying</p>
  <h2>The lid never comes off.</h2>
  <div class="row" style="grid-template-columns:1.25fr 1fr">
    <div class="fig"><img src="{img['tip']}" alt=""><div class="cap"><b>Tipped to empty</b>Forklift with a rotator turns the bin to its right; the load slides onto its own pile</div></div>
    <div style="display:grid;grid-template-rows:1fr auto;gap:5mm;min-height:0">
      <div class="fig"><img src="{img['door']}" alt=""><div class="cap"><b>Trap door</b>Right-hand side, hinged along the top, latched at the bottom</div></div>
      <ul class="ticks">
        <li><b>1.</b> Forks go into the two copper-framed tunnels near the floor, clear over the skid's 100 mm rail.</li>
        <li><b>2.</b> Lift, weigh, and turn the bin to the right.</li>
        <li><b>3.</b> Trap door swings open, load slides out, bin goes back.</li>
      </ul>
    </div>
  </div>
  {foot(7)}
</section>

<section class="page">
  <p class="kick">Security</p>
  <h2>Locked, lit and alarmed.</h2>
  <div class="row" style="grid-template-columns:1fr 1fr">
    <div class="fig" style="background:var(--con)"><img src="{img['hookend']}" style="object-fit:contain" alt=""><div class="cap"><b>Hook end</b>Lights on the arm, controller and siren on the frame</div></div>
    <div>
      <ul class="ticks">
        <li><b>One tap, eight locks.</b> A battery smart lock on every flap. The supervisor locks or unlocks the lot from a phone over Bluetooth.</li>
        <li><b>Every opening logged.</b> Shows who loaded what, and when, if a bin gets contaminated.</li>
        <li><b>Three sensor lights.</b> Two raking along each side from the hook end, one on the rear post. On with movement after dark.</li>
        <li><b>Scheduled alarm.</b> Arms itself for the hours you set, say 6 pm to 6 am and weekends. A forced flap sets off the siren and flashes the lights.</li>
        <li><b>Keyed override</b> for a flat phone or battery. Off-site alerts need a 4G add-on.</li>
      </ul>
    </div>
  </div>
  {foot(8)}
</section>

<section class="page light">
  <p class="kick">The numbers</p>
  <h2>Sized by what a new home throws out.</h2>
  <div class="row" style="grid-template-columns:1.35fr 1fr">
    <div>
      <table><thead><tr><th>Bin</th><th>Material and what goes in</th><th>Side</th><th>Fills per home</th><th>Width mm</th><th>Holds</th><th>Of the space</th></tr></thead><tbody>{rows}</tbody></table>
      <p style="margin-top:2mm;font-size:9pt">No bin is narrower than 1,000 mm. Usable space counts each bin full at 2.15 m. Volumes are estimates from published studies until pilot weighbridge data replaces them.</p>
    </div>
    <div style="display:grid;grid-template-rows:auto 1fr;gap:5mm;min-height:0">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:4mm">
        <div class="big2">{net:.1f} m³<small>sorted per change-over</small></div>
        <div class="big2">{model["changeovers"]:.1f}<small>change-overs for a typical 240 m² home</small></div>
      </div>
      <div class="card"><img src="ga_section.png" alt="Section across the skid with key heights"></div>
    </div>
  </div>
  {foot(9)}
</section>

<section class="page light">
  <p class="kick">Key dimensions</p>
  <h2>The bin, front and side.</h2>
  <div class="row" style="grid-template-columns:1.9fr 1fr">
    <div class="card"><img src="ga_bin.png" alt="Typical bin front and right side with dimensions"></div>
    <div>
      <table><tbody>
        <tr><td><b>Overall</b></td><td>6,000 × 2,450, max 2,500 high</td></tr>
        <tr><td><b>Bin depth</b></td><td>1,150</td></tr>
        <tr><td><b>Bin widths</b></td><td>1,000 to 2,470 (1,000 / 1,230 / 2,010 / 2,470)</td></tr>
        <tr><td><b>Roof</b></td><td>2,500 ridge in the middle, 2,400 at the front</td></tr>
        <tr><td><b>Flap</b></td><td>Hinged at 1,200, opening to 2,000 (dump height)</td></tr>
        <tr><td><b>Fork pockets</b></td><td>200 above the bin base</td></tr>
        <tr><td><b>Skid rail</b></td><td>100 high, edges and centre</td></tr>
        <tr><td><b>Trap door</b></td><td>About 1,030 × 1,900, top-hinged</td></tr>
        <tr><td><b>Steel</b></td><td>4 mm plate throughout</td></tr>
        <tr><td><b>Bins tare</b></td><td>About {tare/1000:.1f} t for eight (steel, from the CAD)</td></tr>
      </tbody></table>
      <p style="margin-top:3mm;font-size:9.5pt">Millimetres. Heights from the ground with bins on the skid. Full drawings and schedule in the fabricator spec.</p>
    </div>
  </div>
  {foot(10)}
</section>

<section class="page">
  <p class="kick">Next</p>
  <h2>What the fabricator confirms.</h2>
  <div class="row c2">
    <ul class="ticks">
      <li><b>Hook trucks.</b> Hook height, runner spacing and rollers, and that a 100 mm deck works on our fleet.</li>
      <li><b>Narrow, tall bins.</b> The 1,000 mm bins are 2.4 m tall: check them on forks and when tipping. The rubble bin needs a fill line at its rated load.</li>
      <li><b>Weight.</b> Real tare of the skid and each bin against the truck's hook-lift rating.</li>
      <li><b>Hardware.</b> Locks, lights, siren and the 4G option, priced.</li>
      <li><b>Sign-off.</b> Structural engineer certifies the skid, pockets and trap door latches.</li>
    </ul>
    <div>
      <p style="font-size:13pt"><strong>Ask for:</strong> shop drawings, tare weights, a price for 1, 10 and 50 stations plus spare bins, and lead times for a prototype and a pilot run.</p>
      <p style="margin-top:6mm"><span class="pill">Live spec</span>rdodeployme.github.io/buildbin-com-au/spec.html</p>
      <p style="margin-top:3mm"><span class="pill">Site</span>rdodeployme.github.io/buildbin-com-au</p>
      <div class="fig" style="height:62mm;margin-top:6mm"><img src="{img['rear34']}" alt=""></div>
      <p style="margin-top:4mm;font-size:10pt;color:var(--dim)">Concept design. Renders from the Blender model. Figures are estimates until a prototype is built and weighed. BuildersBins is a Recycle Group initiative.</p>
    </div>
  </div>
  {foot(11)}
</section>
</body></html>'''
open(os.path.join(HERE, "explainer.html"), "w").write(html)

async def pdf():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1123, "height": 794})
        await pg.goto("file://" + os.path.join(HERE, "explainer.html"), wait_until="networkidle"); await pg.wait_for_timeout(800)
        await pg.pdf(path=os.path.join(HERE, "BuildersBins-station-explainer.pdf"), width="297mm", height="210mm", print_background=True, prefer_css_page_size=True)
        await b.close()
asyncio.run(pdf())
print("ok")
