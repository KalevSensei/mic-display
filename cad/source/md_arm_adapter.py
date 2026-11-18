"""Stand adapter #1: holds the display unit (MI-1 dovetail) on the classmate's microphone arm.

Three printed parts (PETG) plus common hardware:
  A10 clamp saddle: a U under the upper arm bar, its walls ending 0.5 mm below the bar's top face, plus the outrigger
      arm and 3-finger tilt knuckle. Nothing sits on top of the bar: in the head joint's end pose (bar 28.5 deg down
      toward the head) with the Yeti tipped back 55-62 deg, the Yeti lies 1.3-4 mm above the bar's top face.
  A11 pressure pad between the bar and the U's far wall; 2 x M4 set screws in captive nuts push it against the bar
  A12 tilt block: the male MI-1 rail (identical to md_model.rail_local) on one face, 2 knuckle fingers on the other.
The display unit (D01 + D02, md_model.py) slides down onto A12's rail and clicks in, exactly as on the desk foot.

Frames (mm)
  bar frame = the arm bar's own part frame (P03_Varsiputki_2palkki_v2): x along the bar, +x toward the head pivot
  (head pivot hole at x = +200, elbow pivot hole at x = -200); y = the bar's 30 mm side (in the arm's plane,
  "up" when the bar is level); z = the bar's 15 mm side (perpendicular to the arm's plane).
  The bar is a 30 x 15 x 1.5 rectangular tube, 424 long, centred on the origin.
  display frame = md_model.py: X right, Y up on the glass, Z toward the viewer, origin = screen centre.
  head frame = level, origin at the head pivot, x toward the user (along the arm), y up, z = bar z.
  A-frame = the arm's own plane frame (Eino's assembly turned by its 5.49 deg base swivel): x away from the
  base along the arm, y up (desk top at y = 0), z across the arm.

The classmate's arm geometry is read from STEP copies of his SolidWorks Pack and Go
(cad/reference/arm_eino_step/, git-ignored; exported from Eino's SolidWorks files as STEP, see AGENTS.md).

Run:  scripts/md.ps1 arm  (Windows)  or  scripts/md.sh arm  (macOS)
Writes cad/print/A1*.{step,stl,3mf}, cad/print/MD_plate_display_and_arm_clamp.3mf (D01 + D02 + clamp),
cad/print/MD_plate_arm_clamp.3mf (clamp only), cad/print/manifest_arm_adapter.json,
cad/assembly/arm_adapter_on_bar.step and cad/checks/arm_adapter_fit_check.json; exit 1 on a failed check.
Needs md_model.py's D01/D02 exports in cad/print (run md_model.py first).
"""
from pathlib import Path
import json, math, sys, time, zipfile

import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf, gp_Pnt, gp_Dir, gp_Lin
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md_model as M  # noqa: E402  (display unit + MI-1, never changed here)

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad"
ARM = CAD / "reference" / "arm_eino_step"
V = cq.Vector

# ------------------------------------------------------------------ the classmate's arm (read from his CAD)
BAR = dict(h=30.0, t=15.0, wall=1.5, half_len=212.0,
           holes_43=[-40.0, -20.0, 0.0, 15.0, 35.0, 55.0, 75.0],   # spring-plug holes, through both 30-wide walls
           holes_64=[-200.0, 160.0, 200.0])                        # pivot / elbow bolt holes
P11_ORIGINS = [-40.0, -20.0, 15.0, 35.0, 55.0]   # every hole pair the spring plug P11 can be bolted to (CAD: -20)
P11_CAD_UPPER = -20.0
ARMK = dict(
    shoulder=(0.0, 76.0),          # A-frame, lower bar pivot in P02
    lower_cad=32.40, upper_cad=-19.57,   # bar angles in the CAD pose (deg, A-frame)
    elbow_ext=36.0,                # upper pivot = 36 mm beyond the lower bar's +200 hole (P04)
    lever=(36.0, 40.0),            # upper springs' hook hole on P04 (elbow frame)
    p02_hook=(-16.0, 110.0),       # lower springs' hook hole on P02 (A-frame)
    p06_pivot=56.0, p09_offset=239.0,
    spring_w=26.3, spring_r=11.3,  # springs run 26.3 mm either side of the arm plane, coil outer radius 11.3
    head_beta_min=-28.5,           # P05 fork stops the bar descending more than 28.5 deg toward the level head
    tilt_max=80.0,                 # P06 (Yeti tilt) free +-80 deg about its pivot before it hits P05
    swivel=5.4858,                 # base swivel in Eino's CAD pose (desk parts only)
)

# ------------------------------------------------------------------ adapter parameters (bar frame)
CL = dict(x0=92.0, x1=128.0,                 # clamp spans 92..128: 72 mm behind the head pivot hole, 14.85 mm clear of the 75 hole's edge
          y_bot=-20.0, floor_top=-15.05,     # floor under the bar (the bar rests on it)
          y_top=14.5,                        # walls end 0.5 below the bar's top face (y = 15): the top stays free
          wall_fix=(7.6, 8.1, 18.1),         # display-side wall: contact strips at z 7.6 (0.1 off the bar), relieved face 8.1, outer 18.1
          pad=(-7.6, -8.1, -14.1),           # pad: strips at -7.6, body -8.1..-14.1 (6 thick), outer face -14.1
          wall_scr=(-15.1, -25.1),           # set-screw wall: inner face (1.0 travel gap to the pad), outer face
          strip=(11.0, 13.5),                # contact strips on |y| 11..13.5: right next to the bar's 1.5 mm top/bottom walls
          screw_x=(98.0, 122.0), screw_y=0.0, screw_hole=4.5,
          nut_af=7.2, nut_z=(-17.0, -20.4),  # M4 nut pocket (ISO 4032 7.0 AF + 0.2, 3.2 + 0.2 thick), nut dropped in from the top
          dimple=(4.6, 0.6),                 # screw-tip dimples on the pad's outer face (keep the pad on the screws)
          stub_x=(98.0, 122.0), stub_top=-8.0)  # outrigger arm: 24 x 12 mm, bottom on the bed
# tilt axis runs along z through (178, -12.5); the display centre sits wd = 110 mm from the arm plane. That keeps the sight
# lines from the user's eye to the glass outside the Yeti cradle's base plate, also with the Yeti tilted 20 deg
# (58 mm hid 40-50 % of the glass, 100 mm up to 12 % at a 20 deg Yeti tilt).
_wd = 110.0
KN = dict(axis=(178.0, -12.5), wd=_wd,
          fingers=[(_wd - 7.8, _wd - 4.8), (_wd - 1.5, _wd + 1.5), (_wd + 4.8, _wd + 7.8)],   # 3 x 3.0 on A10
          slots=[(_wd - 4.8, _wd - 1.5), (_wd + 1.5, _wd + 4.8)],                               # 2 x 3.3 for A12's fingers
          r=7.5, hole=5.3, slot_r=17.5, sector=(171.0, 315.0), r_out=42.0,
          boss=(_wd - 12.8, _wd - 7.8), boss_r=6.5, nyloc_af=8.15, nyloc_depth=4.5)
RB = dict(xw=13.0, y0=M.MI["y_stop"] - M.MI["rail_len"], y1=M.MI["y_stop"], t=4.0, e=8.0,
          fingers=[(1.65, 4.65), (-4.65, -1.65)])
RB["z_back"] = M.P["back_z"] - RB["t"]                 # -19.9
RB["z_axis"] = RB["z_back"] - RB["e"]                  # -27.9 (display centre is 27.9 in front of the tilt axis)
PITCH = (-3.0, 103.0)   # usable tilt range: glass normal angle above the bar's x axis, in the arm plane
USB = dict(w=13.0, h=7.5, z=(sum(M.B["usb_z"]) / 2), length=30.0)   # plug overmold + strain relief envelope
HW = {  # every bought part; sizes checked in main()
    "M4x10 set screw (grub screw) ISO 4026, flat point, hex socket": 2, "M4 hex nut ISO 4032": 2,
    "M5x25 socket head ISO 4762": 1, "M5 nyloc nut DIN 985": 1, "M5 washer ISO 7089": 1,
}

