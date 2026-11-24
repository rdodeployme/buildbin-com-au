"""A3 PDF drawing set for BuildersBins Rev B (third-angle projection, mm)."""
import math, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, Polygon
from matplotlib.backends.backend_pdf import PdfPages
import cadquery as cq
from params import *
import cad, flats
from proj import project, compound

fm.fontManager.addfont("/home/claude/big/fonts/Archivo-800.ttf")
ARCH = fm.FontProperties(fname="/home/claude/big/fonts/Archivo-800.ttf")
plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
COP, INK, GREY = "#C2804F", "#0E1114", "#6B7177"
DIMFS, NOTEFS = 8.5, 11
DATE = "20 Nov 2026"
OUT = "/home/claude/big/fab/out"
SHEETS = []          # (number, title) filled as we go, used on the cover


class Sheet:
    def __init__(self, pdf, num, title, scale_txt, total):
        self.pdf, self.num, self.title = pdf, num, title
        self.fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
        ax = self.ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.axis("off")
        ax.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=1.2, ec=INK))
        self.title_block(scale_txt, total)

    def title_block(self, scale_txt, total):
        a = self.ax
        x0, y0, wd, ht = 250, 10, 160, 46
        a.add_patch(Rectangle((x0, y0), wd, ht, fill=False, lw=1.0, ec=INK))
        a.add_patch(Rectangle((x0, y0 + ht - 13), wd, 13, fc=INK, ec=INK))
        a.text(x0 + 4, y0 + ht - 6.5, "BUILDERSBINS", fontproperties=ARCH, fontsize=15, color="white", va="center")
        a.text(x0 + wd - 4, y0 + ht - 6.5, "Build. Innovate. Gain.", fontsize=9, color=COP, va="center", ha="right")
        a.plot([x0, x0 + wd], [y0 + ht - 13.6] * 2, color=COP, lw=1.6)
        a.text(x0 + 4, y0 + 25, self.title, fontsize=12, weight="bold", va="center", color=INK)
        a.text(x0 + 4, y0 + 17, "Station Rev B · concept for quotation · not for construction", fontsize=8.5, color=GREY, va="center")
        for i, (k, v) in enumerate([("DWG", f"BB-{self.num}"), ("SCALE @A3", scale_txt), ("REV", "B"),
                                    ("DATE", DATE), ("SHEET", f"{SHEETS_INDEX[self.num]} of {total}")]):
            xx = x0 + 4 + i * 31.5
            a.text(xx, y0 + 9, k, fontsize=6.5, color=GREY)
            a.text(xx, y0 + 3.5, v, fontsize=9, color=INK, weight="bold")
        a.text(14, 13, "All dimensions in millimetres · do not scale · third-angle projection · Recycle Group",
               fontsize=8, color=GREY)

    def save(self):
        self.pdf.savefig(self.fig); plt.close(self.fig)


