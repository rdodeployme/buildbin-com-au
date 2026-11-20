"""BuildersBins Rev B — fabrication geometry (all dimensions in mm).

Station frame: x along the skid from the rear end (0) to the hook end (6300),
y across the skid with 0 on the centreline (+y = side A), z up from the ground.
Bin frame: x across the bin face (0 = left as you face the flap), y from the
front face (0) to the back face (D), z up from the bin base (sits on the deck).
"""
import json, math, os

CFG = json.load(open("/home/claude/big/model/shares.json"))
G = {k: round(v * 1000, 3) for k, v in CFG["geo"].items()}

# ---- skid ----
L, W = G["L"], G["W"]                    # 6300 x 2450
DECK_NOM = G["deck"]                     # 100 nominal on the spec
SHS = 89                                 # runners and cross-members SHS 89x89
DECK = SHS + 10                          # deck top 99 above ground (SHS 89 + 10 plate)
DECK_T = 10                              # deck plate
RUNNER = (50, 90, 5)                     # RHS w x h x t, two longitudinal runners
RUNNER_Y = 550                           # runner centres at +/-550 (to suit fleet)
XMEM_PITCH = 650                         # cross members (PFC 90) between runners
RAIL = (50, 100, 6)                      # kerb rail RHS w x h x t
REAR_ZONE, HOOK_ZONE = G["rear_zone"], G["hook_zone"]  # 150, 300
X0 = REAR_ZONE                           # first module line
XH = L - HOOK_ZONE                       # last module line (6000)
MOD = G["module"]                        # 585
NMOD = 10
GAP = G["gap"]                           # 20 between bins
CL = G["clear"]                          # 5 to rails
HOOK_Z = 1450                            # hook bar height above deck (to suit fleet)
ROLLER = (140, 200)                      # dia x width

# ---- bins ----
T = 4                                    # plate, all sides
D = round(G["depth"])                    # 1140
HF = G["front_top"] - DECK_NOM               # 1800 bin height at the front (lid front edge)
HB = G["back_top"] - DECK_NOM                # 1900 at the back (ridge side)
FB = G["flap_bot"] - DECK_NOM                # 1100 flap hinge above bin base
POCKET_IN = (200, 100)                   # fork pocket internal w x h
POCKET_T = 6
POCKET_Z = G["pocket_bot"] - DECK_NOM        # 200 pocket underside above bin base
FLOOR_Z = POCKET_Z + POCKET_IN[1] + POCKET_T   # 306 floor plate underside
FLAP_SIDE = 35                           # flap inset each side
FLAP_TOP_GAP = 32                        # flap stops under the drip lip
DRIP = (20, 40)                          # lid overhang in front of the face, drip turn-down
BACK_FOLD = 44
DOOR_OPEN = (75, 1065, 380, 1680)        # trap door opening: y0, y1, z0, z1 (right side)
DOOR = (55, 1085, 360, 1700)             # door leaf (20 lap all round)
FRAME_W, FRAME_T = 25, 6                 # copper frame round pocket mouths (front)
BUFFER = (10, 40)                        # rubber buffer strip thickness, width
STEEL = 7850e-9                          # kg/mm3


def width(n): return n * MOD - GAP
def pocket_centres(w):
    pc = max(300, min(1000, w * 0.55))
    return [w / 2 - pc / 2, w / 2 + pc / 2]


SIDES = CFG["modular"]["sides"]
STREAMS = {s["id"]: s for s in CFG["streams"]}
SIZES = sorted({STREAMS[i]["modules"] for side in SIDES.values() for i in side})


def layout():
    """[(side, stream_id, n, x0)] for the default station layout."""
    out = []
    for side in ("A", "B"):
        k = 0
        for sid in SIDES[side]:
            n = STREAMS[sid]["modules"]
            out.append((side, sid, n, X0 + k * MOD + GAP / 2))
            k += n
    return out


def qty_per_station():
    q = {}
    for _, _, n, _ in layout(): q[n] = q.get(n, 0) + 1
    return q
