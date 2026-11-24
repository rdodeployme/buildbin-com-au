"""3D CAD for BuildersBins Rev B: skid, bins by width, station assembly (STEP)."""
import math, os
import cadquery as cq
from params import *

OUT = "/home/claude/big/fab/out"
RUBBER = 1200e-9
COL = {
    "plate": cq.Color(0.16, 0.17, 0.18), "pocket": cq.Color(0.06, 0.07, 0.08),
    "copper": cq.Color(0.76, 0.50, 0.31), "rubber": cq.Color(0.05, 0.05, 0.05),
    "skid": cq.Color(0.20, 0.21, 0.22), "rail": cq.Color(0.76, 0.50, 0.31),
    "hw": cq.Color(0.55, 0.56, 0.58),
}


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def yz_prism(pts, x0, t):
    """Polygon in (y, z), extruded along +x from x0 by t."""
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(t)


def ztop(y):  # lid top surface, bin frame
    return HF + (HB - HF) * y / D


def rhs_x(x0, x1, y0, z0, bw, bh, t):
    """RHS along x, outer bw (y) x bh (z)."""
    o = box(x0, x1, y0, y0 + bw, z0, z0 + bh)
    i = box(x0 - 1, x1 + 1, y0 + t, y0 + bw - t, z0 + t, z0 + bh - t)
    return o.cut(i)


def rhs_y(y0, y1, x0, z0, bw, bh, t):
    o = box(x0, x0 + bw, y0, y1, z0, z0 + bh)
    i = box(x0 + t, x0 + bw - t, y0 - 1, y1 + 1, z0 + t, z0 + bh - t)
    return o.cut(i)


def rhs_z(z0, z1, x0, y0, bx, by, t):
    o = box(x0, x0 + bx, y0, y0 + by, z0, z1)
    i = box(x0 + t, x0 + bx - t, y0 + t, y0 + by - t, z0 - 1, z1 + 1)
    return o.cut(i)