# ------------------------------------------------------------------ helpers
def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_y(r, x, z, y0, y1):
    return cq.Solid.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def cyl_z(r, x, y, z0, z1):
    return cq.Solid.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))


def hex_y(af, x, z, y0, y1):
    """Hex prism along y, flats facing +-z."""
    R = af / math.sqrt(3)
    pts = [(R, 0), (R / 2, af / 2), (-R / 2, af / 2), (-R, 0), (-R / 2, -af / 2), (R / 2, -af / 2)]
    w = cq.Workplane("XZ", origin=(0, y0, 0)).polyline([(x + a, z + b) for a, b in pts]).close().extrude(-(y1 - y0))
    return w.val()


def hex_z(af, x, y, z0, z1):
    """Hex prism along z, flats facing +-y (prints with a flat on top when y is up)."""
    R = af / math.sqrt(3)
    pts = [(R, 0), (R / 2, af / 2), (-R / 2, af / 2), (-R, 0), (-R / 2, -af / 2), (R / 2, -af / 2)]
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline([(x + a, y + b) for a, b in pts]).close().extrude(z1 - z0).val()


def pol(c, r, deg):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def mat(R=np.eye(3), t=(0, 0, 0)):
    m = np.eye(4); m[:3, :3] = R; m[:3, 3] = t
    return m


def rz(deg, about=(0, 0)):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    p = np.array([about[0], about[1], 0.0])
    return mat(R, p - R @ p)


def ry(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return mat(np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]))


def tr(x, y, z=0.0):
    return mat(np.eye(3), (x, y, z))


def loc(m):
    T = gp_Trsf()
    T.SetValues(*[float(m[i, j]) for i in range(3) for j in range(4)])
    return cq.Location(T)


class Posed:
    """A shape with a 4x4 placement; conservative world AABB from its local box corners."""
    def __init__(self, name, shape, m=None):
        self.name, self.shape, self.m = name, shape, (np.eye(4) if m is None else m)
        b = shape.BoundingBox()
        self.corners = np.array([[x, y, z, 1.0] for x in (b.xmin, b.xmax) for y in (b.ymin, b.ymax) for z in (b.zmin, b.zmax)])

    def at(self, m):
        p = Posed.__new__(Posed); p.name, p.shape, p.corners = self.name, self.shape, self.corners; p.m = m @ self.m
        return p

    def aabb(self):
        w = (self.m @ self.corners.T).T[:, :3]
        return w.min(0), w.max(0)

    def solid(self):
        return self.shape.moved(loc(self.m))


def overlap(a, b, pad=0.0):
    a0, a1 = a.aabb(); b0, b1 = b.aabb()
    if np.any(a1 + pad < b0) or np.any(b1 + pad < a0):
        return 0.0
    try:
        return a.solid().intersect(b.solid()).Volume()
    except Exception:
        return -1.0


def dist(a, b):
    d = BRepExtrema_DistShapeShape(a.solid().wrapped, b.solid().wrapped)
    d.Perform()
    return d.Value() if d.IsDone() else -1.0


# ------------------------------------------------------------------ A10 clamp base (display on the +z side; mirrored for the other side)
def tangent_to_bed(r, deg):
    """Point on the circle (axis, r) at deg and where its 45 deg print ramp (the tangent there) meets the bed."""
    p = pol(KN["axis"], r, deg)
    a = math.radians(deg)
    t = (p[1] - CL["y_bot"]) / math.cos(a)
    return p, (p[0] + t * math.sin(a), CL["y_bot"])


def plate_profile():
    ax = KN["axis"]; r = KN["r"]; s0, s1 = KN["sector"]
    yb = CL["y_bot"]
    p_lo, bed_front = tangent_to_bed(r, s1)
    p171 = pol(ax, r, s0)
    p171o = pol(ax, KN["r_out"], s0)
    mid = pol(ax, r, (s1 + s0 + 360) / 2)
    sx0, sx1 = CL["stub_x"]
    w = (cq.Workplane("XY").moveTo(sx0, yb).lineTo(*bed_front).lineTo(*p_lo)
         .threePointArc(mid, p171).lineTo(*p171o).lineTo(sx1, CL["stub_top"]).lineTo(sx0, CL["stub_top"]).close())
    return w


def clamp_base(side=1):
    x0, x1 = CL["x0"], CL["x1"]
    zfs, zfr, zfo = CL["wall_fix"]
    zsi, zso = CL["wall_scr"]
    s0, s1 = CL["strip"]
    b = box(x0, x1, CL["y_bot"], CL["y_top"], zso, zfo)
    b = b.cut(box(x0 - 1, x1 + 1, CL["floor_top"], CL["y_top"] + 1, zsi, zfr))            # the U
    for sg in (-1, 1):                                                                     # contact strips on the fixed wall
        y0, y1 = sorted((sg * s0, sg * s1))
        b = b.fuse(box(x0, x1, y0, y1, zfs, zfr + 0.01))
    # outrigger: arm from the fixed wall out to the knuckle plate, plate forward to the tilt knuckle
    zf0, zf1 = KN["fingers"][0][0], KN["fingers"][-1][1]
    stub = box(*CL["stub_x"], CL["y_bot"], CL["stub_top"], zfo - 0.01, zf0 + 0.01)
    plate = plate_profile().extrude(zf1 - zf0).val().translate(V(0, 0, zf0))
    b = b.fuse(stub).fuse(plate)
    ax = KN["axis"]
    # nyloc boss on the inner finger: disc + a foot inside the free sector down to the bed
    bz0, bz1 = KN["boss"]
    boss = cyl_z(KN["boss_r"], ax[0], ax[1], bz0, bz1 + 0.01)
    p_a = pol(ax, KN["boss_r"], 180.0)
    p_b, p_bed = tangent_to_bed(KN["boss_r"], KN["sector"][1])
    foot_pts = [p_a, (p_a[0], CL["y_bot"]), p_bed, p_b, ax]
    foot = cq.Workplane("XY", origin=(0, 0, bz0)).polyline(foot_pts).close().extrude(bz1 - bz0 + 0.01).val()
    b = b.fuse(boss).fuse(foot)
    for (a0, a1) in KN["slots"]:
        b = b.cut(cyl_z(KN["slot_r"], ax[0], ax[1], a0, a1))
    b = b.cut(cyl_z(KN["hole"] / 2, ax[0], ax[1], bz0 - 1, zf1 + 1))
    b = b.cut(hex_z(KN["nyloc_af"], ax[0], ax[1], bz0 - 0.01, bz0 + KN["nyloc_depth"]))
    # set screws: clearance holes through the far wall, captive nuts dropped in through slots from the wall's top face
    nz0, nz1 = sorted(CL["nut_z"])
    af = CL["nut_af"]; R = af / math.sqrt(3)
    for xs in CL["screw_x"]:
        b = b.cut(cq.Solid.makeCylinder(CL["screw_hole"] / 2, zsi - zso + 2, V(xs, CL["screw_y"], zso - 1), V(0, 0, 1)))
        hexp = [(xs + af / 2, CL["screw_y"] + R / 2), (xs, CL["screw_y"] + R), (xs - af / 2, CL["screw_y"] + R / 2),
                (xs - af / 2, CL["screw_y"] - R / 2), (xs, CL["screw_y"] - R), (xs + af / 2, CL["screw_y"] - R / 2)]
        b = b.cut(cq.Workplane("XY", origin=(0, 0, nz0)).polyline(hexp).close().extrude(nz1 - nz0).val())   # flats face +-x
        b = b.cut(box(xs - af / 2, xs + af / 2, CL["screw_y"], CL["y_top"] + 1, nz0, nz1))             # insertion slot
    b = b.clean()
    if side < 0:
        b = b.mirror("XY")
    return b


