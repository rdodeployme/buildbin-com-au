"""Flat patterns (laser-cut profiles) and cut lists for BuildersBins Rev B. mm."""
import math, os
import ezdxf
from params import *


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


class Flat:
    def __init__(self, code, name, t, qty, outline, holes=(), circles=(), bends=(), note="", mat="Gr 250/300 plate"):
        self.code, self.name, self.t, self.qty = code, name, t, qty
        self.outline, self.holes, self.circles, self.bends = outline, list(holes), list(circles), list(bends)
        self.note, self.mat = note, mat

    @staticmethod
    def _area(p):
        return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2

    def area(self):
        a = self._area(self.outline) - sum(self._area(h) for h in self.holes)
        return a - sum(math.pi * r * r for _c, r in self.circles)

    def mass(self):
        return self.area() * self.t * STEEL

    def bbox(self):
        xs = [p[0] for p in self.outline]; ys = [p[1] for p in self.outline]
        return min(xs), min(ys), max(xs), max(ys)

    def size(self):
        x0, y0, x1, y1 = self.bbox()
        return x1 - x0, y1 - y0


class Section:
    def __init__(self, code, name, sect, length, qty, kgm, note=""):
        self.code, self.name, self.sect, self.length, self.qty, self.kgm, self.note = code, name, sect, length, qty, kgm, note

    def mass(self):
        return self.kgm * self.length / 1000


def kgm_rhs(b, h, t):
    return (b * h - (b - 2 * t) * (h - 2 * t)) * STEEL * 1000


def lid_len():
    oh, _ = DRIP
    return (D + oh) * math.hypot(1, (HB - HF) / D)


def bin_flats(n):
    w = width(n)
    pcs = pocket_centres(w)
    zt0, ztD = HF - T, HB - T
    pw = w - 2 * T
    holes = [rect(cx - T - 100, POCKET_Z, cx - T + 100, POCKET_Z + 100) for cx in pcs]
    F = []
    tag = f"BIN-{n}M"
    F.append(Flat(f"{tag}-01", "Front plate", 4, 1, rect(0, 0, pw, FB), holes,
                  note="Pocket mouths 200 x 100. Copper frames weld over."))
    F.append(Flat(f"{tag}-02", "Back plate", 4, 1, rect(0, 0, pw, ztD), holes,
                  note="Top edge under the lid. Pocket mouths 200 x 100."))
    j = 35 - T
    side = [(-j, FB), (0, FB), (0, 0), (D, 0), (D, ztD), (0, zt0), (-j, zt0)]
    F.append(Flat(f"{tag}-03", "Side plate, left (outside face, front edge at left)", 4, 1, side,
                  bends=[((0, FB), (0, zt0), "BEND 90° IN — flap jamb")]))
    sideR = [(D - x, y) for x, y in side][::-1]
    y0, y1, z0, z1 = DOOR_OPEN
    F.append(Flat(f"{tag}-04", "Side plate, right (outside face, front edge at right)", 4, 1, sideR,
                  holes=[rect(D - y1, z0, D - y0, z1)],
                  bends=[((D, FB), (D, zt0), "BEND 90° IN — flap jamb")],
                  note=f"Trap door opening {y1 - y0:.0f} x {z1 - z0:.0f}."))
    F.append(Flat(f"{tag}-05", "Floor plate", 4, 1, rect(0, 0, pw, D - 2 * T), circles=[((pw - 60, 60), 20)],
                  note="Drain hole 40 dia at the front right corner, plug by others."))
    ll, dr = lid_len(), DRIP[1]
    F.append(Flat(f"{tag}-06", "Lid", 4, 1, rect(0, 0, w, ll + dr),
                  bends=[((0, dr), (w, dr), "BEND 85° DOWN — drip edge")],
                  note="Back edge (top of sheet) at the ridge. Falls 100 to the front. Copper ridge stripe painted."))
    a, h, f = w - 72, (zt0 - 30) - FB, 25
    flap = [(-f, 0), (a + f, 0), (a + f, h), (a, h), (a, h + f), (0, h + f), (0, h), (-f, h)]
    F.append(Flat(f"{tag}-07", "Front flap", 4, 1, flap,
                  bends=[((0, 0), (0, h), "BEND 90° IN"), ((a, 0), (a, h), "BEND 90° IN"), ((0, h), (a, h), "BEND 90° IN")],
                  note="Bottom edge hinged at 1,100 above the bin base."))
    dy0, dy1, dz0, dz1 = DOOR
    F.append(Flat(f"{tag}-08", "Trap door leaf", 4, 1, rect(0, 0, dy1 - dy0, dz1 - dz0),
                  note="Top edge hinged. 20 lap all round the opening."))
    L6 = D - 2 * T
    F.append(Flat(f"{tag}-09", "Fork pocket, top and bottom", 6, 4, rect(0, 0, 212, L6)))
    F.append(Flat(f"{tag}-10", "Fork pocket, web", 6, 4, rect(0, 0, 100, L6), note="Box internal 200 x 100."))
    F.append(Flat(f"{tag}-11", "Pocket mouth frame (copper)", 6, 4, rect(0, 0, 250, 150), holes=[rect(25, 25, 225, 125)],
                  note="Two per pocket, front and back face."))
    S = [
        Section(f"{tag}-12", "Base runner", "RHS 75 x 50 x 4", L6, 2, kgm_rhs(75, 50, 4), "On edge, inside each side wall."),
        Section(f"{tag}-13", "Door stiffener", "RHS 50 x 25 x 3", (z1 - z0) - 80, 2, kgm_rhs(50, 25, 3), "Inside face of door, within the opening."),
    ]
    return F, S