# ------------------------------------------------------------------ bins
def bin_parts(n):
    """{part_name: (workplane, colour_key, material, density)} in the bin frame."""
    w = width(n)
    pcs = pocket_centres(w)
    P = {}
    zt0, ztD = ztop(0) - T, ztop(D) - T          # underside of lid at front / back (1796 / 1896)

    # front plate with pocket mouths
    fp = box(T, w - T, 0, T, 0, FB)
    for cx in pcs:
        fp = fp.cut(box(cx - 100, cx + 100, -1, T + 1, POCKET_Z, POCKET_Z + 100))
    P["front plate"] = (fp, "plate", "4 mm plate", STEEL)

    bp = box(T, w - T, D - T, D, 0, ztD)
    for cx in pcs:
        bp = bp.cut(box(cx - 100, cx + 100, D - T - 1, D + 1, POCKET_Z, POCKET_Z + 100))
    P["back plate"] = (bp, "plate", "4 mm plate", STEEL)

    side = [(0, 0), (D, 0), (D, ztD), (0, zt0)]
    P["side plate, left"] = (yz_prism(side, 0, T).union(box(T, 35, 0, T, FB, FTOP_B)), "plate", "4 mm plate", STEEL)
    rs = yz_prism(side, w - T, T).union(box(w - 35, w - T, 0, T, FB, FTOP_B))
    y0, y1, z0, z1 = DOOR_OPEN
    rs = rs.cut(box(w - T - 1, w + 1, y0, y1, z0, z1))
    P["side plate, right (door)"] = (rs, "plate", "4 mm plate", STEEL)

    P["floor plate"] = (box(T, w - T, T, D - T, FLOOR_Z, FLOOR_Z + T), "plate", "4 mm plate", STEEL)
    # fixed panel above the loading opening (2.0 m dump height) with a folded drip over the flap
    up = box(T, w - T, 0, T, FTOP_B, zt0).union(box(T, w - T, -20, 0, FTOP_B - T, FTOP_B)).union(box(T, w - T, -20, -20 + T, FTOP_B - 30, FTOP_B))
    P["upper front panel"] = (up, "plate", "4 mm plate", STEEL)

    # lid: sloped plate + front drip
    oh, dr = DRIP
    lid = yz_prism([(-oh, ztop(-oh) - T), (D, ztD), (D, ztop(D)), (-oh, ztop(-oh))], 0, w)
    lid = lid.union(box(0, w, -oh - T, -oh, ztop(-oh) - dr, ztop(-oh)))
    P["lid"] = (lid, "plate", "4 mm plate", STEEL)

    # flap: panel in the front plane with 25 folds on sides and top
    fx0, fx1, ftop = 36, w - 36, FTOP_B - T
    fl = box(fx0, fx1, 0, T, FB, ftop)
    fl = fl.union(box(fx0, fx0 + T, T, 29, FB, ftop)).union(box(fx1 - T, fx1, T, 29, FB, ftop))
    fl = fl.union(box(fx0, fx1, T, 29, ftop - T, ftop))
    P["flap"] = (fl, "plate", "4 mm plate", STEEL)

    # trap door on the outside of the right side, stiffeners inside the opening
    dy0, dy1, dz0, dz1 = DOOR
    P["trap door"] = (box(w, w + T, dy0, dy1, dz0, dz1), "plate", "4 mm plate", STEEL)
    st = None
    for yc in (y0 + (y1 - y0) / 3, y0 + 2 * (y1 - y0) / 3):
        s = rhs_z(z0 + 40, z1 - 40, w - 29, yc - 25, 25, 50, 3)
        st = s if st is None else st.union(s)
    P["door stiffeners"] = (st, "plate", "RHS 50x25x3", STEEL)

    # fork pockets: fabricated 6 mm box, internal 200 x 100
    pk = None
    for cx in pcs:
        a, b = cx - 100 - POCKET_T, cx + 100 + POCKET_T
        fz = FLOOR_Z + T
        p = box(cx - 100, cx + 100, T, D - T, POCKET_Z - POCKET_T, POCKET_Z)       # fork-bearing bottom
        p = p.union(box(a, b, T, D - T, POCKET_Z + 100, POCKET_Z + 100 + POCKET_T))  # top
        p = p.union(box(a, cx - 100, T, D - T, fz, POCKET_Z + 100))                 # webs, down to the floor
        p = p.union(box(cx + 100, b, T, D - T, fz, POCKET_Z + 100))
        tt = TUN_TOP
        cov = [(a, tt), (cx, tt + 50), (b, tt), (b - 6, tt), (cx, tt + 50 - 5), (a + 6, tt)]   # sloped cover so loads slide off when tipped
        p = p.union(cq.Workplane("XZ", origin=(0, D - T, 0)).polyline(cov).close().extrude(D - 2 * T))
        pk = p if pk is None else pk.union(p)
    P["fork pockets"] = (pk, "pocket", "6 mm plate", STEEL)

    # base runners inside the side walls (bear on the deck)
    P["base runners"] = (rhs_y(T, D - T, T, 0, 50, 75, 4).union(rhs_y(T, D - T, w - T - 50, 0, 50, 75, 4)),
                         "plate", "RHS 75x50x4", STEEL)
    fb = None
    for yc in (D / 3, 2 * D / 3):
        r = rhs_x(T + 50, w - T - 50, yc - 25, 0, 50, 75, 4)
        fb = r if fb is None else fb.union(r)
    P["floor bearers"] = (fb, "plate", "RHS 75x50x4", STEEL)

    # copper pocket-mouth frames, laser cut from 6 mm plate
    fr = None
    for cx in pcs:
        for ya, yb in ((-FRAME_T, 0), (D, D + FRAME_T)):
            r = box(cx - 125, cx + 125, ya, yb, POCKET_Z - 25, POCKET_Z + 125)
            r = r.cut(box(cx - 100, cx + 100, ya - 1, yb + 1, POCKET_Z, POCKET_Z + 100))
            fr = r if fr is None else fr.union(r)
    P["pocket frames"] = (fr, "copper", "6 mm plate", STEEL)

    # rubber buffers, two per side wall, clear of the door
    bt, bw = BUFFER
    bu = None
    for xa, xb in ((-bt, 0), (w, w + bt)):
        for ya in (10, D - 10 - bw):
            b = box(xa, xb, ya, ya + bw, 400, 2000)
            bu = b if bu is None else bu.union(b)
    P["rubber buffers"] = (bu, "rubber", "rubber 10 x 40", RUBBER)
    return P