class View:
    def __init__(self, sh, polys, s, ox, oy, lw=0.55, color=INK, hidden=()):
        self.sh, self.s, self.ox, self.oy = sh, s, ox, oy
        for p in polys:
            xs, ys = zip(*[self.t(*q) for q in p]); sh.ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round")
        for p in hidden:
            xs, ys = zip(*[self.t(*q) for q in p]); sh.ax.plot(xs, ys, color=GREY, lw=0.35, ls=(0, (3, 2)))

    def t(self, x, y):
        return self.ox + x * self.s, self.oy + y * self.s

    def label(self, x, y, txt, sub=""):
        X, Y = self.t(x, y)
        self.sh.ax.text(X, Y, txt, fontsize=10.5, weight="bold", ha="center", va="top", color=INK)
        if sub:
            self.sh.ax.text(X, Y - 5, sub, fontsize=8.5, ha="center", va="top", color=GREY)

    def note(self, x, y, txt, ha="left", fs=DIMFS, color=INK, **kw):
        X, Y = self.t(x, y); self.sh.ax.text(X, Y, txt, fontsize=fs, ha=ha, color=color, **kw)

    def _arrow(self, X, Y, dx, dy):
        L = 2.2; n = math.hypot(dx, dy) or 1; ux, uy = dx / n, dy / n
        self.sh.ax.add_patch(Polygon([(X, Y), (X - L * ux - 0.7 * uy, Y - L * uy + 0.7 * ux),
                                      (X - L * ux + 0.7 * uy, Y - L * uy - 0.7 * ux)], fc=INK, ec="none"))

    def dimh(self, x1, x2, y, ya=None, yb=None, txt=None, above=True):
        a = self.sh.ax
        X1, Y = self.t(x1, y); X2, _ = self.t(x2, y)
        for xx, yy in ((x1, ya), (x2, yb)):
            if yy is not None:
                Xe, Ye = self.t(xx, yy); a.plot([Xe, Xe], [Ye + (1 if Y > Ye else -1), Y + (1.5 if Y > Ye else -1.5)], color=INK, lw=0.3)
        a.plot([X1, X2], [Y, Y], color=INK, lw=0.3)
        if abs(X2 - X1) > 6:
            self._arrow(X2, Y, 1, 0); self._arrow(X1, Y, -1, 0)
        t = txt if txt is not None else f"{abs(x2 - x1):,.0f}"
        a.text((X1 + X2) / 2, Y + (0.8 if above else -0.8), t, fontsize=DIMFS, ha="center", va="bottom" if above else "top", color=INK)

    def dimv(self, y1, y2, x, xa=None, xb=None, txt=None, left=True):
        a = self.sh.ax
        X, Y1 = self.t(x, y1); _, Y2 = self.t(x, y2)
        for yy, xx in ((y1, xa), (y2, xb)):
            if xx is not None:
                Xe, Ye = self.t(xx, yy); a.plot([Xe + (1 if X > Xe else -1), X + (1.5 if X > Xe else -1.5)], [Ye, Ye], color=INK, lw=0.3)
        a.plot([X, X], [Y1, Y2], color=INK, lw=0.3)
        if abs(Y2 - Y1) > 6:
            self._arrow(X, Y2, 0, 1 if Y2 > Y1 else -1); self._arrow(X, Y1, 0, -1 if Y2 > Y1 else 1)
        t = txt if txt is not None else f"{abs(y2 - y1):,.0f}"
        a.text(X + (-0.8 if left else 0.8), (Y1 + Y2) / 2, t, fontsize=DIMFS, rotation=90, ha="right" if left else "left",
               va="center", color=INK)


def box_text(sh, x, y, w, lines, title=None, fs=NOTEFS, lh=5.2):
    a = sh.ax
    yy = y
    if title:
        a.text(x, yy, title, fontsize=fs + 0.5, weight="bold", color=INK, va="top"); yy -= lh + 1.5
        a.plot([x, x + w], [yy + 2.2, yy + 2.2], color=COP, lw=1.2)
    for ln in lines:
        a.text(x, yy, ln, fontsize=fs, color=INK, va="top"); yy -= lh
    return yy


# -------------------------------------------------------------- views
def bbox_of(polys):
    xs = [p[0] for pl in polys for p in pl]; ys = [p[1] for pl in polys for p in pl]
    return min(xs), min(ys), max(xs), max(ys)


def place(sh, polys, s, x, y, **kw):
    """Place polys with their bbox lower-left at sheet (x, y). Returns view."""
    bx0, by0, _, _ = bbox_of(polys)
    return View(sh, polys, s, x - bx0 * s, y - by0 * s, **kw)


# -------------------------------------------------------------- sheets
def sheet_cover(pdf, total):
    sh = Sheet(pdf, "000", "Cover, notes and sheet list", "NTS", total)
    st = cad.station_assy().toCompound()
    vis, _ = project(st, "iso")
    bx0, by0, bx1, by1 = bbox_of(vis)
    s = min(225 / (bx1 - bx0), 175 / (by1 - by0))
    View(sh, vis, s, 18 - bx0 * s, 50 - by0 * s, lw=0.45)
    a = sh.ax
    a.text(18, 272, "BuildersBins station", fontproperties=ARCH, fontsize=26, color=INK, va="top")
    a.text(18, 259, f"Fabrication drawings · Rev B · eight 4 mm steel bins on a {L / 1000:.1f} m hook skid", fontsize=12, color=GREY, va="top")
    a.plot([18, 90], [253, 253], color=COP, lw=2.2)
    box_text(sh, 255, 272, 150, [
        "1. Concept design for quotation. The fabricator prepares",
        "   shop drawings; a structural engineer certifies the skid,",
        "   hook, fork pockets, hinges and latches.",
        "2. Bins 4 mm plate, pockets and frames 6 mm, deck 10 mm.",
        "   Plate Gr 250/300; hollow sections C350L0.",
        "3. Welding to AS/NZS 1554.1 SP. Kerb rails: continuous",
        "   6 mm fillet both sides to the deck.",
        "4. DXF flats are outside-dimension nets. Apply your own",
        "   bend deductions.",
        "5. Heights from the ground: deck top 99 (SHS 89 + 10 plate),",
        f"   ridge {DECK + HB:,.0f}, lid front edge {DECK + HF:,.0f}, opening top {DECK + FTOP_B:,.0f}.",
        "6. Hook, rollers and runner spacing to suit the operator's",
        "   hook-lift fleet. Confirm before cutting.",
        "7. Finish charcoal; copper #C2804F on rails and pocket frames.",
    ], title="General notes", fs=9.5, lh=4.6)
    yy = 196
    a.text(255, yy, "Sheets", fontsize=10.5, weight="bold", color=INK, va="top"); yy -= 6
    a.plot([255, 405], [yy + 2.2, yy + 2.2], color=COP, lw=1.2)
    for num, title in SHEET_LIST:
        a.text(255, yy, f"BB-{num}", fontsize=8.5, color=GREY, va="top")
        a.text(274, yy, title, fontsize=8.5, color=INK, va="top"); yy -= 4.1
    sh.save()