def bin_hardware(n):
    w = width(n)
    return [
        ("Flap hinge, heavy weld-on barrel", 2, "Bottom edge of flap"),
        ("Flap check chain or stay, with clip", 2, "Holds flap level as a ledge"),
        ("Trap door hinge, continuous, 1,030 long", 1, "Top edge of door, low profile"),
        ("Over-centre latch with safety pin, low profile", 2, "Bottom edge of door, inside the 10 mm buffer zone"),
        ("Bluetooth smart latch (flap)", 1, "By others, to confirm"),
        ("Rubber buffer strip 10 x 40 x 1,300", 4, "Bonded and bolted, 2 per side wall"),
        ("Drain plug 40", 1, "Floor"),
        (f"Sign plate, ACM, {w - 80:.0f} x 840", 1, "Lower front"),
    ]


def skid_flats():
    hy = W / 2
    holes = []
    for k in range(NMOD):
        xc = X0 + (k + 0.5) * MOD
        for yc in (hy - RAIL[0] - 40, -hy + RAIL[0] + 40, RAIL[0] / 2 + 40, -RAIL[0] / 2 - 40):
            holes.append(((xc, yc + hy), 15))
    F = [
        Flat("SKID-01", "Deck plate", 10, 1, rect(0, 0, L, W), circles=holes,
             note="Drain holes 30 dia. Over standard plate size: join over a cross-member, full-penetration butt weld."),
        Flat("SKID-02", "Stop end cap", 6, 4, rect(0, 0, 50, 100)),
        Flat("SKID-03", "Roller bracket", 12, 4, rect(0, 0, 145, 69), circles=[((70, 50 - 20 + 0), 13)],
             note="Axle hole to suit roller."),
        Flat("SKID-04", "Hook bar gusset", 20, 2, rect(0, 0, 90, 140), circles=[((65, 70), 26)],
             note="Hook bar 50 dia passes through."),
    ]
    span_out = hy - (RUNNER_Y + SHS / 2)
    span_mid = 2 * RUNNER_Y - SHS
    px = 6160.5
    brace = math.hypot(px - (XH + 50), 1100 - (DECK + 100))
    S = [
        Section("SKID-05", "Runner", "SHS 89 x 89 x 6", L - 150, 2, kgm_rhs(89, 89, 6), "Centres ±550, to suit hook system"),
        Section("SKID-06", "Cross member, outer", "SHS 89 x 89 x 5", span_out, 20, kgm_rhs(89, 89, 5), "10 positions"),
        Section("SKID-07", "Cross member, between runners", "SHS 89 x 89 x 5", span_mid, 10, kgm_rhs(89, 89, 5), "10 positions"),
        Section("SKID-08", "Kerb rail (outer and centre)", "RHS 100 x 50 x 6", XH - X0, 3, kgm_rhs(100, 50, 6),
                "Stood 100 high, 6 CFW both sides"),
        Section("SKID-09", "Rear stop and hook-end stop", "RHS 100 x 50 x 6", W, 2, kgm_rhs(100, 50, 6), "Full width, rails butt into them"),
        Section("SKID-10", "Hook post", "SHS 89 x 89 x 6", 1500 - DECK, 2, kgm_rhs(89, 89, 6), "At y ±450"),
        Section("SKID-11", "Hook cross beam", "SHS 89 x 89 x 5", 900 + SHS, 1, kgm_rhs(89, 89, 5), "Top of posts"),
        Section("SKID-12", "Hook brace", "SHS 89 x 89 x 5", brace, 2, kgm_rhs(89, 89, 5), "Cut ends to suit"),
        Section("SKID-13", "Hook bar", "Round bar 50 dia", 700, 1, math.pi * 25 ** 2 * STEEL * 1000, "Centre 1,450 above ground, to suit fleet"),
        Section("SKID-14", "Light mast", "SHS 50 x 50 x 3", 1950 - 1589, 1, kgm_rhs(50, 50, 3), "Top 1,950"),
        Section("SKID-15", "Rear light post", "SHS 50 x 50 x 3", 1950 - DECK, 1, kgm_rhs(50, 50, 3), "Top 1,950"),
    ]
    return F, S


