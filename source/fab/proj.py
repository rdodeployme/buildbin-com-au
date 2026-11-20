"""Hidden-line projection of cadquery shapes to 2D polylines (for drawings)."""
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
import cadquery as cq

# view name -> (direction towards the viewer, x direction on the sheet)
VIEWS = {
    "front": ((0, -1, 0), (1, 0, 0)),    # looking along +y (bin frame: at the flap)
    "back": ((0, 1, 0), (-1, 0, 0)),
    "right": ((1, 0, 0), (0, 1, 0)),     # looking along -x (bin right side, door)
    "left": ((-1, 0, 0), (0, -1, 0)),
    "top": ((0, 0, 1), (1, 0, 0)),
    "iso": ((1, -1, 0.8), (1, 1, 0)),
    "iso2": ((-1, -1, 0.8), (1, -1, 0)),
}


def _edges(shape):
    out = []
    if shape is None or shape.IsNull():
        return out
    ex = TopExp_Explorer(shape, TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge_s(ex.Current())
        try:
            c = BRepAdaptor_Curve(e)
            d = GCPnts_QuasiUniformDeflection(c, 0.5)
            pts = [(d.Value(i).X(), d.Value(i).Y()) for i in range(1, d.NbPoints() + 1)]
            if len(pts) > 1:
                out.append(pts)
        except Exception:
            pass
        ex.Next()
    return out


def project(shape, view, hidden=False):
    """shape: cq Workplane/Shape/compound. Returns (visible, hidden) lists of polylines in sheet coords."""
    if isinstance(shape, cq.Workplane):
        shape = cq.Compound.makeCompound([v for v in shape.vals() if isinstance(v, cq.Shape)])
    s = shape.wrapped if hasattr(shape, "wrapped") else shape
    d, x = VIEWS[view] if isinstance(view, str) else view
    algo = HLRBRep_Algo()
    algo.Add(s)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*d), gp_Dir(*x))))
    algo.Update()
    algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    vis = _edges(h.VCompound()) + _edges(h.OutLineVCompound()) + _edges(h.Rg1LineVCompound())
    hid = (_edges(h.HCompound()) + _edges(h.OutLineHCompound())) if hidden else []
    return vis, hid


def compound(parts):
    """parts: {name: (wp, ...)} -> one cq.Compound."""
    sh = []
    for v in parts.values():
        sh += [s for s in v[0].solids().vals()]
    return cq.Compound.makeCompound(sh)