def sheet_ga(pdf, total):
    sh = Sheet(pdf, "001", "Station general arrangement", "1:30", total)
    s = 1 / 30
    st = cad.station_assy().toCompound()
    top, _ = project(st, "top")
    vp = place(sh, top, s, 40, 186)
    vp.label(L / 2, -W / 2 - 160, "PLAN", "Hook end on the right")
    vp.dimh(0, L, W / 2 + 260, W / 2, W / 2)
    vp.dimv(-W / 2, W / 2, -250, 0, 0)
    for side, sid, n, x0 in layout():
        w = width(n)
        yc = 600 if side == "A" else -600
        vp.note(x0 + w / 2, yc, f"{STREAMS[sid]['name']}\n{w:,.0f}", ha="center", fs=7.5, va="center", color=GREY, rotation=90 if w < 1000 else 0)
    vp.note(-200, W / 2 - 300, "SIDE A", ha="right", fs=9, weight="bold")
    vp.note(-200, -W / 2 + 200, "SIDE B", ha="right", fs=9, weight="bold")

    fr, _ = project(st, "front")
    ve = place(sh, fr, s, 40, 62)
    ve.label(L / 2, -150, "SIDE B ELEVATION")
    ve.dimv(0, DECK, -150, 0, 0, left=True)
    ve.dimv(0, DECK + HF, -450, 0, 0)
    ve.dimv(0, DECK + HB, -750, None, None, txt=f"{DECK + HB:,.0f} ridge")
    ve.dimv(0, DECK + FB, L + 180, L, L, left=False)
    for side, _s, n_, x_ in layout():
        if side == "B":
            ve.dimh(x_, x_ + width(n_), DECK + HF + 160, None, None)

    en, _ = project(st, ((1, 0, 0), (0, 1, 0)))
    vx = place(sh, en, s, 300, 62)
    vx.label(0, -150, "HOOK-END VIEW")
    vx.dimh(-W / 2, W / 2, -60, None, None)
    vx.dimv(0, 1450, W / 2 + 180, None, None, left=False, txt="1,450 hook")
    vx.dimv(0, LIGHT_TOP, W / 2 + 380, None, None, left=False, txt=f"{LIGHT_TOP:,} light")
    box_text(sh, 330, 268, 75, [f"Overall {L:,.0f} x {W:,.0f} x {DECK + HB:,.0f}", "Bins 1,140 deep, 4 per side",
                                f"Station tare ≈ {TARE['station'] / 1000:.1f} t"], title="Key figures", fs=9.5, lh=4.6)
    sh.save()


def sheet_skid(pdf, total):
    sh = Sheet(pdf, "010", "Hook skid", "1:25", total)
    s = 1 / 25
    sk = compound(cad.skid_parts())
    top, _ = project(sk, "top")
    vp = place(sh, top, s, 30, 170)
    vp.label(L / 2, -W / 2 - 170, "SKID PLAN", "Bins removed")
    vp.dimh(0, L, W / 2 + 250, W / 2, W / 2)
    vp.dimh(0, X0, -W / 2 - 80, -W / 2, -W / 2, above=False)
    vp.dimh(X0, XH, -W / 2 - 80, None, -W / 2, above=False, txt=f"{XH - X0:,.0f} bin zone")
    vp.dimh(XH, L, -W / 2 - 80, None, L and -W / 2, above=False)
    vp.dimv(-W / 2, W / 2, -260, 0, 0)
    vp.dimv(-RUNNER_Y, RUNNER_Y, L + 250, L, L, left=False, txt="1,100 runner ctrs")
    vp.dimv(W / 2 - RAIL[0], W / 2, -120, 0, 0, txt="50")

    fr, _ = project(sk, "front")
    ve = place(sh, fr, s, 30, 75)
    ve.label(L / 2, -160, "SKID SIDE ELEVATION")
    ve.dimv(0, SHS, -120, 0, 0, txt="89")
    ve.dimv(0, DECK + RAIL[1], -380, 0, 0, txt="199 rail top")
    ve.dimv(0, 1450, L + 200, L, L, left=False, txt="1,450 hook ctr")
    ve.dimv(0, LIGHT_TOP, L + 420, L, L, left=False, txt=f"{LIGHT_TOP:,}")
    xs = [150 + i * (L - SHS - 150) / 9 for i in range(10)]
    ve.dimh(xs[0], xs[1], -60, 0, 0, above=False, txt=f"{xs[1] - xs[0]:.0f} x-member pitch")
    box_text(sh, 330, 268, 75, [
        "Runners SHS 89 x 89 x 6", "Cross members SHS 89 x 89 x 5", "Deck 10 mm, 40 drain holes 30 dia",
        "Kerb rails RHS 100 x 50 x 6", "Stops RHS 100 x 50 x 6, full width", "Rollers 140 dia x 200 (to suit)",
        "Hook bar 50 dia (to suit fleet)", f"Skid tare ≈ {TARE['skid']:,.0f} kg",
        "See BB-011 for the kerb rail."], title="Skid", fs=9.5, lh=4.6)
    sh.save()


