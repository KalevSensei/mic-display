"""Dimensioned drawing (PDF, 4 sheets A3) and shaded render (PNG) of stand adapter #1 (md_arm_adapter.py).

Run after md_arm_adapter.py:  scripts/md.ps1 drawing  (Windows)  or  scripts/md.sh drawing  (macOS)
Writes cad/drawings/A10-A12_arm_adapter_drawings.pdf and cad/renders/A10_arm_adapter_on_arm.png.
Everything renders off screen (matplotlib Agg, VTK off-screen); no window opens.
"""
from pathlib import Path
import json, math, sys, textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md_model as M  # noqa: E402
import md_arm_adapter as A  # noqa: E402

CAD = Path(__file__).resolve().parents[1]
V = cq.Vector
INK, THIN, GREY = "#111111", "#333333", "#9a9a9a"
DATE = "2026-11-17"
PREVIEW = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None


# ------------------------------------------------------------------ projection
def project(shape, N, X, hidden=True):
    """Hidden-line projection. N = direction toward the viewer, X = screen right. Returns (visible, hidden) polylines."""
    algo = HLRBRep_Algo()
    algo.Add(shape.wrapped)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*N), gp_Dir(*X))))
    algo.Update(); algo.Hide()
    h = HLRBRep_HLRToShape(algo)

    def lines(comps):
        out = []
        for c in comps:
            if c is None or c.IsNull():
                continue
            for e in cq.Shape.cast(c).Edges():
                n = 2 if e.geomType() == "LINE" else 40
                pts = np.array([[p.x, p.y] for p in e.positions(np.linspace(0, 1, n))])
                out.append(pts)
        return out
    vis = lines([h.VCompound(), h.OutLineVCompound(), h.Rg1LineVCompound()])
    hid = lines([h.HCompound(), h.OutLineHCompound()]) if hidden else []
    return vis, hid


class View:
    def __init__(self, ax, shape, N, X, origin, scale=1.0, hidden=True, label=None):
        self.ax, self.s, self.o = ax, scale, np.array(origin, float)
        self.N, self.X = np.array(N, float), np.array(X, float)
        self.Y = np.cross(self.N, self.X)
        vis, hid = project(shape, N, X, hidden)
        for pl in hid:
            q = self.o + pl * self.s
            ax.plot(q[:, 0], q[:, 1], color=GREY, lw=0.35, ls=(0, (3, 2)))
        for pl in vis:
            q = self.o + pl * self.s
            ax.plot(q[:, 0], q[:, 1], color=INK, lw=0.7, solid_capstyle="round")
        if label:
            bb = np.vstack(vis)
            ax.text(self.o[0] + bb[:, 0].min() * self.s, self.o[1] + bb[:, 1].min() * self.s - 9, label,
                    fontsize=7.5, color=INK, ha="left", va="top", style="italic")

    def p(self, P3):
        """Model point (3D) -> paper point."""
        P3 = np.asarray(P3, float)
        return self.o + self.s * np.array([P3 @ self.X, P3 @ self.Y])


def _txt(ax, x, y, s, rot=0, ha="center", va="bottom", size=6.8):
    ax.text(x, y, s, fontsize=size, rotation=rot, ha=ha, va=va, color=INK,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.2, alpha=0.85))