def clamp_pad(side=1):
    """A11 in its place on the bar (on the side away from the display)."""
    x0, x1 = CL["x0"], CL["x1"]
    zs, zr, zo = CL["pad"]
    s0, s1 = CL["strip"]
    c = box(x0, x1, CL["floor_top"] + 0.05, CL["y_top"], zo, zr)
    for sg in (-1, 1):
        y0, y1 = sorted((sg * s0, sg * s1))
        c = c.fuse(box(x0, x1, y0, y1, zr - 0.01, zs))
    d, h = CL["dimple"]
    for xs in CL["screw_x"]:
        c = c.cut(cq.Solid.makeCylinder(d / 2, h + 0.01, V(xs, CL["screw_y"], zo - 0.01), V(0, 0, 1)))
    c = c.clean()
    return c.mirror("XY") if side < 0 else c


# ------------------------------------------------------------------ A12 tilt block (display frame)
def finger_profile_yz():
    zc, r = RB["z_axis"], KN["r"]
    zb = RB["z_back"]
    tz, ty = zc - r / math.sqrt(2), -r / math.sqrt(2)          # tangent point of the 45 deg print ramp
    c = tz + ty                                               # ramp line z + y = c
    y_bed = RB["y0"]
    return [(y_bed, zb), (y_bed, c - y_bed), (ty, tz)], (0.0, zc - r), (r, zc), (r, zb)


def tilt_block():
    b = box(-RB["xw"], RB["xw"], RB["y0"], RB["y1"], RB["z_back"], M.P["back_z"])
    b = b.fuse(M.rail_local())
    pts, mid, top, top_back = finger_profile_yz()
    for (a0, a1) in RB["fingers"]:
        w = (cq.Workplane("YZ", origin=(a0, 0, 0)).moveTo(*pts[0]).lineTo(*pts[1]).lineTo(*pts[2])
             .threePointArc(mid, top).lineTo(*top_back).close().extrude(a1 - a0))
        b = b.fuse(w.val())
    b = b.cut(cq.Solid.makeCylinder(KN["hole"] / 2, 2 * RB["xw"], V(-RB["xw"], 0, RB["z_axis"]), V(1, 0, 0)))
    return b.clean()


def hardware(side=1):
    """Hinge bolt head, washer, the protruding nyloc nut and bolt tip (bar frame), for the collision sweeps.
    The set screws sit 1.6 mm inside the far wall, so nothing of them sticks out."""
    hw = []
    ax = KN["axis"]; zt = KN["fingers"][-1][1]; bz0 = KN["boss"][0]
    hw += [cyl_z(5.0, ax[0], ax[1], zt, zt + 1.0), cyl_z(4.25, ax[0], ax[1], zt + 1.0, zt + 6.0),   # M5 washer 10 x 1, head 8.5 x 5
           cyl_z(4.6, ax[0], ax[1], bz0 + KN["nyloc_depth"] - 5.0, bz0), cyl_z(2.5, ax[0], ax[1], zt + 1.0 - 25.0, bz0)]
    s = hw[0]
    for h in hw[1:]:
        s = s.fuse(h)
    return s.mirror("XY") if side < 0 else s


def usb_plug():
    """Envelope of a USB-C plug in the display's bottom opening (display frame)."""
    r = M.P["od"] / 2
    return box(-USB["w"] / 2, USB["w"] / 2, -r - USB["length"], -r + 2.0, USB["z"] - USB["h"] / 2, USB["z"] + USB["h"] / 2)


def display_to_bar(eps, side=1):
    """4x4 placing display-frame shapes on the bar: glass normal at eps deg above the bar's x axis."""
    a = math.radians(eps)
    n = np.array([math.cos(a), math.sin(a), 0.0])
    yv = np.array([-math.sin(a), math.cos(a), 0.0])
    xv = np.array([0.0, 0.0, -1.0])
    ax = np.array([KN["axis"][0], KN["axis"][1], side * KN["wd"]])
    o = ax + (-RB["z_axis"]) * n
    return mat(np.column_stack([xv, yv, n]), o)


# ------------------------------------------------------------------ arm parts
def load_arm():
    names = {"bar": "P03_Varsiputki_2palkki_v2", "p02": "P02_Kaantojalka_2palkki_v2", "p04": "P04_Kyynarnivel_2palkki_v2",
             "p05": "P05_Paa_2palkki_v2", "p06": "P06_Kallistuspala_2palkki_v2", "p11": "P11_Jousitulppa_30x15",
             "p19": "P19_Yeti_sanka_v2", "p09": "P09_Yeti_tilavaraus_2palkki_v2", "p01": "P01_Poytapuristin_2palkki_v2",
             "p07": "P07_Puristinlautanen_2palkki_v2", "p08": "P08_Puristinnuppi_2palkki_v2"}
    out = {}
    for k, n in names.items():
        f = ARM / f"{n}.step"
        if not f.exists():
            sys.exit(f"missing {f}: export Eino's arm as STEP into cad/reference/arm_eino_step/ first (AGENTS.md)")
        out[k] = cq.importers.importStep(str(f)).val()
    return out


def spring(p0, p1, w):
    p0 = np.array([p0[0], p0[1], w]); p1 = np.array([p1[0], p1[1], w])
    d = p1 - p0; L = float(np.linalg.norm(d))
    return cq.Solid.makeCylinder(ARMK["spring_r"], L, V(*p0), V(*(d / L)))


def head_group(arm, tilt):
    """Head parts in the head frame (level, origin = head pivot); P06/P19/P09 tilted about the P06 pivot."""
    t = rz(tilt, (0.0, ARMK["p06_pivot"]))
    return [Posed("P05 head", arm["p05"]), Posed("P06 tilt piece", arm["p06"], t), Posed("P19 Yeti cradle", arm["p19"], t),
            Posed("P09 Yeti", arm["p09"], t @ tr(0, ARMK["p09_offset"]))]


def head_to_bar(beta):
    """head frame -> bar frame for a bar at beta deg (A-frame angle) under a level head."""
    return tr(200.0, 0.0) @ rz(-beta)


def arm_pose(arm, th1, th2):
    """Eino's arm in the A-frame for lower-bar angle th1 and upper-bar angle th2 (deg); head level, tilt 0.
    Returns (dict of Posed, upper-bar placement matrix)."""
    S = np.array(ARMK["shoulder"])
    u1 = np.array([math.cos(math.radians(th1)), math.sin(math.radians(th1))])
    u2 = np.array([math.cos(math.radians(th2)), math.sin(math.radians(th2))])
    lower = tr(*(S + 200 * u1)) @ rz(th1)
    elbow = tr(*(S + 400 * u1)) @ rz(th1)
    U = S + (400 + ARMK["elbow_ext"]) * u1
    upper = tr(*(U + 200 * u2)) @ rz(th2)
    H = U + 400 * u2
    lev = elbow @ np.array([ARMK["lever"][0], ARMK["lever"][1], 0, 1])
    p = {
        "lower bar": Posed("lower bar P03", arm["bar"], lower),
        "elbow": Posed("elbow P04", arm["p04"], elbow),
        "lower P11": Posed("lower spring plug P11", arm["p11"], lower @ tr(15.0, 0)),
        "upper bar": Posed("upper bar P03", arm["bar"], upper),
        "upper P11": Posed("upper spring plug P11", arm["p11"], upper @ tr(P11_CAD_UPPER, 0)),
        "P02": Posed("swivel P02", arm["p02"], tr(0, 24.0)),
        "P01": Posed("desk clamp P01", arm["p01"], ry(-ARMK["swivel"]) @ tr(42.0, 0)),
        "P07": Posed("clamp plate P07", arm["p07"], ry(-ARMK["swivel"]) @ tr(42.0 + 40.0, -47.5)),
        "P08": Posed("clamp knob P08", arm["p08"], ry(-ARMK["swivel"]) @ tr(42.0 + 40.0, -161.0)),
        # desk top: Eino's P10 desk stand-in (500 x 600 x 25 from the clamp edge), extended to a 2 m desk
        "desk": Posed("desk top", box(0.0, 2000.0, -25.0, 0.0, -1000.0, 1000.0), ry(-ARMK["swivel"]) @ tr(42.0, 0)),
    }
    pin_l = S + 200 * u1
    for s in (-1, 1):
        p[f"lower spring {s:+d}"] = Posed(f"lower spring P12 ({'+' if s > 0 else '-'} side)", spring(ARMK["p02_hook"], pin_l, s * ARMK["spring_w"]))
        for o in (P11_CAD_UPPER, max(P11_ORIGINS)):
            pin_u = U + (200 + o - 15.0) * u2
            p[f"upper spring {s:+d} P11@{o:g}"] = Posed(f"upper spring P13 ({'+' if s > 0 else '-'} side, plug at {o:g})", spring(lev[:2], pin_u, s * ARMK["spring_w"]))
    hb = tr(*H) @ np.eye(4)
    for h in head_group(arm, 0.0):
        p[h.name] = h.at(hb)
    return p, upper