def sheet_rail(pdf, total):
    sh = Sheet(pdf, "011", "Kerb rail and bin restraint details", "1:4", total)
    a = sh.ax
    s = 1 / 4
    yL = W / 2 - 420                                   # left edge of detail A (model y)
    v = View(sh, [], s, 50 - yL * s, 75)
    yR0, yR1 = W / 2 - RAIL[0], W / 2
    yb = yR0 - CL                                       # bin front face

    def R(x0, x1, y0, y1, **kw):
        X0_, Y0_ = v.t(x0, y0); X1_, Y1_ = v.t(x1, y1)
        a.add_patch(Rectangle((X0_, Y0_), X1_ - X0_, Y1_ - Y0_, **kw))
    a.plot(*zip(v.t(yL - 10, 0), v.t(W / 2 + 70, 0)), color=INK, lw=0.8)
    a.text(*v.t(W / 2 + 72, -6), "ground", fontsize=8.5, color=GREY, va="top")
    R(yL, W / 2, 0, SHS, fc="none", ec=INK, lw=0.6)
    R(yL, W / 2 - 5, 5, SHS - 5, fc="none", ec=GREY, lw=0.4, ls="--")
    R(yL, W / 2, SHS, DECK, fc="#D6DBDF", ec=INK, lw=0.6)
    R(yR0, yR1, DECK, DECK + RAIL[1], fc=COP, ec=INK, lw=0.7)
    R(yR0 + 6, yR1 - 6, DECK + 6, DECK + RAIL[1] - 6, fc="white", ec=INK, lw=0.5)
    for xx, sg in ((yR0, -1), (yR1, 1)):
        a.add_patch(Polygon([v.t(xx, DECK), v.t(xx + sg * 6, DECK), v.t(xx, DECK + 6)], fc=INK))
    top = DECK + 560
    R(yb - T, yb, DECK, DECK + POCKET_Z, fc="#2A3036", ec=INK, lw=0.6)
    R(yb - T, yb, DECK + POCKET_Z + 100, top, fc="#2A3036", ec=INK, lw=0.6)
    R(yb, yb + FRAME_T, DECK + POCKET_Z - 25, DECK + POCKET_Z, fc=COP, ec=INK, lw=0.5)
    R(yb, yb + FRAME_T, DECK + POCKET_Z + 100, DECK + POCKET_Z + 125, fc=COP, ec=INK, lw=0.5)
    R(yL, yb - T, DECK + POCKET_Z - POCKET_T, DECK + POCKET_Z, fc="#0B0D0F", ec=INK, lw=0.5)
    R(yL, yb - T, DECK + POCKET_Z + 100, DECK + POCKET_Z + 106, fc="#0B0D0F", ec=INK, lw=0.5)
    R(yL, yb - T, DECK + FLOOR_Z, DECK + FLOOR_Z + T, fc="#2A3036", ec=INK, lw=0.5)
    R(yL, yL + 50, DECK, DECK + 75, fc="none", ec=GREY, lw=0.5, ls="--")
    X0_, Y0_ = v.t(yL, DECK + POCKET_Z + 25); X1_, _ = v.t(W / 2 + 150, 0)
    a.add_patch(Rectangle((X0_, Y0_), X1_ - X0_, 50 * s, fill=False, ec=GREY, lw=0.9, ls=(0, (4, 2))))
    a.text(*v.t(W / 2 + 155, DECK + POCKET_Z + 50), "fork tine", fontsize=8.5, color=GREY, va="center")
    v.dimh(yb, yR0, DECK + RAIL[1] + 60, DECK + 150, DECK + RAIL[1], txt="5")
    v.dimh(yR0, yR1, DECK + RAIL[1] + 25, DECK + RAIL[1], DECK + RAIL[1], txt="50")
    v.dimv(0, SHS, W / 2 + 25, W / 2, W / 2, left=False, txt="89")
    v.dimv(SHS, DECK, W / 2 + 60, W / 2, W / 2, left=False, txt="10")
    v.dimv(DECK, DECK + RAIL[1], W / 2 + 25, W / 2, W / 2, left=False, txt="100 rail")
    v.dimv(DECK + RAIL[1], DECK + POCKET_Z, W / 2 + 25, None, None, left=False, txt="100 clear")
    v.dimv(DECK + POCKET_Z, DECK + POCKET_Z + 100, W / 2 + 25, None, None, left=False, txt="100 pocket")
    v.dimv(0, DECK + POCKET_Z, yL - 40, None, yL, txt="299 pocket underside")
    v.dimv(0, DECK + RAIL[1], yL - 110, None, None, txt="199 rail top")
    v.note(yb - 30, top - 40, "bin front plate 4", ha="right", fs=8.5)
    v.note(yb - 30, DECK + FLOOR_Z + 18, "floor 4", ha="right", fs=8.5)
    v.note(yb - 30, DECK + POCKET_Z + 112, "pocket box, 6 mm, 200 x 100 internal", ha="right", fs=8.5)
    v.note(yL + 60, DECK + 30, "base runner", fs=8.5, color=GREY)
    v.note(W / 2 + 120, DECK + 10, "6 CFW both sides,\nfull length", fs=8.5, weight="bold")
    v.note(yb + 10, DECK + POCKET_Z + 140, "copper frame", fs=8.5)
    v.label((yL + W / 2) / 2, -30, "DETAIL A  1:4", "Section across the outer kerb rail at a fork pocket")

    s2 = 1 / 4
    v2 = View(sh, [], s2, 230, 215)
    R2 = lambda x0, x1, y0, y1, **kw: a.add_patch(Rectangle(v2.t(x0, y0), (x1 - x0) * s2, (y1 - y0) * s2, **kw))
    R2(0, 50, 0, 160, fc=COP, ec=INK, lw=0.6); R2(6, 44, 0, 154, fc="white", ec=INK, lw=0.4)
    R2(50, 330, 110, 160, fc=COP, ec=INK, lw=0.6); R2(50, 330, 116, 154, fc="white", ec=INK, lw=0.4)
    R2(0, 50, 160, 166, fc=INK, ec=INK)
    R2(60, 330, -60, 105, fc="#2A3036", ec=INK, lw=0.6)
    R2(50, 60, -60, 70, fc=INK, ec=INK)
    v2.dimh(50, 60, -80, -60, -60, above=False, txt="10")
    v2.dimv(105, 110, 345, 330, 330, left=False, txt="5")
    v2.note(195, 20, "bin", ha="center", color="white", fs=9, va="center")
    v2.note(55, -120, "rubber buffer 10 x 40", fs=8.5)
    v2.note(25, 185, "6 cap", ha="center", fs=8.5)
    v2.note(200, 175, "kerb rail", ha="center", fs=8.5)
    v2.note(-12, 80, "rear stop", ha="right", fs=8.5, rotation=90, va="center")
    v2.label(165, -150, "DETAIL B  1:4", "Plan at the rear stop corner")

    v3 = View(sh, [], s2, 340, 215)
    R3 = lambda x0, x1, y0, y1, **kw: a.add_patch(Rectangle(v3.t(x0, y0), (x1 - x0) * s2, (y1 - y0) * s2, **kw))
    R3(0, 120, -60, 160, fc="#2A3036", ec=INK, lw=0.6)
    R3(140, 260, -60, 160, fc="#2A3036", ec=INK, lw=0.6)
    R3(120, 130, -60, -20, fc=INK, ec=INK); R3(130, 140, -60, -20, fc=INK, ec=INK)
    R3(120, 124, 0, 160, fc=GREY, ec=INK, lw=0.4)
    v3.dimh(120, 140, -80, -60, -60, above=False, txt="20")
    v3.note(60, 60, "bin", ha="center", color="white", fs=9, va="center")
    v3.note(200, 60, "next", ha="center", color="white", fs=9, va="center")
    v3.note(122, 175, "trap door 4", ha="center", fs=8.5)
    v3.label(130, -150, "DETAIL C  1:4", "Plan between two bins")

    box_text(sh, 230, 160, 175, [
        "• The lip is now a 100 x 50 x 6 RHS kerb, not a folded",
        f"  plate. A closed tube welded along its full {XH - X0:,.0f} can't",
        "  fold over when a bin or a fork knocks it.",
        "• 6 mm fillet weld both sides, full length, to the 10 mm",
        "  deck over SHS cross members. Rails butt into the rear",
        "  and hook-end stops and are welded all round.",
        "• Bins sit 5 clear of each rail: they drop in without",
        "  binding but can't move more than 5 across.",
        "• Fork pockets sit 100 above the rail top, so the forks",
        "  never touch the rail going in or out.",
        "• 10 mm rubber buffers fill the 20 mm gaps, so each row",
        "  packs tight between the stops and can't slide.",
    ], title="Why it won't bend and still holds the bins", fs=9.5, lh=4.5)
    sh.save()


