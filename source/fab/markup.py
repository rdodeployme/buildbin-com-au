"""Simple A3 markup set: whole station, separated, skid, typical bin. Light lines, main mm dims, notes boxes."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
from matplotlib.backends.backend_pdf import PdfPages
import cadquery as cq
from params import *
import cad
from proj import project, compound, VIEWS
from drawings import ARCH, COP, INK, GREY

LINE = "#4A5056"
DFS, LFS = 10, 12
OUT = "/home/claude/big/fab/out/BuildersBins-markup-drawings-RevB.pdf"
TOTAL = 8


# ------------------------------------------------------------ model helpers
def station(lift=0.0, skid=True, bins=True, apart=0.0):
    sh = []
    if skid:
        sh += [s for v in cad.skid_parts().values() for s in v[0].solids().vals()]
    if bins:
        cache = {}
        for side, sid, n, x0 in layout():
            if n not in cache:
                cache[n] = compound(cad.bin_parts(n))
            w = width(n)
            c = cache[n]
            if side == "B":
                loc = cq.Location(cq.Vector(x0, -(W / 2 - RAIL[0] - CL) - apart, DECK + lift))
            else:
                loc = cq.Location(cq.Vector(x0 + w, W / 2 - RAIL[0] - CL + apart, DECK + lift), cq.Vector(0, 0, 1), 180)
            sh.append(c.moved(loc))
    return cq.Compound.makeCompound(sh)


def iso_basis(view="iso"):
    d, x = VIEWS[view]
    n = np.array(d, float); n /= np.linalg.norm(n)
    vx = np.array(x, float); vx /= np.linalg.norm(vx)
    vy = np.cross(n, vx)
    return vx, vy


# ------------------------------------------------------------ sheet
class MSheet:
    def __init__(self, pdf, idx, title, sub):
        self.pdf = pdf
        self.fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
        a = self.ax = self.fig.add_axes([0, 0, 1, 1])
        a.set_xlim(0, 420); a.set_ylim(0, 297); a.axis("off")
        a.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=0.9, ec=INK))
        a.add_patch(Rectangle((10, 271), 400, 16, fc=INK, ec=INK))
        a.plot([10, 410], [271, 271], color=COP, lw=1.8)
        a.text(16, 279, "BUILDERSBINS", fontproperties=ARCH, fontsize=14, color="white", va="center")
        a.text(78, 279, title, fontsize=13, weight="bold", color="white", va="center")
        a.text(404, 279, f"Markup set · Rev B · 20 Nov 2026 · page {idx} of {TOTAL}", fontsize=9, color=COP, va="center", ha="right")
        a.text(16, 265, sub, fontsize=11, color=GREY, va="top")
        a.text(16, 13, "All measurements in millimetres. Heights from the ground with the bins on the skid. Concept only, not for construction.",
               fontsize=8.5, color=GREY)

    def notes(self, x, y, w, h, title="Changes / notes"):
        a = self.ax
        a.add_patch(Rectangle((x, y), w, h, fill=False, ec=GREY, lw=0.6))
        a.text(x + 3, y + h - 3, title, fontsize=11, weight="bold", color=INK, va="top")
        yy = y + h - 14
        while yy > y + 4:
            a.plot([x + 3, x + w - 3], [yy, yy], color="#D6DBDF", lw=0.5); yy -= 8

    def save(self):
        self.pdf.savefig(self.fig); plt.close(self.fig)


class V:
    """2D view: model (u, v) -> sheet mm."""
    def __init__(self, sh, polys, s, ox, oy, lw=0.5, col=LINE):
        self.sh, self.s, self.ox, self.oy = sh, s, ox, oy
        for p in polys:
            xs, ys = zip(*[self.t(*q) for q in p]); sh.ax.plot(xs, ys, color=col, lw=lw, solid_capstyle="round")

    def t(self, x, y):
        return self.ox + x * self.s, self.oy + y * self.s

    def arrow(self, X, Y, ux, uy):
        L = 2.6
        self.sh.ax.add_patch(Polygon([(X, Y), (X - L * ux - 0.8 * uy, Y - L * uy + 0.8 * ux),
                                      (X - L * ux + 0.8 * uy, Y - L * uy - 0.8 * ux)], fc=INK, ec="none"))

    def dim2(self, P1, P2, O1, O2, txt, fs=DFS):
        """Sheet points: P = feature points, O = dimension-line points."""
        a = self.sh.ax
        for P, O in ((P1, O1), (P2, O2)):
            dx, dy = O[0] - P[0], O[1] - P[1]; n = math.hypot(dx, dy) or 1
            a.plot([P[0] + dx / n * 1.2, O[0] + dx / n * 1.8], [P[1] + dy / n * 1.2, O[1] + dy / n * 1.8], color=INK, lw=0.35)
        a.plot([O1[0], O2[0]], [O1[1], O2[1]], color=INK, lw=0.4)
        dx, dy = O2[0] - O1[0], O2[1] - O1[1]; n = math.hypot(dx, dy) or 1
        if n > 7:
            self.arrow(O2[0], O2[1], dx / n, dy / n); self.arrow(O1[0], O1[1], -dx / n, -dy / n)
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        nx, ny = -math.sin(math.radians(ang)), math.cos(math.radians(ang))
        a.text((O1[0] + O2[0]) / 2 + nx * 1.2, (O1[1] + O2[1]) / 2 + ny * 1.2, txt, fontsize=fs, rotation=ang,
               ha="center", va="bottom", rotation_mode="anchor", color=INK, weight="bold")

    def dimh(self, x1, x2, y, ya, yb, txt=None):
        self.dim2(self.t(x1, ya), self.t(x2, yb), self.t(x1, y), self.t(x2, y), txt or f"{abs(x2 - x1):,.0f}")

    def dimv(self, y1, y2, x, xa, xb, txt=None):
        self.dim2(self.t(xa, y1), self.t(xb, y2), self.t(x, y1), self.t(x, y2), txt or f"{abs(y2 - y1):,.0f}")

    def label(self, x, y, txt, fs=LFS, **kw):
        X, Y = self.t(x, y); self.sh.ax.text(X, Y, txt, fontsize=fs, color=INK, **kw)


class IsoV(V):
    def __init__(self, sh, shape, box, view="iso", lw=0.45):
        vis, _ = project(shape, view)
        xs = [p[0] for pl in vis for p in pl]; ys = [p[1] for pl in vis for p in pl]
        bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
        x, y, w, h = box
        s = min(w / (bx1 - bx0), h / (by1 - by0))
        ox = x + (w - (bx1 - bx0) * s) / 2 - bx0 * s
        oy = y + (h - (by1 - by0) * s) / 2 - by0 * s
        super().__init__(sh, vis, s, ox, oy, lw=lw)
        self.vx, self.vy = iso_basis(view)

    def p(self, X, Y, Z):
        q = np.array([X, Y, Z], float)
        return self.t(float(q @ self.vx), float(q @ self.vy))

    def dim3(self, a, b, off, txt):
        a, b, off = np.array(a, float), np.array(b, float), np.array(off, float)
        self.dim2(self.p(*a), self.p(*b), self.p(*(a + off)), self.p(*(b + off)), txt)

    def tag(self, pt, txt, dx=0, dy=0, fs=10, **kw):
        X, Y = self.p(*pt)
        if dx or dy:
            self.sh.ax.plot([X, X + dx], [Y, Y + dy], color=COP, lw=0.7)
            self.sh.ax.plot([X], [Y], "o", ms=2.5, color=COP)
        self.sh.ax.text(X + dx, Y + dy, txt, fontsize=fs, color=INK, ha="center", va="bottom" if dy >= 0 else "top",
                        bbox=dict(fc="white", ec="none", pad=0.6), **kw)


def place(sh, polys, s, x, y, lw=0.5):
    xs = [p[0] for pl in polys for p in pl]; ys = [p[1] for pl in polys for p in pl]
    return V(sh, polys, s, x - min(xs) * s, y - min(ys) * s, lw=lw)


def bin_name(sid):
    return STREAMS[sid].get("name", sid)


# ------------------------------------------------------------ pages
def p_whole_iso(pdf):
    sh = MSheet(pdf, 1, "The whole station", "3D view from the side B / hook-end corner.")
    v = IsoV(sh, station(), (30, 40, 270, 210))
    hy = W / 2
    v.dim3((0, -hy, 0), (L, -hy, 0), (0, -700, 0), f"{L:,.0f} long")
    v.dim3((L, -hy, 0), (L, hy, 0), (900, 0, 0), "2,450 wide")
    v.dim3((0, -hy, 0), (0, -hy, DECK + HF), (0, -500, 0), f"{DECK + HF:,.0f} front edge")
    v.dim3((0, 0, 0), (0, 0, DECK + HB), (-700, 0, 0), f"{DECK + HB:,.0f} ridge")
    v.tag((L - 150, 0, 1500), "hook frame", dx=12, dy=12)
    v.tag((2000, -hy, DECK + 50), "kerb rail 100 high", dx=-10, dy=-16)
    sh.notes(310, 40, 95, 210)
    sh.save()


def p_whole_ortho(pdf):
    sh = MSheet(pdf, 2, "The whole station: plan, side and end", "Plan from above, side B elevation, and the hook-end view.")
    s = 1 / 30
    st = station()
    top, _ = project(st, "top")
    vp = place(sh, top, s, 40, 168)
    vp.dimh(0, L, W / 2 + 260, W / 2, W / 2)
    vp.dimv(-W / 2, W / 2, -260, 0, 0)
    for side, sid, n, x0 in layout():
        w = width(n)
        vp.label(x0 + w / 2, 600 if side == "A" else -600, f"{bin_name(sid)}\n{w:,.0f}", fs=8.5, ha="center", va="center",
                 rotation=90 if width(n) < 1000 else 0)
    vp.label(-150, W / 2 - 350, "SIDE A", fs=9, ha="right", weight="bold")
    vp.label(-150, -W / 2 + 250, "SIDE B", fs=9, ha="right", weight="bold")
    vp.label(L / 2, -W / 2 - 280, "PLAN (hook end on the right)", fs=11, ha="center", weight="bold", va="top")

    fr, _ = project(st, "front")
    ve = place(sh, fr, s, 40, 42)
    ve.dimv(0, DECK + HF, -250, 0, 0, txt=f"{DECK + HF:,.0f}")
    ve.dimv(0, DECK + HB, -600, 0, 0, txt=f"{DECK + HB:,.0f}")
    ve.dimv(0, DECK + FB, L + 200, L, L, txt=f"{DECK + FB:,.0f} flap")
    ve.dimv(0, DECK + FTOP_B, L + 450, L, L, txt=f"{DECK + FTOP_B:,.0f} dump height")
    ve.label(L / 2, -60, "SIDE B ELEVATION", fs=11, ha="center", weight="bold", va="top")

    en, _ = project(st, ((1, 0, 0), (0, 1, 0)))
    vx = place(sh, en, s, 305, 42)
    vx.dimh(-W / 2, W / 2, 2350, 2000, 2000)
    vx.dimv(0, 1450, W / 2 + 200, W / 2 - 400, W / 2 - 400, txt="1,450 hook")
    vx.label(0, -60, "HOOK-END VIEW", fs=11, ha="center", weight="bold", va="top")
    sh.notes(300, 160, 105, 95)
    sh.save()


def p_sep_iso(pdf):
    sh = MSheet(pdf, 3, "Separated: bins lifted off the skid",
                "Bins raised 1,200 so you can see the skid, the kerb rails and how each bin sits. Bin widths along the front.")
    lift = 1200
    v = IsoV(sh, station(lift=lift), (25, 35, 290, 222))
    hy = W / 2
    yb = -(W / 2 - RAIL[0] - CL)
    for side, sid, n, x0 in layout():
        w = width(n)
        if side == "B":
            v.dim3((x0, yb, DECK + lift), (x0 + w, yb, DECK + lift), (0, -350, 0), f"{w:,.0f}")
            v.tag((x0 + w / 2, yb, DECK + lift + 1300), f"{bin_name(sid)}", fs=9 if width(n) >= 1000 else 8, rotation=90 if width(n) < 1000 else 0)
        else:
            v.tag((x0 + w / 2, 0, DECK + lift + HB + 30), f"{bin_name(sid)} · {w:,.0f}", dx=0, dy=8, fs=8.5)
    v.tag((1200, -hy + 25, DECK + 100), "outer kerb rail", dx=-14, dy=10)
    v.tag((5200, 0, DECK + 100), "centre rail", dx=16, dy=-18)
    v.dim3((X0, -hy, 0), (XH, -hy, 0), (0, -800, 0), f"{XH - X0:,.0f} bin zone")
    sh.notes(320, 35, 85, 222)
    sh.save()


def p_sep_elev(pdf):
    sh = MSheet(pdf, 4, "Separated: bin sizes along each side",
                f"Each side takes {XH - X0 - 4 * GAP:,.0f} of bins plus 20 mm gaps. Bins are 1,000 to 2,470 wide.")
    s = 1 / 30
    bins_only = station(skid=False)
    for k, (side, view, yb0, title) in enumerate((("B", "front", 150, "SIDE B (as you stand at side B)"),
                                                   ("A", ((0, 1, 0), (-1, 0, 0)), 30 + 0, "SIDE A (as you stand at side A)"))):
        pass
    # side B
    frB, _ = project(station(skid=False), "front")
    vb = place(sh, frB, s, 62, 162)
    xsB = [(x0, n, sid) for side, sid, n, x0 in layout() if side == "B"]
    for x0, n, sid in xsB:
        w = width(n)
        vb.dimh(x0, x0 + w, -120, 0, 0, txt=f"{w:,.0f}")
        vb.label(x0 + w / 2, 1450, f"{bin_name(sid)}", fs=9, ha="center", va="center", rotation=90 if width(n) < 1000 else 0)
    vb.dimv(0, HF, X0 - 260, X0, X0, txt=f"{HF:,.0f}")
    vb.dimv(0, FB, X0 - 520, X0, X0, txt=f"{FB:,.0f} flap")
    vb.dimv(0, FTOP_B, X0 - 780, X0, X0, txt=f"{FTOP_B:,.0f} opening")
    vb.label(L / 2, -330, "SIDE B BINS (as you stand at side B)", fs=11, ha="center", weight="bold", va="top")
    # side A, viewed from +y: x runs right-to-left
    frA, _ = project(station(skid=False), ((0, 1, 0), (-1, 0, 0)))
    va = place(sh, frA, s, 62, 52)
    # in this view u = -x, so map x -> u = -x
    xsA = [(x0, n, sid) for side, sid, n, x0 in layout() if side == "A"]
    for x0, n, sid in xsA:
        w = width(n)
        va.dimh(-(x0 + w), -x0, -120, 0, 0, txt=f"{w:,.0f}")
        va.label(-(x0 + w / 2), 1450, f"{bin_name(sid)}", fs=9, ha="center", va="center", rotation=90 if width(n) < 1000 else 0)
    va.label(-L / 2, -330, "SIDE A BINS (as you stand at side A)", fs=11, ha="center", weight="bold", va="top")
    sh.notes(310, 52, 95, 205)
    sh.save()


def p_skid_iso(pdf):
    sh = MSheet(pdf, 5, "The skid on its own", "Bins removed. 10 mm deck on SHS 89 runners and cross members, kerb rails welded on top.")
    sk = compound(cad.skid_parts())
    v = IsoV(sh, sk, (25, 40, 290, 215))
    hy = W / 2
    v.dim3((0, -hy, 0), (L, -hy, 0), (0, -700, 0), f"{L:,.0f}")
    v.dim3((L, -hy, 0), (L, hy, 0), (900, 0, 0), "2,450")
    v.tag((2500, -hy + 25, DECK + 100), "outer kerb rail RHS 100x50x6", dx=-10, dy=-18)
    v.tag((2500, 0, DECK + 100), "centre rail", dx=8, dy=14)
    v.tag((X0 - 25, 700, DECK + 100), "rear stop", dx=-10, dy=10)
    v.tag((XH + 25, -900, DECK + 100), "hook-end stop", dx=10, dy=-14)
    v.tag((PX + 44, 0, 1500), "hook frame, hook bar 1,450", dx=6, dy=14)
    v.tag((75, -550, 70), "rear rollers", dx=-12, dy=-10)
    v.tag((L - 30, 0, LIGHT_TOP), f"light mast {LIGHT_TOP:,}", dx=-30, dy=6)
    sh.notes(320, 40, 85, 215)
    sh.save()


def p_skid_ortho(pdf):
    sh = MSheet(pdf, 6, "The skid: plan, side and end", "Where the rails, runners and cross members sit.")
    s = 1 / 30
    sk = compound(cad.skid_parts())
    top, _ = project(sk, "top")
    vp = place(sh, top, s, 45, 160)
    hy = W / 2
    vp.dimh(0, L, hy + 220, hy, hy)
    vp.dimh(0, X0, -hy - 150, -hy, -hy, txt="150")
    vp.dimh(X0, XH, -hy - 150, -hy, -hy, txt=f"{XH - X0:,.0f} bin zone")
    vp.dimh(XH, L, -hy - 150, -hy, -hy, txt="300")
    vp.dimv(-hy, hy, -250, 0, 0)
    vp.dimv(-RUNNER_Y, RUNNER_Y, L + 250, L, L, txt="1,100 runners")
    vp.dimv(hy - RAIL[0] - CL - D, hy - RAIL[0] - CL, L + 520, L, L, txt="1,140 bin")
    vp.label(L / 2, -hy - 420, "SKID PLAN", fs=11, ha="center", weight="bold", va="top")

    fr, _ = project(sk, "front")
    ve = place(sh, fr, s, 45, 50)
    ve.dimv(0, DECK, -200, 0, 0, txt="99 deck")
    ve.dimv(0, DECK + RAIL[1], -520, 0, 0, txt="199 rail")
    ve.dimv(0, 1450, L + 250, L - 40, L - 40, txt="1,450 hook")
    ve.dimv(0, LIGHT_TOP, L + 560, L - 300, L - 300, txt=f"{LIGHT_TOP:,}")
    ve.label(L / 2, -120, "SKID SIDE", fs=11, ha="center", weight="bold", va="top")

    en, _ = project(sk, ((-1, 0, 0), (0, -1, 0)))
    vx = place(sh, en, s, 300, 160)
    vx.label(0, -200, "REAR END", fs=11, ha="center", weight="bold", va="top")
    # rear view: u = -y
    vx.dimh(-hy, hy, -100, 0, 0)
    sh.notes(300, 42, 105, 80)
    sh.save()


def p_bin_iso(pdf, n=None):
    n = n or SIZES[0]
    w = width(n)
    sh = MSheet(pdf, 7, f"A typical bin ({w:,.0f} wide)",
                f"Flap side and trap-door side. Five bins are this size ({', '.join(used_by(n))}); the others differ only in width.")
    b = compound(cad.bin_parts(n))
    v1 = IsoV(sh, b, (25, 45, 135, 200), view="iso2")
    v1.dim3((0, 0, 0), (w, 0, 0), (0, -300, 0), f"{w:,.0f}")
    v1.dim3((0, 0, 0), (0, D, 0), (-300, 0, 0), "1,140")
    v1.tag((w / 2, 0, FB + 330), "drop-down flap", dx=0, dy=0, fs=9)
    v1.tag((pocket_centres(w)[0], 0, POCKET_Z + 50), "fork pocket", dx=-10, dy=-14, fs=9)
    v1.label(0, 0, "")
    sh.ax.text(92, 40, "FLAP SIDE", fontsize=11, weight="bold", ha="center")
    v2 = IsoV(sh, b, (170, 45, 135, 200), view="iso")
    v2.tag((w, D / 2, 1030), "trap door, top-hinged", dx=10, dy=0, fs=9)
    v2.tag((w / 2, D * 0.6, ztop_(D * 0.6)), "hard lid", dx=0, dy=8, fs=9)
    sh.ax.text(237, 40, "TRAP-DOOR SIDE", fontsize=11, weight="bold", ha="center")
    sh.notes(315, 45, 90, 200)
    sh.save()


def ztop_(y):
    return HF + (HB - HF) * y / D


def p_bin_ortho(pdf, n=None):
    n = n or SIZES[0]
    w = width(n)
    sh = MSheet(pdf, 8, f"A typical bin: front and side ({w:,.0f} wide)", "Heights from the bin base. Add 99 for heights from the ground on the skid.")
    s = 1 / 17
    b = compound(cad.bin_parts(n))
    pcs = pocket_centres(w)
    fr, _ = project(b, "front")
    vf = V(sh, fr, s, 55, 62)
    vf.dimh(0, w, -150, 0, 0)
    vf.dimh(36, w - 36, FB + 250, FB, FB, txt=f"{w - 72:,.0f} flap")
    vf.dimh(pcs[0], pcs[1], POCKET_Z - 90, POCKET_Z, POCKET_Z, txt=f"{pcs[1] - pcs[0]:,.0f} pockets")
    vf.dimv(0, POCKET_Z, -120, pcs[0] - 100, pcs[0] - 100, txt="200")
    vf.dimv(0, FB, -330, 0, 0, txt=f"{FB:,.0f}")
    vf.dimv(0, FTOP_B, -540, 0, 0, txt=f"{FTOP_B:,.0f} opening")
    vf.dimv(0, HF, -750, 0, 0, txt=f"{HF:,.0f}")
    vf.label(w / 2, -330, "FRONT (flap side)", fs=11, ha="center", weight="bold", va="top")
    rt, _ = project(b, "right")
    vr = V(sh, rt, s, 55 + w * s + 55, 62)
    vr.dimh(0, D, -150, 0, 0)
    vr.dimv(0, HB, D + 140, D, D, txt=f"{HB:,.0f}")
    vr.dimv(DOOR[2], DOOR[3], D + 360, D, D, txt=f"{DOOR[3] - DOOR[2]:,.0f} door")
    vr.dimh(DOOR[0], DOOR[1], DOOR[3] + 330, DOOR[3], DOOR[3], txt="1,030 door")
    vr.label(D / 2, -330, "RIGHT SIDE (trap door)", fs=11, ha="center", weight="bold", va="top")
    sh.notes(300, 62, 105, 190)
    sh.save()


def build():
    with PdfPages(OUT) as pdf:
        p_whole_iso(pdf); p_whole_ortho(pdf); p_sep_iso(pdf); p_sep_elev(pdf)
        p_skid_iso(pdf); p_skid_ortho(pdf); p_bin_iso(pdf); p_bin_ortho(pdf)
    return OUT


if __name__ == "__main__":
    print(build())