# ------------------------------------------------------------------ visibility (ray trace through the real solids)
def ray_hits(shape_w, p0, p1):
    d = p1 - p0; L = float(np.linalg.norm(d))
    lin = gp_Lin(gp_Pnt(*p0), gp_Dir(*(d / L)))
    it = BRepIntCurveSurface_Inter()
    it.Init(shape_w, lin, 1e-4)
    while it.More():
        if 0.5 < it.W() < L - 0.5:
            return True
        it.Next()
    return False


def glass_points(n_rings=4):
    r = M.P["lip_id"] / 2 - 0.5
    pts = [(0.0, 0.0)]
    for k in range(1, n_rings + 1):
        rr = r * k / n_rings
        for i in range(6 * k):
            a = 2 * math.pi * i / (6 * k)
            pts.append((rr * math.cos(a), rr * math.sin(a)))
    return [np.array([x, y, M.B["glass_front"] + 0.01, 1.0]) for x, y in pts]


# ------------------------------------------------------------------ 3MF plate writer (one object per part)
def write_3mf(path, items):
    objs, build = [], []
    for i, (name, shape) in enumerate(items, start=1):
        vs, ts = shape.tessellate(0.02, 0.1)
        v = "".join(f'<vertex x="{p.x:.4f}" y="{p.y:.4f}" z="{p.z:.4f}"/>' for p in vs)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in ts)
        objs.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{v}</vertices><triangles>{t}</triangles></mesh></object>')
        build.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(objs)}</resources><build>{"".join(build)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels); z.writestr("3D/3dmodel.model", model)


def to_bed(shape, R=None):
    s = shape if R is None else shape.moved(loc(R))
    s = cq.Shape.cast(s.wrapped)
    b = s.BoundingBox()
    return s.translate(V(-(b.xmin + b.xmax) / 2, -(b.ymin + b.ymax) / 2, -b.zmin))


def mass_estimate(s):
    """Solid mass and an estimate at 2 perimeters (0.9 mm shell) + 15 % infill: shell = area x 0.9, capped at the volume."""
    vol, area = s.Volume(), s.Area()
    shell = min(vol, area * 0.9)
    return vol, shell + 0.15 * (vol - shell)