def sheet_bin(pdf, n, num, total):
    w = width(n)
    sc = 25
    sh = Sheet(pdf, num, f"Bin, {w:,.0f} wide", f"1:{sc}", total)
    s = 1 / sc
    lab = -10 / s
    parts = cad.bin_parts(n)
    comp = compound(parts)
    pcs = pocket_centres(w)
    fr, _ = project(comp, "front")
    vf = View(sh, fr, s, 40, 82)
    vf.label(w / 2, lab, "FRONT", "Flap side")
    vf.dimh(0, w, -2.5 / s, 0, 0, above=False)
    vf.dimh(36, w - 36, FB + 120, FB, FB, txt=f"{w - 72:,.0f} flap")
    vf.dimh(0, pcs[0], POCKET_Z - 70, None, POCKET_Z, above=False)
    vf.dimh(pcs[0], pcs[1], POCKET_Z - 70, None, POCKET_Z, above=False)
    vf.dimv(0, POCKET_Z, -60, 0, pcs[0] - 100, txt="200")
    vf.dimv(POCKET_Z, POCKET_Z + 100, -60, None, pcs[0] - 100, txt="100")
    vf.dimv(0, FB, -170, 0, 0)
    vf.dimv(0, FTOP_B, -280, None, 36, txt=f"{FTOP_B:,.0f} opening")
    vf.dimv(0, HF, -390, None, 0, txt=f"{HF:,.0f}")

    rt, _ = project(comp, "right")
    vr = View(sh, rt, s, 40 + w * s + 40, 82)
    vr.label(D / 2, lab, "RIGHT SIDE", "Trap door, top-hinged")
    vr.dimh(0, D, -2.5 / s, 0, 0, above=False)
    vr.dimv(0, HB, D + 60, D, D, left=False, txt=f"{HB:,.0f}")
    vr.dimv(DOOR[2], DOOR[3], D + 160, D, D, left=False, txt=f"{DOOR[3] - DOOR[2]:,.0f} door")
    vr.dimv(0, DOOR[2], D + 160, None, None, left=False, txt=f"{DOOR[2]:,.0f}")
    vr.dimh(DOOR[0], DOOR[1], DOOR[3] + 260, DOOR[3], DOOR[3], txt="1,030 door")

    cut = cq.Compound.makeCompound([sld for v in parts.values() for sld in v[0].solids().vals()])
    cutter = cq.Workplane("XY").box(10000, 10000, 10000, centered=False).translate((pcs[1], -5000, -5000)).val()
    sec = cut.cut(cutter)
    sc, _ = project(sec, "right")
    xs = 40 + w * s + 40 + D * s + 48
    vs = View(sh, sc, s, xs, 82)
    vs.label(D / 2, lab, "SECTION A-A", "Through the right fork pocket")
    vs.dimv(POCKET_Z, POCKET_Z + 100, -60, 0, 0, txt="100")
    vs.dimv(0, FLOOR_Z + T, D + 60, D, D, left=False, txt=f"{FLOOR_Z + T} floor")
    vs.note(D / 2, POCKET_Z + 30, "fork pocket", ha="center", fs=8)
    vs.note(-20, FB + 280, "flap", ha="right", fs=8)

    tp, _ = project(comp, "top")
    vt = View(sh, tp, s, 40, 82 + HB * s + 22 + DRIP[0] * s + 14)
    vt.note(w + 12 / s, D / 2, "PLAN", ha="left", fs=10.5, weight="bold", va="center")
    vt.dimv(0, D, w + 60, w, w, left=False, txt=f"{D:,} deep")
    vt.note(w + 12 / s, D / 2 - 4 / s, "lid falls 100 to the front", ha="left", fs=8.5, color=GREY, va="top")

    F, S = flats.bin_flats(n)
    tm = TARE[f"bin{n}"]
    box_text(sh, 255, 268, 150, [
        f"Width {w:,.0f} x {D:,} deep",
        *textwrap.wrap("Used for: " + ", ".join(used_by(n)), 52),
        f"Height {HF:,.0f} front / {HB:,.0f} back, opening {FB:,.0f}-{FTOP_B:,.0f}",
        f"Pocket centres {pcs[1] - pcs[0]:,.0f} (55% of width, 300-1,000)",
        "Walls, floor, lid, flap, door 4 mm",
        "Pockets: 6 mm box, 200 x 100 internal",
        "Copper frames 250 x 150 x 6 at each mouth",
        "Base runners RHS 75 x 50 x 4, door stiffeners RHS 50 x 25 x 3",
        f"Tare ≈ {tm:,.0f} kg (steel, excl. hardware)",
        f"Flat patterns: BB-{int(num) + 10:03d}",
    ], title="Bin data", fs=9.5, lh=4.6)
    sh.save()