def skid_hardware():
    return [
        ("Rear roller 140 dia x 200, with axle and bearings", 2, "To suit hook-lift system"),
        ("LED sensor floodlight", 3, "Two on the mast, one on the rear post"),
        ("Controller, battery, siren, keyed override (IP-rated box)", 1, "On the hook frame, by others"),
    ]


# ------------------------------------------------------------------ DXF
def write_dxf(f, path):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    for nm, col in (("CUT", 7), ("BEND", 1), ("TEXT", 3)):
        doc.layers.add(nm, color=col)
    doc.layers.get("BEND").dxf.linetype = "DASHED"
    m = doc.modelspace()
    m.add_lwpolyline(f.outline, close=True, dxfattribs={"layer": "CUT"})
    for h in f.holes:
        m.add_lwpolyline(h, close=True, dxfattribs={"layer": "CUT"})
    for c, r in f.circles:
        m.add_circle(c, r, dxfattribs={"layer": "CUT"})
    for a, b, lab in f.bends:
        m.add_line(a, b, dxfattribs={"layer": "BEND", "linetype": "DASHED"})
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        vert = abs(a[0] - b[0]) < 1
        m.add_text(lab, height=18, rotation=90 if vert else 0,
                   dxfattribs={"layer": "TEXT"}).set_placement((mx - 8 if vert else mx, my if vert else my + 8))
    x0, y0, x1, y1 = f.bbox()
    m.add_text(f"{f.code}  {f.name}", height=30, dxfattribs={"layer": "TEXT"}).set_placement((x0, y0 - 60))
    m.add_text(f"{f.t} mm {f.mat}   QTY {f.qty} per item   {x1 - x0:.0f} x {y1 - y0:.0f}   bends: apply own deductions",
               height=20, dxfattribs={"layer": "TEXT"}).set_placement((x0, y0 - 95))
    doc.saveas(path)


def write_all(out="/home/claude/big/fab/out/DXF"):
    files = []
    groups = [(f"BIN-{n}M", bin_flats(n)[0]) for n in SIZES] + [("SKID", skid_flats()[0])]
    for g, flats in groups:
        os.makedirs(f"{out}/{g}", exist_ok=True)
        for f in flats:
            nm = f"{f.code}_{f.name.split(' (')[0].replace(',', '').replace(' ', '-')}_{f.t}mm_x{f.qty}.dxf"
            write_dxf(f, f"{out}/{g}/{nm}")
            files.append(f"{g}/{nm}")
    return files


if __name__ == "__main__":
    fl = write_all()
    print(len(fl), "dxf"); print("\n".join(fl[:12]))
    for n in SIZES:
        F, S = bin_flats(n)
        print(n, round(sum(f.mass() * f.qty for f in F) + sum(s.mass() * s.qty for s in S), 1), "kg")
    F, S = skid_flats()
    print("skid", round(sum(f.mass() * f.qty for f in F) + sum(s.mass() * s.qty for s in S), 1))