def mass(wp, dens):
    return sum(s.Volume() for s in wp.solids().vals()) * dens


# ------------------------------------------------------------------ skid
def skid_parts():
    P = {}
    hy = W / 2
    runner_ys = (-RUNNER_Y, RUNNER_Y)
    r = None
    for yc in runner_ys:
        s = rhs_x(150, L, yc - SHS / 2, 0, SHS, SHS, 6)
        r = s if r is None else r.union(s)
    P["runners"] = (r, "skid", "SHS 89x89x6", STEEL)

    xs = [150 + i * (L - SHS - 150) / 9 for i in range(10)]
    cm = None
    spans = [(-hy, -RUNNER_Y - SHS / 2), (-RUNNER_Y + SHS / 2, RUNNER_Y - SHS / 2), (RUNNER_Y + SHS / 2, hy)]
    for x in xs:
        for a, b in spans:
            s = rhs_y(a, b, x, 0, SHS, SHS, 5)
            cm = s if cm is None else cm.union(s)
    P["cross members"] = (cm, "skid", "SHS 89x89x5", STEEL)

    deck = box(0, L, -hy, hy, SHS, DECK)
    holes = []
    for k in range(NDRAIN):
        xc = X0 + (k + 0.5) * DRAIN_PITCH
        for yc in (hy - RAIL[0] - 40, -hy + RAIL[0] + 40, RAIL[0] / 2 + 40, -RAIL[0] / 2 - 40):
            holes.append((xc, yc))
    for xc, yc in holes:
        deck = deck.cut(cq.Workplane("XY").circle(15).extrude(20).translate((xc, yc, SHS - 5)))
    P["deck plate"] = (deck, "skid", "10 mm plate", STEEL)

    rw, rh, rt = RAIL
    rails = None
    for y0 in (hy - rw, -rw / 2, -hy):
        s = rhs_x(X0, XH, y0, DECK, rw, rh, rt)
        rails = s if rails is None else rails.union(s)
    P["kerb rails"] = (rails, "rail", "RHS 100x50x6", STEEL)
    P["rear stop"] = (rhs_y(-hy, hy, X0 - rw, DECK, rw, rh, rt), "rail", "RHS 100x50x6", STEEL)
    P["hook-end stop"] = (rhs_y(-hy, hy, XH, DECK, rw, rh, rt), "rail", "RHS 100x50x6", STEEL)
    caps = None
    for xa in (X0 - rw, XH):
        for ya, yb in ((-hy - 6, -hy), (hy, hy + 6)):
            c = box(xa, xa + rw, ya, yb, DECK, DECK + rh)
            caps = c if caps is None else caps.union(c)
    P["stop end caps"] = (caps, "rail", "6 mm plate", STEEL)

    # rear rollers between 12 mm bracket plates
    rd, rwid = ROLLER
    ro, br = None, None
    for yc in runner_ys:
        c = cq.Workplane("XZ", origin=(0, yc + rwid / 2, 0)).center(75, rd / 2).circle(rd / 2).extrude(rwid)
        ro = c if ro is None else ro.union(c)
        for ya in (yc - rwid / 2 - 14, yc + rwid / 2 + 2):
            b = box(5, 150, ya, ya + 12, 20, SHS)
            br = b if br is None else br.union(b)
    P["rear rollers"] = (ro, "hw", "roller 140 dia x 200", STEEL)
    P["roller brackets"] = (br, "skid", "12 mm plate", STEEL)

    # hook A-frame
    px = PX
    posts, braces = None, None
    for yc in (-450, 450):
        p = rhs_z(DECK, 1500, px, yc - SHS / 2, SHS, SHS, 6)
        posts = p if posts is None else posts.union(p)
    P["hook posts"] = (posts, "skid", "SHS 89x89x6", STEEL)
    P["hook cross beam"] = (rhs_y(-450 - SHS / 2, 450 + SHS / 2, px, 1500, SHS, SHS, 5), "skid", "SHS 89x89x5", STEEL)
    for yc in (-450, 450):
        # raked brace from the hook-end stop to the post at 1,100
        x_a, z_a, x_b, z_b = XH + 50, DECK + 100, px, 1100
        ln = math.hypot(x_b - x_a, z_b - z_a)
        ang = math.degrees(math.atan2(z_b - z_a, x_b - x_a))
        b = rhs_x(0, ln, -SHS / 2 + yc, -SHS / 2, SHS, SHS, 5).rotate((0, 0, 0), (0, 1, 0), -ang).translate((x_a, 0, z_a))
        braces = b if braces is None else braces.union(b)
    P["hook braces"] = (braces, "skid", "SHS 89x89x5", STEEL)
    gus = None
    for yc in (-300, 300):
        g = box(px + SHS, px + SHS + 90, yc - 10, yc + 10, 1380, 1520)
        gus = g if gus is None else gus.union(g)
    P["hook gussets"] = (gus, "skid", "20 mm plate", STEEL)
    hb = cq.Workplane("XZ", origin=(0, 350, 0)).center(px + SHS + 65, 1450).circle(25).extrude(700)
    P["hook bar"] = (hb, "hw", "50 dia round bar", STEEL)
    mast = rhs_z(1589, LIGHT_TOP, px + 20, -25, 50, 50, 3)
    P["light mast"] = (mast, "skid", "SHS 50x50x3", STEEL)
    P["rear light post"] = (rhs_z(DECK, LIGHT_TOP, 30, -25, 50, 50, 3), "skid", "SHS 50x50x3", STEEL)
    return P