def pack(items, W_, H_, gap=12):
    """items: [(w, h, key)] mm on sheet. Shelf pack, returns {key: (x, y)} or None."""
    pos, x, y, rowh = {}, 0, 0, 0
    for w_, h_, k in sorted(items, key=lambda i: -i[1]):
        if x + w_ > W_:
            x, y, rowh = 0, y + rowh + gap, 0
        if y + h_ > H_:
            return None
        pos[k] = (x, y); x += w_ + gap; rowh = max(rowh, h_)
    return pos


def sheet_flats(pdf, F, num, title, total, extra_lines=()):
    for sc in (20, 25, 30, 40, 50, 60):
        s = 1 / sc
        items = [(max(f.size()[0] * s + 14, 1.55 * len(f"{f.code}  {f.name.split(' (')[0]}") + 4), f.size()[1] * s + 22, i)
                 for i, f in enumerate(F)]
        pos = pack(items, 380, 175 if sc < 60 else 175)
        if pos:
            break
    sh = Sheet(pdf, num, title, f"1:{sc}", total)
    a = sh.ax
    for i, f in enumerate(F):
        px, py = pos[i]
        fx0, fy0, fx1, fy1 = f.bbox()
        ox, oy = 20 + px + 10 - fx0 * s, 270 - py - (fy1 - fy0) * s - 10 - fy0 * s
        v = View(sh, [f.outline + [f.outline[0]]] + [h + [h[0]] for h in f.holes], s, ox, oy, lw=0.6)
        for (cx, cy), r in f.circles:
            a.add_patch(plt.Circle(v.t(cx, cy), max(r * s, 0.4), fill=False, ec=INK, lw=0.5))
        for p0, p1, _lab in f.bends:
            a.plot(*zip(v.t(*p0), v.t(*p1)), color=COP, lw=0.7, ls=(0, (4, 2)))
        v.dimh(fx0, fx1, fy0 - 3 / s, fy0, fy0, above=False)
        v.dimv(fy0, fy1, fx0 - 3 / s, fx0, fx0)
        X, Y = v.t(fx0, fy1)
        a.text(X, Y + 1.5, f"{f.code}  {f.name.split(' (')[0]}", fontsize=8, weight="bold", color=INK)
        a.text(X, Y + 5.2, f"{f.t} mm · qty {f.qty}" + (" · bends dashed" if f.bends else ""), fontsize=7.5, color=GREY)
    box_text(sh, 20, 60, 220, [ln for e in extra_lines for ln in textwrap.wrap(e, 118)] + [
        "Outside-dimension nets. Copper dashed lines are bend lines; apply your own bend deductions.",
        "DXF files for every part are in the pack (layers CUT, BEND, TEXT; units mm).",
    ], title="Notes", fs=9.5, lh=4.6)
    sh.save()


