"""Cut list / BOM spreadsheet for BuildersBins Rev B."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from params import *
import flats

OUT = "/home/claude/big/fab/out/BuildersBins-cut-list-RevB.xlsx"
HEAD = PatternFill("solid", fgColor="0E1114")
COP = PatternFill("solid", fgColor="C2804F")
HF_ = Font(bold=True, color="FFFFFF")
thin = Border(bottom=Side(style="thin", color="D6DBDF"))


def sheet(wb, title, header, rows, widths, total_cols=None):
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.fill, c.font, c.alignment = HEAD, HF_, Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 30
    for r in rows:
        ws.append(r)
    for i, wd in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = wd
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.border = thin
            if isinstance(c.value, float):
                c.number_format = "#,##0.0"
    ws.freeze_panes = "A2"
    return ws


def build():
    wb = Workbook(); wb.remove(wb.active)
    q = qty_per_station()
    # summary
    rows, tot = [], 0
    for n in SIZES:
        F, S = flats.bin_flats(n)
        m = sum(f.mass() * f.qty for f in F) + sum(s.mass() * s.qty for s in S)
        rows.append([f"Bin {tag(n)}", width(n), q.get(n, 0), round(m, 1), round(m * q.get(n, 0), 1)])
        tot += m * q.get(n, 0)
    F, S = flats.skid_flats()
    sk = sum(f.mass() * f.qty for f in F) + sum(s.mass() * s.qty for s in S) + 60
    rows.append(["Hook skid (incl. ~60 kg rollers)", W, 1, round(sk, 1), round(sk, 1)])
    rows.append(["Station, empty (steel only)", "", "", "", round(tot + sk, 1)])
    ws = sheet(wb, "Summary", ["Item", "Width / mm", "Qty per station", "Steel each / kg", "Steel per station / kg"],
               rows, [34, 12, 15, 16, 20])
    for c in ws[ws.max_row]:
        c.font = Font(bold=True)
    ws.append([]); ws.append(["Masses are steel only from the CAD geometry, excluding welds, paint, hardware and electrics."])
    ws.append(["Default layout. Side A: general 4M, plastic 2M, EPS 1M, cardboard 3M. Side B: timber 6M, rubble 1M, steel 1M, plasterboard 2M."])

    # plates
    prow = []
    for n in SIZES:
        F, _S = flats.bin_flats(n)
        for f in F:
            w_, h_ = f.size()
            prow.append([f.code, f"Bin {tag(n)}", f.name, f.t, round(w_), round(h_), f.qty, q.get(n, 0), f.qty * q.get(n, 0),
                         round(f.mass(), 1), round(f.mass() * f.qty * q.get(n, 0), 1), "Yes" if f.bends else "", f.note])
    F, _S = flats.skid_flats()
    for f in F:
        w_, h_ = f.size()
        prow.append([f.code, "Skid", f.name, f.t, round(w_), round(h_), f.qty, 1, f.qty, round(f.mass(), 1),
                     round(f.mass() * f.qty, 1), "Yes" if f.bends else "", f.note])
    sheet(wb, "Plates (laser cut)", ["Code", "Assembly", "Part", "Thk / mm", "Blank W", "Blank H", "Qty per item",
                                     "Items per station", "Qty per station", "Mass each / kg", "Mass per station / kg",
                                     "Bends", "Note"], prow, [14, 10, 34, 9, 9, 9, 10, 10, 10, 11, 13, 7, 60])
    # sections
    srow = []
    for n in SIZES:
        _F, S = flats.bin_flats(n)
        for s in S:
            srow.append([s.code, f"Bin {tag(n)}", s.name, s.sect, round(s.length), s.qty, q.get(n, 0), s.qty * q.get(n, 0),
                         round(s.kgm, 2), round(s.mass() * s.qty * q.get(n, 0), 1), s.note])
    _F, S = flats.skid_flats()
    for s in S:
        srow.append([s.code, "Skid", s.name, s.sect, round(s.length), s.qty, 1, s.qty, round(s.kgm, 2),
                     round(s.mass() * s.qty, 1), s.note])
    sheet(wb, "Sections (cut list)", ["Code", "Assembly", "Part", "Section", "Length / mm", "Qty per item",
                                      "Items per station", "Qty per station", "kg/m (nominal)", "Mass per station / kg", "Note"],
          srow, [14, 10, 30, 20, 11, 10, 10, 10, 11, 14, 45])
    # hardware
    hrow = []
    for n in SIZES:
        for nm, qn, nt in flats.bin_hardware(n):
            hrow.append([f"Bin {tag(n)}", nm, qn, q.get(n, 0), qn * q.get(n, 0), nt])
    for nm, qn, nt in flats.skid_hardware():
        hrow.append(["Skid", nm, qn, 1, qn, nt])
    sheet(wb, "Hardware (by others)", ["Assembly", "Item", "Qty per item", "Items per station", "Qty per station", "Note"],
          hrow, [10, 52, 11, 11, 12, 48])
    wb.save(OUT)
    return OUT, tot + sk


if __name__ == "__main__":
    print(build())