# ------------------------------------------------------------------ main
def main():
    t0 = time.time()
    fast = "--fast" in sys.argv
    out = {"checks": [], "numbers": {}, "assumptions": []}
    fail = []
    nums = out["numbers"]

    def check(name, ok, detail):
        out["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            fail.append(name)
        print(("PASS " if ok else "FAIL ") + name + " | " + detail, flush=True)

    arm = load_arm()
    bar = Posed("upper bar P03", arm["bar"])
    base = {1: clamp_base(1), -1: clamp_base(-1)}
    pad = {1: clamp_pad(1), -1: clamp_pad(-1)}
    blk = tilt_block()
    d01 = M.shell(); d02, _ = M.back()
    plug = usb_plug()

    # ---------- 1. clamp on the real bar
    for side in (1, -1):
        sd = "+" if side > 0 else "-"
        vb = overlap(Posed("A10", base[side]), bar)
        vc = overlap(Posed("A11", pad[side]), bar) + overlap(Posed("A11", pad[side]), Posed("A10", base[side]))
        check(f"A10 saddle and A11 pad ({sd}z variant) vs bar and each other: no overlap", 0 <= vb < 0.01 and 0 <= vc < 0.01, f"{vb:.4f} / {vc:.4f} mm3")
    # contact patches: push the bar 0.15 toward each jaw (0.10 gap + 0.05 into the strips); overlap / 0.05 = contact area
    a_base = base[1].intersect(arm["bar"].translate(V(0, 0, 0.15))).Volume() / 0.05
    a_pad = pad[1].intersect(arm["bar"].translate(V(0, 0, -0.15))).Volume() / 0.05
    want = 2 * (CL["strip"][1] - CL["strip"][0]) * (CL["x1"] - CL["x0"])
    nums["contact_area_fixed_wall_mm2"] = round(a_base, 1); nums["contact_area_pad_mm2"] = round(a_pad, 1)
    check("clamp grips the bar's two 30 mm faces only on strips at |y| 11..13.5, next to the tube's top and bottom walls",
          abs(a_base - want) < 3 and abs(a_pad - want) < 3, f"fixed wall {a_base:.1f} mm2, pad {a_pad:.1f} mm2, design {want:.0f} mm2")
    top_band = max(base[1].intersect(box(CL["x0"] - 1, CL["x1"] + 1, -50, 50, -30, 30)).BoundingBox().ymax, pad[1].BoundingBox().ymax)
    nums["clamp_top_below_bar_top_mm"] = round(BAR["h"] / 2 - top_band, 2)
    check("nothing of the clamp rises above the bar's top face (the Yeti can fold down onto the bar)", top_band <= BAR["h"] / 2 - 0.4,
          f"clamp top {top_band:.2f}, bar top {BAR['h'] / 2:.2f}")
    travel = CL["pad"][2] - CL["wall_scr"][0]
    nums["pad_travel_available_mm"] = round(travel, 2)
    check("pad has travel left after taking up both 0.1 mm gaps (> 0.5 mm)", travel - 0.2 > 0.5, f"{travel:.2f} mm gap behind the pad")
    edges = [(h, h + 2.15, "4.3") for h in BAR["holes_43"]] + [(h, h + 3.2, "6.4") for h in BAR["holes_64"]]
    clear_back = min(CL["x0"] - (h + (2.15 if d == "4.3" else 3.2)) for h, _, d in edges if h < CL["x0"])
    clear_front = min((h - (2.15 if d == "4.3" else 3.2)) - CL["x1"] for h, _, d in edges if h > CL["x1"])
    p11_front = max(P11_ORIGINS) + 28.0
    nums["clear_to_hole_behind"] = round(clear_back, 2); nums["clear_to_hole_ahead"] = round(clear_front, 2)
    nums["clear_to_spring_plug_at_furthest_holes"] = round(CL["x0"] - p11_front, 2)
    check("clamp covers no hole of the bar and clears the spring plug in every hole pair",
          clear_back > 5 and clear_front > 5 and CL["x0"] - p11_front > 5,
          f"{clear_back:.2f} mm to the 75 mm spring hole, {clear_front:.2f} mm to the 160 mm hole, {CL['x0'] - p11_front:.1f} mm to P11 on holes 55/75")
    for o in P11_ORIGINS:
        p11 = Posed("P11", arm["p11"], tr(o, 0))
        v = sum(overlap(Posed("A", s_), p11) for s_ in (base[1], base[-1], pad[1], pad[-1]))
        if v > 0.01:
            check(f"spring plug P11 on holes {o:g}/{o + 20:g}", False, f"overlap {v:.3f} mm3")
    # loads. Set-screw thrust F = T / (0.2 d), 2 screws. Snug = 0.1 N m (short arm of the 2 mm key, fingers only);
    # heavy-handed 0.3 N m. Each 30 mm face carries F on 2 strips; the strip's load centre (|y| 12.25) sits 1.25 mm inside
    # the inner face of the tube's top/bottom wall (|y| 13.5) -> face bending; the top/bottom walls take it in compression.
    L = CL["x1"] - CL["x0"]
    lever = (BAR["h"] / 2 - BAR["wall"]) - sum(CL["strip"]) / 2
    arm_u = CL["screw_y"] - CL["floor_top"]
    t_w = abs(CL["wall_scr"][1] - CL["wall_scr"][0]); t_p = abs(CL["pad"][2] - CL["pad"][1])
    span = sum(CL["strip"])
    res = {}
    for label, T in (("snug_0.1Nm", 0.1), ("overtight_0.3Nm", 0.3)):
        F = 2 * T / (0.2 * 0.004)
        q = F / 2 / L
        res[label] = dict(F=F, wall=F / 2 / (BAR["wall"] * L), bend=6 * q * lever / BAR["wall"] ** 2,
                          u=6 * F * arm_u / (L * t_w ** 2), pad=6 * (F * span / 4) / (L * t_p ** 2))
    mu = 0.25; need = 20.0 / (2 * mu)
    sn, ov = res["snug_0.1Nm"], res["overtight_0.3Nm"]
    nums.update({"squeeze_snug_N": round(sn["F"]), "squeeze_overtight_N": round(ov["F"]),
                 "tube_top_bottom_wall_compression_MPa_snug": round(sn["wall"], 1), "tube_face_bending_MPa_snug": round(sn["bend"], 1),
                 "tube_face_bending_MPa_overtight": round(ov["bend"], 1),
                 "petg_U_wall_root_bending_MPa_snug": round(sn["u"], 1), "petg_U_wall_root_bending_MPa_overtight": round(ov["u"], 1),
                 "petg_pad_bending_MPa_snug": round(sn["pad"], 1), "petg_pad_bending_MPa_overtight": round(ov["pad"], 1),
                 "squeeze_needed_for_20N_push_N": round(need), "grip_margin_snug": round(sn["F"] / need, 1)})
    check("tube not crushed: snug squeeze stays under 1/3 of aluminium 6060-T5 yield (120 MPa), over-tightened still under yield",
          max(sn["wall"], sn["bend"]) < 40 and max(ov["wall"], ov["bend"]) < 120,
          f"snug {sn['F']:.0f} N: wall {sn['wall']:.1f} MPa, face bending {sn['bend']:.1f} MPa; 0.3 N m {ov['F']:.0f} N: {ov['wall']:.1f} / {ov['bend']:.1f} MPa")
    check("PETG U wall and pad: snug under 10 MPa (long-term creep), over-tightened under 30 MPa (PETG yields at about 50)",
          max(sn["u"], sn["pad"]) < 10 and max(ov["u"], ov["pad"]) < 30,
          f"snug: wall root {sn['u']:.1f}, pad {sn['pad']:.1f} MPa; 0.3 N m: {ov['u']:.1f} / {ov['pad']:.1f} MPa")
    check("no slide under a 20 N push along the bar (friction 0.25 on 2 faces); rotation about the bar is form-locked by the U",
          sn["F"] > 5 * need, f"snug squeeze {sn['F']:.0f} N vs {need:.0f} N needed (x{sn['F'] / need:.1f})")
    hang = 2 * mu * 0.1 * sn["F"]
    check("the clamp hangs under the bar on friction: with only 10 % of the snug squeeze left it still carries clamp + display (1 N) and a 5 N press",
          hang > 6.0, f"{hang:.1f} N of friction at 10 % squeeze")

    # ---------- 2. MI-1 match with D02 (rail identical to the desk foot's)
    rail = M.rail_local(); rail_nb = M.rail_local(with_bump=False)
    diff = blk.intersect(rail).Volume() - rail.Volume()
    check("A12 rail is the MI-1 rail of md_model (same solid)", abs(diff) < 0.01, f"rail volume inside A12 differs by {diff:.4f} mm3")
    blk_nb = box(-RB["xw"], RB["xw"], RB["y0"], RB["y1"], RB["z_back"], M.P["back_z"]).fuse(rail_nb)
    v = blk_nb.intersect(d02).Volume() + blk.intersect(d01).Volume()
    check("A12 (without the detent bump) vs display unit at home: no overlap", v < 0.01, f"{v:.4f} mm3")
    vb = blk.intersect(d02).Volume()
    nums["detent_bump_overlap_nominal_mm3"] = round(vb, 3)
    check("detent bump is the only designed interference (same as the desk foot)", abs(vb - rail.intersect(d02).Volume()) < 0.01,
          f"{vb:.3f} mm3 nominal (bump into the groove); preload when home {M.MI['bump_h'] - (M.MI['depth'] - M.MI['rail_h']) - M.MI['groove_depth'] - M.MI['axial_play']:.2f} mm")
    seat = box(-RB["xw"], RB["xw"], RB["y0"], RB["y1"], M.P["back_z"] - 0.05, M.P["back_z"]).intersect(d02.translate(V(0, 0, -0.05))).Volume() / 0.05
    nums["display_seat_area_on_A12_mm2"] = round(seat, 1)
    check("display back face sits flat on A12's front face", seat > 200, f"{seat:.0f} mm2 of contact beside the rail")

    # ---------- 3. tilt knuckle: fingers interleave with clearance, display tilts through the whole range without touching A10
    gaps = []
    zr = sorted((KN["wd"] - a1, KN["wd"] - a0) for a0, a1 in RB["fingers"])    # display X = -z, so z = wd - X
    for (w0, w1), (s0, s1) in zip(zr, KN["slots"]):
        gaps += [w0 - s0, s1 - w1]
    nums["knuckle_finger_clearance_each_side"] = [round(g, 2) for g in gaps]
    check("knuckle: A12 fingers sit in A10's slots with 0.10-0.20 mm each side", all(0.1 <= g <= 0.2 for g in gaps), f"{[round(g, 2) for g in gaps]} mm")
    worst = 0.0
    tested = []
    hwp = {1: hardware(1), -1: hardware(-1)}
    for side in (1, -1):
        a10 = Posed("A10", base[side].fuse(hwp[side]))
        for eps in np.arange(PITCH[0], PITCH[1] + 0.01, 2.0):
            m = display_to_bar(float(eps), side)
            for nm, s in (("A12", blk), ("D01", d01), ("D02", d02), ("USB plug", plug)):
                v = overlap(Posed(nm, s, m), a10)
                worst = max(worst, v)
                if v > 0.01:
                    tested.append(f"{nm} at {eps:.0f} deg ({side:+d}): {v:.3f}")
    check(f"display + A12 + USB plug tilt {PITCH[0]:g}..{PITCH[1]:g} deg without touching A10 (2 deg steps, both sides)",
          worst < 0.01, "; ".join(tested[:5]) or "0 mm3 at every step")
    for eps in (PITCH[0] - 4, PITCH[1] + 4):
        m = display_to_bar(eps, 1)
        v = sum(overlap(Posed(nm, s, m), Posed("A10", base[1])) for nm, s in (("A12", blk), ("D01", d01), ("D02", d02)))
        nums[f"stop_contact_at_{eps:g}deg_mm3"] = round(v, 2)

    # the display slides onto A12's rail from above (along its +Y, 45 mm) without touching the clamp, at the tilt it is set for
    du = d01.fuse(d02)
    stuck = []
    for side in (1, -1):
        fixed_parts = [Posed("A10", base[side]), Posed("A11", pad[side]), Posed("hinge bolt", hwp[side]), bar]
        for eps in (45.0, 64.0, 90.0):
            for dyy in np.arange(0.0, 45.01, 5.0):
                m = display_to_bar(eps, side) @ tr(0, float(dyy))
                v = sum(overlap(Posed("display", du, m), f) for f in fixed_parts)
                if v > 0.01:
                    stuck.append(f"tilt {eps:g}, {dyy:g} mm up, side {side:+d}: {v:.2f} mm3")
    check("display slides on and off the rail (45 mm along the rail) at tilt 45, 64 and 90 deg without touching the clamp, bolts or bar",
          not stuck, "; ".join(stuck[:4]) or "clear at every 5 mm step")
    # friction hinge: 4 PETG-on-PETG faces between the 5 fingers, M5 nyloc at a snug 1 N m, annulus 2.65..7.5 mm
    Fm5 = 1.0 / (0.2 * 0.005); r_eff = 2 / 3 * (7.5 ** 3 - 2.65 ** 3) / (7.5 ** 2 - 2.65 ** 2) / 1000
    T_hold = 4 * 0.3 * (0.2 * Fm5) * r_eff        # only 20 % of the bolt force left after flexing the outer fingers
    T_touch = 5.0 * (-RB["z_axis"] + M.P["od"] / 2) / 1000     # 5 N press at the glass edge
    nums["hinge_holding_torque_Nm"] = round(T_hold, 2); nums["touch_torque_5N_at_glass_edge_Nm"] = round(T_touch, 2)
    check("tilt hinge holds a 5 N press on the glass edge (M5 nyloc snug, 20 % of its preload counted)", T_hold > 2 * T_touch,
          f"{T_hold:.2f} N m holding vs {T_touch:.2f} N m from the press")

    # ---------- 4a. arm range, head end: bar angle x Yeti tilt (bar frame); every pose Eino's own parts allow
    betas = [-28.5, -20, -10, 0, 15, 30, 45, 60, 75, 90, 120, 150, 180] if not fast else [-28.5, 0, 45, 90, 180]
    tilts = list(range(-80, 81, 20)) if not fast else [-80, 0, 80]
    epss = [PITCH[0], 25, 50, 75, PITCH[1]]
    reach, hits, limits = 0, [], {}

    def own_hit(hb, tilt):
        heads = [h.at(hb) for h in head_group(arm, tilt)]
        return sum(overlap(h, bar) for h in heads) + sum(overlap(h, heads[0]) for h in heads[1:3]) > 0.5

    for beta in betas:
        hb = head_to_bar(beta)
        # the Yeti's own tilt limits at this bar angle (where Eino's parts touch the bar or the head), found by bisection:
        # the extreme poses (the Yeti folded down onto the bar) are tested exactly, not only on the 20 deg grid
        lim = []
        for sgn in (1, -1):
            if not own_hit(hb, sgn * ARMK["tilt_max"]):
                lim.append(sgn * ARMK["tilt_max"]); continue
            lo, hi = 0.0, ARMK["tilt_max"]
            for _ in range(8):
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if own_hit(hb, sgn * mid) else (mid, hi)
            lim.append(sgn * lo)
        limits[str(beta)] = [round(v, 1) for v in lim]
        for tilt in sorted(set(tilts + lim)):
            heads = [h.at(hb) for h in head_group(arm, tilt)]
            own = sum(overlap(h, bar) for h in heads) + sum(overlap(h, heads[0]) for h in heads[1:3])
            if own > 0.5:
                continue        # Eino's arm cannot be in this pose
            reach += 1
            for side in (1, -1):
                ad = [Posed("A10", base[side]), Posed("A11", pad[side]), Posed("hinge bolt", hwp[side])]
                for eps in epss:
                    m = display_to_bar(eps, side)
                    ad += [Posed(f"A12@{eps:g}", blk, m), Posed(f"D01@{eps:g}", d01, m), Posed(f"D02@{eps:g}", d02, m), Posed(f"USB@{eps:g}", plug, m)]
                for a in ad:
                    for h in heads:
                        v = overlap(a, h)
                        if v > 0.01:
                            hits.append(f"{a.name} x {h.name} beta {beta} tilt {tilt} side {side:+d}: {v:.2f}")
    nums["head_sweep_poses_reachable"] = reach
    nums["yeti_tilt_limits_by_bar_angle"] = limits
    check(f"no contact with the head, tilt piece, Yeti cradle or Yeti: bar {betas[0]}..{betas[-1]} deg x Yeti tilt to its own limits (+-80 deg or where it lands on the bar), display tilt {PITCH[0]:g}..{PITCH[1]:g}, both sides",
          not hits, f"{reach} reachable head poses; " + ("; ".join(hits[:4]) if hits else "0 contacts"))
    # closest approach to the head parts at the head joint's stop (bar descending 28.5 deg, worst case)
    hb = head_to_bar(ARMK["head_beta_min"])
    cl = []
    for tilt in (-80, -40, 0, 40, 80):
        heads = [h.at(hb) for h in head_group(arm, tilt)]
        if sum(overlap(h, bar) for h in heads) > 0.5:
            continue
        for h in heads:
            for a in (Posed("A10", base[1]), Posed("A11", pad[1]), Posed("D02", d02, display_to_bar(50, 1)), Posed("D01", d01, display_to_bar(50, 1))):
                cl.append((dist(a, h), a.name, h.name, tilt))
    cl.sort()
    nums["closest_to_head_parts_at_head_stop"] = [f"{d:.1f} mm {a} to {h} (Yeti tilt {t})" for d, a, h, t in cl[:3]]
    check("at the head joint's stop the adapter keeps >= 5 mm from every head part", cl[0][0] >= 5.0, nums["closest_to_head_parts_at_head_stop"][0])

    # ---------- 4b. arm range, whole arm: shoulder x elbow (A-frame), springs at the CAD and furthest plug holes
    th1s = list(range(-20, 111, 10)) if not fast else [-20, 30, 90]
    phis = list(range(-180, 180, 10)) if not fast else list(range(-180, 180, 30))
    reach_arm, hits_arm, desk_hits, lowest = 0, [], [], []
    cad_ok = None
    for th1 in th1s + ["cad"]:
        for phi in (phis if th1 != "cad" else [None]):
            if th1 == "cad":
                a1, a2 = ARMK["lower_cad"], ARMK["upper_cad"]
            else:
                a1, a2 = th1, th1 + phi
            beta = (a2 + 180) % 360 - 180
            if beta < ARMK["head_beta_min"]:
                continue
            P, up = arm_pose(arm, a1, a2)
            lowerg = [P["lower bar"], P["elbow"], P["lower P11"]]
            fixed = [P["P02"], P["P01"], P["desk"]]
            upperg = [P["upper bar"], P["upper P11"]] + [P[k] for k in ("P05 head", "P06 tilt piece", "P19 Yeti cradle", "P09 Yeti")]
            springs_l = [P["lower spring -1"], P["lower spring +1"]]
            # Eino's own limits: lower arm vs swivel, desk clamp and desk; upper arm + head vs everything below it
            own = 0.0
            for a in lowerg:
                for b in fixed:
                    own += overlap(a, b)
            for a in upperg:
                for b in lowerg + fixed + springs_l:
                    own += overlap(a, b)
            if th1 == "cad":
                cad_ok = own < 0.5
            if own > 0.5:
                continue
            reach_arm += 1
            for side in (1, -1):
                ad = [Posed("A10", base[side], up), Posed("A11", pad[side], up), Posed("hinge bolt", hwp[side], up)]
                for eps in (PITCH[0], 50, PITCH[1]):
                    m = up @ display_to_bar(eps, side)
                    ad += [Posed(f"A12@{eps:g}", blk, m), Posed(f"display@{eps:g}", d02, m), Posed(f"glass@{eps:g}", d01, m), Posed(f"USB@{eps:g}", plug, m)]
                others = lowerg + [P["P02"], P["P01"], P["P07"], P["P08"], P["upper P11"]] + springs_l + \
                    [P[k] for k in P if k.startswith("upper spring")]
                for a in ad:
                    for b in others:
                        v = overlap(a, b)
                        if v > 0.01:
                            hits_arm.append(f"{a.name} x {b.name} at lower {a1:.0f} / upper {a2:.0f} deg side {side:+d}: {v:.2f}")
                    if overlap(a, P["desk"]) > 0.01:
                        desk_hits.append((a1, a2, a.name, side))
                lo_ad = min(x.aabb()[0][1] for x in ad)
                lo_head = P["P05 head"].aabb()[0][1]
                lowest.append(lo_ad - lo_head)
    nums["arm_sweep_poses_reachable"] = reach_arm
    check("Eino's CAD pose is inside the swept range (sanity)", bool(cad_ok), "CAD pose reachable" if cad_ok else "CAD pose flagged as self-colliding")
    check("no contact with the lower bar, elbow, spring plugs, springs, swivel or desk clamp anywhere in the arm's range (shoulder -20..110 deg x elbow full circle, both sides, 3 display tilts)",
          not hits_arm, f"{reach_arm} reachable arm poses; " + ("; ".join(hits_arm[:4]) if hits_arm else "0 contacts"))
    nums["poses_where_adapter_reaches_the_desk_before_eino_parts"] = len(desk_hits)
    nums["adapter_lowest_point_minus_head_lowest_point_worst_mm"] = round(max(lowest), 1) if lowest else None
    nums["adapter_lowest_point_minus_head_lowest_point_best_mm"] = round(min(lowest), 1) if lowest else None

    # ---------- 5. layout: visibility from the user's eye, mic path, monitor view (use poses)
    out["assumptions"] = [
        "user sits in line with the arm beyond the head (the Yeti's front faces along the arm in Eino's CAD: cradle knobs on the arm's z axis)",
        "capsule at head-frame height 280 mm (upper part of the Yeti body, P09 spans 144..334); mouth level with it, 100-200 mm in front (USE_SETUP)",
        "eyes 75 mm above the mouth and 10 mm behind it: eye x 110..210, y 330..380, sideways -40..+40 mm (head movement)",
    ]
    eyes = [np.array([x, y, w]) for x in (110, 160, 210) for y in (330, 355, 380) for w in (-40, 0, 40)]
    eye0 = np.array([160.0, 355.0, 0.0])
    vis_rows = []
    for beta in (-28.5, -20.0, 0.0, 20.0):
        hb = head_to_bar(beta)
        # aim: glass normal toward the nominal eye, projected on the arm plane (only tilt about z is adjustable)
        e0b = (hb @ np.append(eye0, 1.0))[:3]
        best = None
        for eps in np.arange(PITCH[0], PITCH[1] + 0.01, 1.0):
            m = display_to_bar(float(eps), -1)
            c = m[:3, 3]; n = m[:3, 2]
            dvec = e0b - c; ang = math.degrees(math.acos(np.dot(dvec, n) / np.linalg.norm(dvec)))
            if best is None or ang < best[1]:
                best = (float(eps), ang)
        eps, off_axis = best
        m = display_to_bar(eps, -1)
        gp = [m @ g for g in glass_points()]
        up = (rz(beta) @ m)[:3, 1][1]          # display's +Y (rail stop side) in the arm's plane frame: > 0 = points upward
        row = {"bar_deg": beta, "tilt_set_deg": round(eps, 1), "off_axis_deg": round(off_axis, 1),
               "eye_distance_mm": round(float(np.linalg.norm(e0b - m[:3, 3]))), "display_up_axis_vertical_component": round(float(up), 2)}
        for ytilt in (-20, -10, 0, 10, 20):
            occl = [h.at(hb).solid().wrapped for h in head_group(arm, ytilt)] + [arm["bar"].wrapped, base[-1].wrapped, pad[-1].wrapped,
                                                                                  hwp[-1].wrapped, d01.moved(loc(m)).wrapped]
            seen = lambda e: sum(0 if any(ray_hits(o, e, g[:3]) for o in occl) else 1 for g in gp) / len(gp)
            row[f"glass_visible_nominal_eye_yeti_tilt_{ytilt}"] = round(seen(e0b), 3)
            if ytilt == 0:
                row["glass_visible_worst_of_27_eyes"] = round(min(seen((hb @ np.append(e, 1.0))[:3]) for e in eyes), 3)
        vis_rows.append(row)
    nums["view_from_user"] = vis_rows
    f0 = lambda r: min(r[f"glass_visible_nominal_eye_yeti_tilt_{t}"] for t in (-10, 0, 10))
    f20 = lambda r: min(r[f"glass_visible_nominal_eye_yeti_tilt_{t}"] for t in (-20, 20))
    check("user sees the whole glass from the nominal eye (>= 99 % with the Yeti tilted up to 10 deg, >= 95 % at 20 deg), bar -28.5..+20 deg; "
          "ray trace through head, Yeti, cradle, bar, clamp, bolts and the display's own lip",
          all(f0(r) >= 0.99 and f20(r) >= 0.95 for r in vis_rows),
          "; ".join(f"bar {r['bar_deg']}: {f0(r) * 100:.0f} % ({f20(r) * 100:.0f} % at Yeti tilt 20; worst of 27 eye positions {r['glass_visible_worst_of_27_eyes'] * 100:.0f} %), "
                    f"{r['eye_distance_mm']} mm, {r['off_axis_deg']} deg off-axis" for r in vis_rows))
    check("reading distance 300-450 mm (USE_SETUP)", all(300 <= r["eye_distance_mm"] <= 450 for r in vis_rows), f"{[r['eye_distance_mm'] for r in vis_rows]} mm")
    check("in every reading pose the display's weight presses it onto the MI-1 rail stop (its up axis points upward)",
          all(r["display_up_axis_vertical_component"] > 0.2 for r in vis_rows), f"{[r['display_up_axis_vertical_component'] for r in vis_rows]}")
    # mic path and monitor view (head frame): the display stays below the Yeti body, so it is out of the mouth-to-capsule
    # path, and far below the user's lowest sight line to the monitor
    vs = np.array([[v.x, v.y, v.z, 1.0] for v in d01.tessellate(0.5)[0]] + [[v.x, v.y, v.z, 1.0] for v in d02.tessellate(0.5)[0]])
    tops, depress = [], []
    for beta in (-28.5, -20.0, 0.0, 20.0):
        inv = np.linalg.inv(head_to_bar(beta))
        for eps in np.arange(PITCH[0], PITCH[1] + 0.01, 5.0):
            pts = (inv @ display_to_bar(float(eps), -1) @ vs.T).T[:, :3]
            tops.append(pts[:, 1].max())
            rel = pts - eye0
            depress.append(np.degrees(np.arctan2(-rel[:, 1], np.hypot(rel[:, 0], rel[:, 2]))).min())
    # monitor: 650 mm in front of the eye, lower screen edge 100 mm above the desk, eye 450 mm above the desk (USE_SETUP)
    mon = math.degrees(math.atan2(450.0 - 100.0, 650.0))
    nums["display_top_above_head_pivot_max_mm"] = round(max(tops), 1)
    nums["yeti_body_bottom_above_head_pivot_mm"] = 144.0
    nums["display_seen_below_horizontal_min_deg"] = round(min(depress), 1)
    nums["monitor_lower_edge_below_horizontal_deg"] = round(mon, 1)
    check("display stays below the Yeti body, out of the mouth-to-capsule path (every bar angle and display tilt)",
          max(tops) < 144.0 - 20, f"display top at most {max(tops):.0f} mm above the head pivot; Yeti body starts 144 mm above it; capsule about 280 mm")
    check("display sits well under the user's lowest sight line to the monitor (>= 15 deg lower)", min(depress) > mon + 15,
          f"display seen at least {min(depress):.0f} deg below horizontal; monitor's lower edge at {mon:.0f} deg")

    # ---------- 6. hardware lengths
    # M4x10 set screw from outside the far wall: tip in the pad's dimple, back end must stay inside the wall
    tip = CL["pad"][2] + CL["dimple"][1]                 # dimple bottom (left-built variant, screws on the -z side)
    back = tip - 10.0
    nz0, nz1 = sorted(CL["nut_z"])
    nums["set_screw_back_end_recessed_mm"] = round(back - CL["wall_scr"][1], 2)
    nums["set_screw_length_through_nut_mm"] = round(min(tip, nz1) - max(back, nz0), 2)
    check("M4x10 set screw: runs through the whole captive nut and its back end stays inside the wall (0.5-3 mm)",
          min(tip, nz1) - max(back, nz0) >= 3.2 and 0.5 <= back - CL["wall_scr"][1] <= 3.0,
          f"{min(tip, nz1) - max(back, nz0):.2f} mm in the nut zone, back end {back - CL['wall_scr'][1]:.2f} mm inside the wall's outer face")
    head5 = KN["fingers"][-1][1] + 1.0; nyl_bot = KN["boss"][0] + KN["nyloc_depth"] - 5.0
    tip5 = head5 - 25.0
    nums["M5x25_tip_past_nyloc_mm"] = round(nyl_bot - tip5, 2)
    check("M5x25: passes the nyloc nut by >= 1.5 mm (nylon ring fully engaged)", nyl_bot - tip5 >= 1.5, f"{nyl_bot - tip5:.2f} mm")

    # ---------- exports
    pr = CAD / "print"; asm = CAD / "assembly"; asm.mkdir(parents=True, exist_ok=True)
    pr.mkdir(parents=True, exist_ok=True)
    rot_up_y = mat(np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]))      # y -> +Z (print up)
    rot_down_y = mat(np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]))    # y -> -Z
    parts = {
        "A10_PETG_arm_clamp_base_display_right": to_bed(base[-1], rot_up_y),
        "A10_PETG_arm_clamp_base_display_left": to_bed(base[1], rot_up_y),
        "A11_PETG_arm_clamp_pad": to_bed(pad[1]),
        "A12_PETG_arm_MI1_tilt_block": to_bed(blk, rot_up_y),
    }
    manifest = []
    for name, s in parts.items():
        w = cq.Workplane().add(s)
        for ext in ("step", "stl", "3mf"):
            kw = {"tolerance": 0.02, "angularTolerance": 0.1} if ext in ("stl", "3mf") else {}
            cq.exporters.export(w, str(pr / f"{name}.{ext}"), **kw)
    # combined print plate: D01 + D02 (M05, as printed from cad/print) + A10 (right) + A11 + A12; MK4S bed 250 x 210, >= 10 mm apart
    plate_parts = [(n, cq.importers.importStep(str(pr / f"{n}.step")).val()) for n in ("D01_PETG_display_shell", "D02_PETG_display_back_MI1")]
    plate_parts += [(n, parts[n]) for n in ("A10_PETG_arm_clamp_base_display_right", "A11_PETG_arm_clamp_pad", "A12_PETG_arm_MI1_tilt_block")]
    for name, s in plate_parts + [(n, parts[n]) for n in parts if n.endswith("_left")]:
        vol, est = mass_estimate(s)
        bb = s.BoundingBox()
        manifest.append({"part": name, "volume_cm3": round(vol / 1000, 2), "petg_g_solid": round(vol / 1000 * 1.27, 1),
                         "petg_g_2perim_15infill_est": round(est / 1000 * 1.27, 1),
                         "print_size_mm": [round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)]})
    (pr / "manifest_arm_adapter.json").write_text(json.dumps(manifest, indent=2))
    out["parts"] = manifest
    gapmm = 15.0
    pp = dict(plate_parts)
    bx = {n: pp[n].BoundingBox() for n in pp}
    a10 = "A10_PETG_arm_clamp_base_display_right"
    grid = [["D01_PETG_display_shell", "D02_PETG_display_back_MI1"], ["A11_PETG_arm_clamp_pad", "A12_PETG_arm_MI1_tilt_block"]]
    pos = {a10: (-bx[a10].xmin, -bx[a10].ymin)}
    x0g, y = bx[a10].xlen + gapmm, 0.0       # the four small parts in a 2 x 2 grid beside the clamp base
    colw = [max(bx[r[c]].xlen for r in grid) for c in range(2)]
    for r in grid:
        x = x0g
        for c, n in enumerate(r):
            pos[n] = (x - bx[n].xmin, y - bx[n].ymin)
            x += colw[c] + gapmm
        y += max(bx[n].ylen for n in r) + gapmm
    row1, row2 = [a10] + grid[0], grid[1]
    allb = [(pp[n].BoundingBox(), pos[n]) for n in pos]
    w_all = max(b.xmax + d[0] for b, d in allb); h_all = max(b.ymax + d[1] for b, d in allb)
    ox, oy = (250 - w_all) / 2, (210 - h_all) / 2
    placed = [(n, pp[n].translate(V(pos[n][0] + ox, pos[n][1] + oy, 0))) for n in row1 + row2]
    boxes = [(n, s.BoundingBox()) for n, s in placed]
    inside = all(b.xmin >= 5 and b.ymin >= 5 and b.xmax <= 245 and b.ymax <= 205 for _, b in boxes)
    gap = min(max(b2.xmin - b1.xmax, b1.xmin - b2.xmax, b2.ymin - b1.ymax, b1.ymin - b2.ymax)
              for i, (_, b1) in enumerate(boxes) for (_, b2) in boxes[i + 1:])
    nums["plate_min_gap_mm"] = round(gap, 1)
    nums["plate_boxes_xmin_ymin_xmax_ymax_h"] = {n: [round(b.xmin, 1), round(b.ymin, 1), round(b.xmax, 1), round(b.ymax, 1), round(b.zmax, 1)] for n, b in boxes}
    check("print plate: 5 parts inside the MK4S bed (250 x 210, 5 mm margin), >= 10 mm apart", inside and gap >= 10, f"min gap {gap:.1f} mm")
    write_3mf(pr / "MD_plate_display_and_arm_clamp.3mf", placed)
    # clamp-only plate (A10 right + A11 + A12) for printing the adapter on its own: A10 left, A11 over A12 beside it
    cl = [a10, "A11_PETG_arm_clamp_pad", "A12_PETG_arm_MI1_tilt_block"]
    cpos = {a10: (-bx[a10].xmin, -bx[a10].ymin)}
    yy = 0.0
    for n in cl[1:]:
        cpos[n] = (bx[a10].xlen + gapmm - bx[n].xmin, yy - bx[n].ymin); yy += bx[n].ylen + gapmm
    w_c = max(bx[n].xmax + cpos[n][0] for n in cl); h_c = max(bx[n].ymax + cpos[n][1] for n in cl)
    cx, cy = (250 - w_c) / 2, (210 - h_c) / 2
    cplaced = [(n, pp[n].translate(V(cpos[n][0] + cx, cpos[n][1] + cy, 0))) for n in cl]
    cboxes = [s.BoundingBox() for _, s in cplaced]
    cin = all(b.xmin >= 5 and b.ymin >= 5 and b.xmax <= 245 and b.ymax <= 205 for b in cboxes)
    cgap = min(max(b2.xmin - b1.xmax, b1.xmin - b2.xmax, b2.ymin - b1.ymax, b1.ymin - b2.ymax)
               for i, b1 in enumerate(cboxes) for b2 in cboxes[i + 1:])
    nums["clamp_plate_min_gap_mm"] = round(cgap, 1)
    check("clamp-only plate: A10 + A11 + A12 inside the MK4S bed (250 x 210, 5 mm margin), >= 10 mm apart", cin and cgap >= 10,
          f"min gap {cgap:.1f} mm")
    write_3mf(pr / "MD_plate_arm_clamp.3mf", cplaced)
    # assemblies (git-ignored): adapter + display on the bar, and in Eino's CAD pose
    m = display_to_bar(50, -1)
    cq.exporters.export(cq.Workplane().add(cq.Compound.makeCompound([arm["bar"], base[-1], pad[-1], blk.moved(loc(m)), d01.moved(loc(m)), d02.moved(loc(m))])),
                        str(asm / "arm_adapter_on_bar.step"))
    out["failed"] = fail
    out["runtime_s"] = round(time.time() - t0)
    (CAD / "checks" / "arm_adapter_fit_check.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out["numbers"], indent=1))
    print("FAILED:" if fail else "ALL PASS", fail, f"{out['runtime_s']} s")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