def sheet_cutlist(pdf, num, total):
    sh = Sheet(pdf, num, "Cut list and station summary", "NTS", total)
    a = sh.ax
    rows = [("Item", "Qty / stn", "Steel each", "Steel / stn")]
    q = qty_per_station()
    for n in SIZES:
        rows.append((f"Bin {width(n):,.0f} wide", q.get(n, 0), f"{TARE[f'bin{n}']:,.0f} kg", f"{TARE[f'bin{n}'] * q.get(n, 0):,.0f} kg"))
    rows.append(("Hook skid", 1, f"{TARE['skid']:,.0f} kg", f"{TARE['skid']:,.0f} kg"))
    rows.append(("Station, empty (steel)", "", "", f"{TARE['station']:,.0f} kg"))
    y = 268
    a.text(20, y, "Station summary", fontsize=11.5, weight="bold", va="top"); y -= 8
    for r in rows:
        bold = r is rows[0] or r is rows[-1]
        for x, c in zip((20, 110, 140, 175), r):
            a.text(x, y, str(c), fontsize=10, va="top", weight="bold" if bold else "normal", color=INK)
        y -= 5.4
    y -= 6
    a.text(20, y, "Skid sections", fontsize=11.5, weight="bold", va="top"); y -= 8
    F, S = flats.skid_flats()
    for x, c in zip((20, 40, 95, 140, 165, 180), ("Code", "Part", "Section", "Length", "Qty", "Note")):
        a.text(x, y, c, fontsize=9, weight="bold", va="top")
    y -= 5
    for sec in S:
        for x, c in zip((20, 40, 95, 140, 165, 180), (sec.code, sec.name, sec.sect, f"{sec.length:,.0f}", sec.qty, sec.note)):
            a.text(x, y, str(c), fontsize=8.5, va="top")
        y -= 4.5
    y2 = 268
    a.text(250, y2, "Bin sections (per bin)", fontsize=11.5, weight="bold", va="top"); y2 -= 8
    for n in SIZES:
        _F, S = flats.bin_flats(n)
        for sec in S:
            a.text(250, y2, f"{sec.code}  {sec.name}", fontsize=8.5, va="top")
            a.text(330, y2, f"{sec.sect} x {sec.length:,.0f}  qty {sec.qty}", fontsize=8.5, va="top"); y2 -= 4.5
    y2 -= 5
    a.text(250, y2, "Hardware per bin (by others)", fontsize=11.5, weight="bold", va="top"); y2 -= 8
    for nm, qn, nt in flats.bin_hardware(2):
        a.text(250, y2, f"{qn} x {nm}", fontsize=8.5, va="top"); y2 -= 4.5
    a.text(250, y2 - 3, "Full plate and section list with masses: BuildersBins-cut-list-RevB.xlsx", fontsize=9, color=GREY, va="top")
    sh.save()