def dim(ax, a, b, off, text=None, axis="x", fmt="{:.1f}", value=None, scale=1.0):
    """Linear dimension between paper points a, b, measured along paper x or y, drawn `off` mm away."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if axis == "x":
        y = (a[1] if off > 0 else a[1]) + off if abs(a[1] - b[1]) < 1e-6 else max(a[1], b[1]) + off if off > 0 else min(a[1], b[1]) + off
        for p in (a, b):
            ax.plot([p[0], p[0]], [p[1] + np.sign(off) * 0.8, y + np.sign(off) * 1.2], color=THIN, lw=0.3)
        ax.annotate("", (a[0], y), (b[0], y), arrowprops=dict(arrowstyle="<|-|>", lw=0.35, color=THIN, shrinkA=0, shrinkB=0,
                                                              mutation_scale=4))
        val = abs(b[0] - a[0]) / scale if value is None else value
        _txt(ax, (a[0] + b[0]) / 2, y + 0.4, text or fmt.format(val))
    else:
        x = max(a[0], b[0]) + off if off > 0 else min(a[0], b[0]) + off
        for p in (a, b):
            ax.plot([p[0] + np.sign(off) * 0.8, x + np.sign(off) * 1.2], [p[1], p[1]], color=THIN, lw=0.3)
        ax.annotate("", (x, a[1]), (x, b[1]), arrowprops=dict(arrowstyle="<|-|>", lw=0.35, color=THIN, shrinkA=0, shrinkB=0,
                                                              mutation_scale=4))
        val = abs(b[1] - a[1]) / scale if value is None else value
        _txt(ax, x - 0.4, (a[1] + b[1]) / 2, text or fmt.format(val), rot=90, ha="right", va="center")


def note(ax, p, q, text, ha="left"):
    """Leader from a feature point p to the text at q."""
    ax.annotate(text, xy=p, xytext=q, fontsize=6.6, color=INK, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.35, color=THIN, mutation_scale=4, shrinkA=1, shrinkB=0),
                bbox=dict(facecolor="white", edgecolor="none", pad=0.2, alpha=0.85))


def sheet(pdf_pages, title, number, total, part, material, orientation, scale_txt, body, notes=()):
    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(plt.Rectangle((10, 10), 400, 277, fill=False, lw=1.0, color=INK))
    # title block
    x0, y0, w, h = 250, 10, 160, 34
    ax.add_patch(plt.Rectangle((x0, y0), w, h, fill=False, lw=0.8, color=INK))
    for yy in (y0 + 22, y0 + 14, y0 + 7):
        ax.plot([x0, x0 + w], [yy, yy], color=INK, lw=0.4)
    ax.text(x0 + 2, y0 + 28, title, fontsize=10, weight="bold", va="center", color=INK)
    ax.text(x0 + 2, y0 + 18, part, fontsize=7, va="center", color=INK)
    ax.text(x0 + 2, y0 + 10.5, f"Material: {material}    Print: {orientation}", fontsize=6.4, va="center", color=INK)
    ax.text(x0 + 2, y0 + 3.5, f"Mic display, M06 stand adapter #1    mm    scale {scale_txt}    {DATE}    sheet {number}/{total}",
            fontsize=6.4, va="center", color=INK)
    # notes column
    ny = 44 + 6 + 6.5 * len(notes)
    if notes:
        ax.text(252, ny + 4, "Notes", fontsize=7.5, weight="bold", color=INK, va="bottom")
        for i, n in enumerate(notes):
            ax.text(252, ny - 6.5 * i, n, fontsize=6.3, color=INK, va="top", wrap=True)
    body(ax)
    pdf_pages.savefig(fig)
    if PREVIEW:
        fig.savefig(Path(PREVIEW) / f"sheet{number}.png", dpi=110)
    return fig


# ------------------------------------------------------------------ the parts (display on the user's right = -z)
def parts():
    base = A.clamp_base(-1); pad = A.clamp_pad(-1); blk = A.tilt_block()
    return base, pad, blk


GEN = ["General: functional limits for a 0.4 mm PETG print at JHC (MK4S HF0.4, 0.20 mm SPEED).",
       "Untoleranced sizes +-0.3. Sizes marked * are functional; their limits are listed below.",
       "Edges as modelled (no extra chamfers needed). No supports."]


def sheet_assembly(pdf, base, pad, blk, fit):
    def body(ax):
        m = A.display_to_bar(60.0, -1)
        du = M.shell().fuse(M.back()[0]).moved(A.loc(m))
        b12 = blk.moved(A.loc(m))
        bar = cq.Solid.makeBox(150, 30, 15, V(62, -15, -7.5))      # the arm's 30 x 15 bar (a segment), for orientation
        bar = bar.cut(cq.Solid.makeBox(147, 27, 12, V(60, -13.5, -6)))
        asm = cq.Compound.makeCompound([bar, base, pad, b12, du])
        # plan view from above (x to the right = toward the Yeti head; screen up = display side)
        pv = View(ax, asm, (0, 1, 0), (1, 0, 0), (40 - 62 * 0.75, 170), 0.75, hidden=False, label="Seen from above (scale 1:1.33)")
        dim(ax, pv.p((128, 15, 7.5)), pv.p((200, 15, 7.5)), -14, "72: clamp face to head pivot bolt centre", scale=0.75)
        ax.plot(*pv.p((200, 0, 0)), marker="+", ms=8, color=INK, mew=0.6)
        _txt(ax, *(pv.p((200, 0, 0)) + [0, 2.5]), "head pivot bolt", size=6.2)
        dim(ax, pv.p((178, 0, 0)), pv.p((178, 0, -110)), 22, "110 bar centre to display centre", axis="y", scale=0.75)
        note(ax, pv.p((95, 0, 20)), (14, 152), "A11 pad + 2 x M4x10\nset screws (user's left)")
        note(ax, pv.p((110, 0, -50)), (14, 232), "A10 saddle under the bar")
        # iso view
        View(ax, asm, (0.55, 0.55, -0.62), (0.75, 0, 0.66), (130, 70), 0.75, hidden=False, label="Isometric (bar segment for orientation)")
        # tables
        tx, ty = 252, 270
        ax.text(tx, ty, "Printed parts (PETG, MK4S HF0.4, 0.20 mm SPEED profile)", fontsize=7.5, weight="bold", color=INK)
        rows = [("Part", "File (cad/print/)", "Qty", "g sliced", "time")]
        for r in fit.get("slicer", []):
            rows.append(r)
        for i, r in enumerate(rows):
            for j, (c, xo) in enumerate(zip(r, (0, 14, 104, 114, 132))):
                ax.text(tx + xo, ty - 6 - 4.6 * i, c, fontsize=6.2, color=INK, weight="bold" if i == 0 else "normal")
        hy = ty - 14 - 4.6 * len(rows)
        ax.text(tx, hy, "Bought parts", fontsize=7.5, weight="bold", color=INK)
        hw = [("2", "M4x10 set screw, ISO 4026 (flat point), hex socket 2 mm, steel"),
              ("2", "M4 hex nut, ISO 4032 (7 mm across flats, 3.2 thick)"),
              ("1", "M5x25 socket head screw, ISO 4762 (4 mm hex key)"),
              ("1", "M5 nyloc nut, DIN 985 (8 mm across flats, 5 thick)"),
              ("1", "M5 washer, ISO 7089 (10 x 5.3 x 1)")]
        for i, (q, d) in enumerate(hw):
            ax.text(tx, hy - 6 - 4.6 * i, q, fontsize=6.2, color=INK); ax.text(tx + 8, hy - 6 - 4.6 * i, d, fontsize=6.2, color=INK)
        ay = hy - 14 - 4.6 * len(hw)
        ax.text(tx, ay, "Assembly", fontsize=7.5, weight="bold", color=INK)
        steps = ["1  Push the 2 M4 nuts down into the slots in A10's far wall; thread the set screws in from outside.",
                 "2  A12's 2 fingers into A10's 3: M5x25 + washer from the outer finger, nyloc in its hex pocket.",
                 "   Tighten until the display holds any angle against a firm tap (about 1 N m).",
                 "3  Saddle up under the bar, display arm on the user's right, head-side face 72 mm from the",
                 "   head pivot bolt centre. Drop A11 in between bar and far wall, dimples toward the screws.",
                 "4  Set screws finger-tight on the short arm of the 2 mm key (about 0.1 N m). Not more.",
                 "5  Display slides down onto A12's rail until it clicks (MI-1, as on the desk foot)."]
        for i, t in enumerate(steps):
            ax.text(tx, ay - 6 - 4.4 * i, t, fontsize=6.0, color=INK)
    return sheet(pdf, "Stand adapter #1: assembly", 1, 4, "A10 saddle + A11 pad + A12 tilt block on the classmate's arm",
                 "PETG", "see sheets 2-4", "1:1.33 / iso", body,
                 notes=["The display sits beside the Yeti head, on the user's right, facing the user; it tilts -3..103 deg.",
                        "Nothing rises above the bar's top face: the Yeti can fold down onto the bar."])


def sheet_a10(pdf, base):
    def body(ax):
        pv = View(ax, base, (0, 1, 0), (1, 0, 0), (40 - 92, 145), 1.0, label="Seen from above")
        fv = View(ax, base, (0, 0, 1), (1, 0, 0), (40 - 92, 70), 1.0, label="Seen from the arm side (+z)")
        ev = View(ax, base, (1, 0, 0), (0, 0, -1), (225.1, 215), 1.0, label="Seen from the head end")
        # plan view: bar centreline across the U, then the dimensions
        a, b = pv.p((86, 0, 0)), pv.p((190, 0, 0))
        ax.plot([a[0], b[0]], [a[1], b[1]], color=THIN, lw=0.3, ls=(0, (8, 2, 1, 2)))
        dim(ax, pv.p((92, 0, 25.1)), pv.p((128, 0, 25.1)), -6, "36 *")
        dim(ax, pv.p((98, 0, -18.1)), pv.p((122, 0, -18.1)), 12, "24")
        dim(ax, pv.p((92, 0, 25.1)), pv.p((98, 0, -117.8)), -8, axis="y", value=142.9)
        dim(ax, pv.p((92, 0, 25.1)), pv.p((92, 0, -18.1)), -18, axis="y", value=43.2)
        dim(ax, pv.p((185, 0, -102.2)), pv.p((185, 0, -117.8)), 6, "15.6", axis="y")
        note(ax, pv.p((183, 0, -116.3)), (166, 276), "3 fingers 3.0 thick, 2 slots 3.3 * wide")
        dim(ax, pv.p((185, 0, 0)), pv.p((185, 0, -110)), 22, "110 bar centreline to display centre", axis="y")
        note(ax, pv.p((122, 0, 20)), (98, 105), "2 x M4 set-screw holes, dia 4.5 thru the far wall,\n24 apart, 6 in from each end, centred 20 above the bottom")
        # front view (from +z)
        dim(ax, fv.p((92, -20, 25)), fv.p((92, 14.5, 25)), -8, axis="y", value=34.5)
        dim(ax, fv.p((92, -20, 25)), fv.p((92, -15.05, 25)), -16, "5 floor", axis="y")
        dim(ax, fv.p((178, -20, 0)), fv.p((178, -12.5, 0)), 14, "7.5", axis="y")
        dim(ax, fv.p((122, -20, 0)), fv.p((122, -8, 0)), 4, "12", axis="y")
        dim(ax, fv.p((128, -20, 0)), fv.p((178, -20, 0)), -4, "50 to axis")
        note(ax, fv.p((178 + 5.3 / 2 * 0.7, -12.5 + 5.3 / 2 * 0.7, 0)), fv.p((200, 12, 0)), "axis dia 5.3* thru,\nknuckle R7.5, slots R17.5")
        note(ax, fv.p((172, -20, 0)), fv.p((205, -26, 0)), "45 deg print ramp")
        # end view (from +x, display side to the right)
        dim(ax, ev.p((0, 14.5, 15.1)), ev.p((0, 14.5, -7.6)), 6, "22.7 * (bar 15 + pad 6 + gaps)")
        dim(ax, ev.p((0, -20, 25.1)), ev.p((0, -20, 15.1)), -6, "10")
        dim(ax, ev.p((0, -20, -8.1)), ev.p((0, -20, -18.1)), -6, "10")
        note(ax, ev.p((0, 12.25, -7.6)), (255, 250), "contact strips 2.5 wide, 0.5 high,\nat 11..13.5 above/below the bar centre *")
        note(ax, ev.p((0, 8, 18.7)), (195, 262), "M4 nut slot 7.2 * wide, 3.4 * deep,\nfrom the top down to the screw axis", ha="right")
    return sheet(pdf, "A10 clamp saddle", 2, 4, "A10_PETG_arm_clamp_base_display_right (left = mirror)", "PETG",
                 "bottom face (floor) on the bed, U open upward", "1:1", body,
                 notes=GEN + ["* U inner width 22.7 +0.3/-0.1: bar 15.0 + pad 6.0 + 1.0 travel + 0.1 + 0.1 gaps; bar must drop in.",
                              "* Axis hole 5.3 +0.3/-0.1 (M5 must pass); slots 3.3 +0.2/-0.05 (A12 fingers 3.0 must enter).",
                              "* Nut slots 7.2 +0.3/-0.05 across flats (M4 nut 7.0 must drop in and not turn).",
                              "* Strips: the bar must touch only the strips; file the relief if it touches in the middle.",
                              "Wall tops end 0.5 below the bar's top face: never raise them.",
                              "Drawn: right-hand version (display on the user's right). The left-hand file is its mirror image."])


def sheet_a11_a12(pdf, pad, blk):
    def body(ax):
        # A11 pad (left-built geometry is the same part): face view and edge view, 2:1
        p1 = A.clamp_pad(1)
        fv = View(ax, p1, (0, 0, -1), (-1, 0, 0), (40 + 128 * 2, 205), 2.0, label="A11 pad, seen from the screw side (2:1)")
        ev = View(ax, p1, (1, 0, 0), (0, 0, -1), (165 + (-7.6) * 2, 205), 2.0, label="A11 edge (2:1)")
        dim(ax, fv.p((128, -15, -14.1)), fv.p((92, -15, -14.1)), -8, "36", scale=2)
        dim(ax, fv.p((128, -15, -14.1)), fv.p((128, 14.5, -14.1)), -8, "29.5", axis="y", scale=2)
        dim(ax, fv.p((122, 0, -14.1)), fv.p((98, 0, -14.1)), 0, "24", scale=2)
        note(ax, fv.p((98, 0, -14.1)), fv.p((80, 18, -14.1)), "2 x dimple dia 4.6 x 0.6 deep,\ncentred 15 above the bottom edge")
        dim(ax, ev.p((0, -15, -7.6)), ev.p((0, -15, -14.1)), -8, "6.5 (6 + 0.5 strip)", scale=2)
        dim(ax, ev.p((0, 11, -7.6)), ev.p((0, 13.5, -7.6)), -4, "2.5", axis="y", scale=2)
        dim(ax, ev.p((0, -15, -7.6)), ev.p((0, 11, -7.6)), -12, "26", axis="y", scale=2)
        # A12 tilt block (display frame): rail face, side, top; 2:1
        rv = View(ax, blk, (0, 0, 1), (1, 0, 0), (75, 85), 2.0, label="A12, rail face (2:1)")
        sv = View(ax, blk, (1, 0, 0), (0, 0, -1), (160, 85), 2.0, label="A12 side (2:1)")
        dim(ax, rv.p((-13, -14, 0)), rv.p((13, -14, 0)), -8, "26", scale=2)
        dim(ax, rv.p((-13, -14, 0)), rv.p((-13, 16, 0)), -8, "30 (MI-1 rail length)", axis="y", scale=2)
        dim(ax, sv.p((0, 16, -15.9)), sv.p((0, 16, -19.9)), 4, "4", scale=2)
        dim(ax, sv.p((0, -14, -19.9)), sv.p((0, -14, -27.9)), -8, "8 to axis", scale=2)
        dim(ax, sv.p((0, -14, -27.9)), sv.p((0, 0, -27.9)), 10, "14", axis="y", scale=2)
        note(ax, sv.p((0, 7.5 * 0.7, -27.9 - 7.5 * 0.7)), sv.p((0, 26, -55)), "2 fingers 3.0 * thick, 3.3 apart;\nR7.5, axis dia 5.3 * thru, 45 deg ramp")
        note(ax, rv.p((0, 2, -13.15)), rv.p((24, 22, 0)), "male MI-1 rail = md_model.rail_local():\nfixed, identical to the desk foot A00")
    return sheet(pdf, "A11 pressure pad, A12 tilt block", 3, 4, "A11_PETG_arm_clamp_pad, A12_PETG_arm_MI1_tilt_block", "PETG",
                 "A11 flat, dimples down; A12 standing on its rail's bottom end", "2:1", body,
                 notes=GEN + ["* A12 fingers 3.0 -0.2/+0.05 (must enter A10's 3.3 slots).",
                              "* MI-1 rail: as printed for the desk foot. Never change it (md_model.py MI dict).",
                              "A11 can be printed with either face down; dimples face the set screws."])


def sheet_checks(pdf, fit):
    def body(ax):
        ax.text(20, 270, "Fit checks against the classmate's arm CAD (cad/checks/arm_adapter_fit_check.json)", fontsize=9,
                weight="bold", color=INK)
        y = 262
        for c in fit["checks"]:
            line = ("PASS  " if c["ok"] else "FAIL  ") + c["check"] + (f"  [{c['detail']}]" if c.get("detail") else "")
            for k, part in enumerate(textwrap.wrap(line, 250, subsequent_indent="          ")):
                ax.text(20, y, part, fontsize=5.6, color=INK if c["ok"] else "#b00020")
                y -= 3.4
            if y < 60:
                ax.text(20, y, "... (full list in the JSON)", fontsize=5.6, color=INK)
                break
        ax.text(20, 52, "Still to check on the real arm (cannot be settled in CAD):", fontsize=7.5, weight="bold", color=INK)
        todo = ["Bar outside 30.0 x 15.0 (calipers) and its outer corner radius (the strips assume <= 1.5).",
                "Bar material (aluminium assumed); then the set-screw torque that holds without marking it.",
                "The user's seat, eye height and distance against the 390 mm reading distance used here.",
                "The Yeti's side knobs and the real cable route of the display's USB-C lead.",
                "Grip after a week: re-snug the set screws once if the adapter has crept."]
        for i, t in enumerate(todo):
            ax.text(20, 46 - 4.4 * i, "- " + t, fontsize=6.4, color=INK)
    return sheet(pdf, "Stand adapter #1: checks", 4, 4, "CAD fit checks and the physical checks still open", "-", "-", "-", body)


def make_pdf(fit):
    base, pad, blk = parts()
    out = CAD / "drawings"; out.mkdir(exist_ok=True)
    f = out / "A10-A12_arm_adapter_drawings.pdf"
    with PdfPages(f) as pdf:
        for fn in (lambda: sheet_assembly(pdf, base, pad, blk, fit), lambda: sheet_a10(pdf, base),
                   lambda: sheet_a11_a12(pdf, pad, blk), lambda: sheet_checks(pdf, fit)):
            fig = fn(); plt.close(fig)
        d = pdf.infodict(); d["Title"] = "Mic display M06 stand adapter #1 drawings"; d["Subject"] = "A10 A11 A12"
    return f


# ------------------------------------------------------------------ shaded render (VTK, off screen)
def render(path, beta=-19.57):
    import vtk
    arm = A.load_arm()
    base, pad, blk = parts()
    hb = A.head_to_bar(beta)
    # reading tilt for this bar angle: glass normal toward the nominal eye
    e = (hb @ np.array([160.0, 355.0, 0.0, 1.0]))[:3]
    best = min(np.arange(A.PITCH[0], A.PITCH[1] + 0.01, 1.0),
               key=lambda eps: -np.dot(e - A.display_to_bar(float(eps), -1)[:3, 3], A.display_to_bar(float(eps), -1)[:3, 2])
               / np.linalg.norm(e - A.display_to_bar(float(eps), -1)[:3, 3]))
    m = A.display_to_bar(float(best), -1)
    to_world = np.linalg.inv(hb)      # bar frame -> head frame (level), so the picture is upright
    items = [(arm["bar"], np.eye(4), (0.72, 0.73, 0.75)), (base, np.eye(4), (0.16, 0.36, 0.62)), (pad, np.eye(4), (0.16, 0.36, 0.62)),
             (blk, m, (0.16, 0.36, 0.62)), (M.shell(), m, (0.12, 0.12, 0.13)), (M.back()[0], m, (0.12, 0.12, 0.13)),
             (A.hardware(-1), np.eye(4), (0.55, 0.55, 0.58))]
    for h in A.head_group(arm, 0.0):
        items.append((h.shape, hb @ h.m, (0.80, 0.80, 0.82) if "Yeti" in h.name else (0.70, 0.71, 0.73)))
    # glass face as a dark disc
    glass = cq.Solid.makeCylinder(M.B["glass_d"] / 2 - 2.2, 0.05, V(0, 0, M.B["glass_front"]), V(0, 0, 1))
    items.append((glass, m, (0.02, 0.05, 0.10)))
    ren = vtk.vtkRenderer(); ren.SetBackground(1, 1, 1)
    for shp, mm, col in items:
        vs, ts = shp.moved(A.loc(to_world @ mm)).tessellate(0.1, 0.2)
        pts = vtk.vtkPoints()
        for v in vs:
            pts.InsertNextPoint(v.x, v.y, v.z)
        polys = vtk.vtkCellArray()
        for t in ts:
            polys.InsertNextCell(3); [polys.InsertCellPoint(i) for i in t]
        pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(polys)
        nrm = vtk.vtkPolyDataNormals(); nrm.SetInputData(pd); nrm.SetFeatureAngle(35); nrm.SplittingOn(); nrm.Update()
        mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nrm.GetOutputPort())
        ac = vtk.vtkActor(); ac.SetMapper(mp); ac.GetProperty().SetColor(*col)
        ac.GetProperty().SetSpecular(0.25); ac.GetProperty().SetSpecularPower(25); ac.GetProperty().SetAmbient(0.15)
        ren.AddActor(ac)
    cam = ren.GetActiveCamera()
    focal = (to_world @ np.append(m[:3, 3], 1))[:3] * 0.5 + np.array([0, 110, 0]) * 0.5
    cam.SetFocalPoint(*focal)
    cam.SetPosition(*(focal + np.array([560, 300, -500])))
    cam.SetViewUp(0, 1, 0); cam.SetViewAngle(23)
    ren.ResetCameraClippingRange()
    lk = vtk.vtkLightKit(); lk.AddLightsToRenderer(ren)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.SetShowWindow(False); rw.SetMultiSamples(8)
    rw.AddRenderer(ren); rw.SetSize(2400, 1600); rw.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(str(path)); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
    rw.Finalize()
    return best


def main():
    fit = json.loads((CAD / "checks" / "arm_adapter_fit_check.json").read_text())
    sl = CAD / "print" / "slice_summary_arm_adapter.json"
    if sl.exists():
        fit["slicer"] = [tuple(r) for r in json.loads(sl.read_text())["table"]]
    if "--render-only" not in sys.argv:
        f = make_pdf(fit)
        print("wrote", f)
    if "--no-render" not in sys.argv:
        r = CAD / "renders" / "A10_arm_adapter_on_arm.png"
        eps = render(r)
        print("wrote", r, "display tilt", eps)


if __name__ == "__main__":
    main()