# ------------------------------------------------------------------ export
def to_assy(parts, name):
    a = cq.Assembly(name=name)
    for k, (wp, col, *_r) in parts.items():
        a.add(wp, name=k.replace(" ", "_").replace(",", "").replace("(", "").replace(")", ""), color=COL[col])
    return a


def bin_assy(n):
    return to_assy(bin_parts(n), f"BB-BIN-{tag(n)}")


def station_assy():
    st = cq.Assembly(name="BB-STATION-RevB")
    st.add(to_assy(skid_parts(), "BB-SKID"), name="skid")
    cache = {}
    for side, sid, n, x0 in layout():
        if n not in cache:
            cache[n] = bin_assy(n)
        w = width(n)
        if side == "B":
            loc = cq.Location(cq.Vector(x0, -(W / 2 - RAIL[0] - CL), DECK))
        else:
            loc = cq.Location(cq.Vector(x0 + w, W / 2 - RAIL[0] - CL, DECK), cq.Vector(0, 0, 1), 180)
        st.add(cache[n], name=f"bin_{side}_{sid}_{tag(n)}", loc=loc)
    return st


if __name__ == "__main__":
    os.makedirs(f"{OUT}/STEP", exist_ok=True)
    for n in SIZES:
        bin_assy(n).export(f"{OUT}/STEP/BB-BIN-{tag(n)}.step")
        print("bin", n, "ok", round(sum(mass(wp, d) for wp, _c, _m, d in bin_parts(n).values()), 1), "kg")
    to_assy(skid_parts(), "BB-SKID").export(f"{OUT}/STEP/BB-SKID.step")
    print("skid ok", round(sum(mass(wp, d) for wp, _c, _m, d in skid_parts().values()), 1), "kg")
    station_assy().export(f"{OUT}/STEP/BB-STATION-RevB.step")
    print("station ok")