SHEET_LIST = [("000", "Cover, notes and sheet list"), ("001", "Station general arrangement"), ("010", "Hook skid"),
              ("011", "Kerb rail and bin restraint details")]
SHEET_LIST += [(f"{100 + i:03d}", f"Bin {width(n):,.0f} wide") for i, n in enumerate(SIZES, 1)]
SHEET_LIST += [(f"{110 + i:03d}", f"Bin {width(n):,.0f} flat patterns") for i, n in enumerate(SIZES, 1)]
SHEET_LIST += [("200", "Skid flat patterns"), ("300", "Cut list and station summary")]
SHEETS_INDEX = {num: i + 1 for i, (num, _t) in enumerate(SHEET_LIST)}
TARE = {}


def build(path=f"{OUT}/BuildersBins-fabrication-drawings-RevB.pdf"):
    for n in SIZES:
        F, S = flats.bin_flats(n)
        TARE[f"bin{n}"] = sum(f.mass() * f.qty for f in F) + sum(x.mass() * x.qty for x in S)
    F, S = flats.skid_flats()
    TARE["skid"] = sum(f.mass() * f.qty for f in F) + sum(x.mass() * x.qty for x in S) + 2 * 30
    TARE["station"] = TARE["skid"] + sum(TARE[f"bin{n}"] * k for n, k in qty_per_station().items())
    total = len(SHEET_LIST)
    with PdfPages(path) as pdf:
        sheet_cover(pdf, total); sheet_ga(pdf, total); sheet_skid(pdf, total); sheet_rail(pdf, total)
        for i, n in enumerate(SIZES, 1):
            sheet_bin(pdf, n, f"{100 + i:03d}", total)
        for i, n in enumerate(SIZES, 1):
            F, _S = flats.bin_flats(n)
            sheet_flats(pdf, F, f"{110 + i:03d}", f"Bin {width(n):,.0f} flat patterns", total,
                        [f"Bin {width(n):,.0f} ({', '.join(used_by(n))}): width {width(n):,.0f}. Pocket mouths 200 x 100 with centres at {', '.join(f'{c - T:,.0f}' for c in pocket_centres(width(n)))} from the plate's left edge."])
        F, _S = flats.skid_flats()
        sheet_flats(pdf, F, "200", "Skid flat patterns", total,
                    [f"Deck plate {L:,.0f} x {W:,.0f} is over standard plate size: join over a cross member, full-penetration butt weld."])
        sheet_cutlist(pdf, "300", total)
    return path


if __name__ == "__main__":
    print(build(), TARE)
