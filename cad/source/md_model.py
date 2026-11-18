"""Mic-stand display: display unit (D01 shell + D02 back) and mounting interface MI-1, desk foot A00.

Frame (mm): X right and Y up as seen from the front, Z toward the viewer. Origin = screen centre.
The board is Waveshare ESP32-S3-Touch-AMOLED-1.75 (cad/reference/ESP32-S3-Touch-AMOLED-1_75.stp,
Waveshare's own model). Its STEP has the screen normal along +y and the USB-C at -x; rotating it
120 deg about (1,1,1) maps x->Y, y->Z, z->X, so the USB-C points down (-Y) and the screen faces +Z.

Run:  scripts/md.ps1 cad  (Windows)  or  scripts/md.sh cad  (macOS)
Writes cad/print/*.{step,stl,3mf}, cad/assembly/*.step and cad/checks/fit_check.json; exit 1 on a failed check.
"""
from pathlib import Path
import json, math, sys

import cadquery as cq

ROOT = Path(__file__).resolve().parents[2]
CAD = ROOT / "cad"
V = cq.Vector

# ---------------------------------------------------------------- board (read from Waveshare's STEP)
B = dict(
    glass_d=48.96, glass_front=2.77,          # touch glass outer diameter, front face
    standoff_bottom=-7.63,                     # 3 x M2 brass standoffs (H3.5) under the PCB, female thread
    standoff_xy=[(14.70, 13.75), (14.70, -13.75), (-20.50, 0.00)],
    pcb_bottom=-4.13,
    header_bottom=-9.93,                       # 8-pin header, deepest part
    usb_x=(-4.81, 4.81), usb_z=(-7.38, -3.22), usb_edge_y=-23.79,
    btn_angle=33.5, btn_z=-4.83,               # PWR / BOOT side buttons, degrees from +Y
)

# ---------------------------------------------------------------- display unit
P = dict(
    bore_d=49.40,          # glass 48.96 + 0.22 per side (PETG prints holes small)
    wall=2.00,
    lip_t=1.20, lip_id=44.60, lip_gap=0.10,    # lip covers the 2.2 mm black glass border; 0.1 off the glass
    split_z=-10.50,        # shell back edge = inner face of the back (header bottom -9.93 -> 0.57 clear)
    back_z=-15.90,         # back face (flat, prints on the bed)
    boss_d=5.00,           # board-screw bosses on the back, up to the standoffs
    m2_clear=2.40, m2_pilot=1.70, cbore_d=4.20, head_seat_z=-10.70,   # screw heads sit 0.2 under the inner face
    shell_screw_r=23.90, shell_screw_deg=[90.0, 235.0, 305.0],  # degrees from +X, counter-clockwise from the front
    shell_boss_top=-5.00,  # at the wall; underside sloped 45 deg so it prints without support
    usb_w=13.0, usb_h=7.5, usb_r=2.0,          # plug overmold clearance (typical USB-C overmold 12.4 x 6.5)
    btn_hole_d=2.5,
)
P["od"] = P["bore_d"] + 2 * P["wall"]

# ---------------------------------------------------------------- mounting interface MI-1 (fixed: every adapter fits every display unit)
MI = dict(
    floor_w=20.00, depth=3.00, angle=60.0,     # female channel: 20.00 wide at its floor, 3.00 deep, flanks 60 deg to the face
    y_open=-27.50, y_stop=16.00,               # open at the bottom edge, closed at the top (stop face at Y=16)
    groove_y=8.00, groove_r=1.50, groove_depth=0.40,  # detent groove across the channel floor
    clear=0.20,                                # rail flanks 0.20 off the channel flanks (normal)
    rail_h=2.75, rail_len=30.0,
    tongue_w=8.0, tongue_t=1.40, tongue_from=5.0, tongue_to=17.0, slot=0.8,   # from the rail's top end
    bump_h=1.20, bump_r=1.50, bump_at=8.0,
    axial_play=0.40,                           # display can lift 0.2 / cos(60) off the adapter face before the flanks touch
)
MI["open_w"] = MI["floor_w"] - 2 * MI["depth"] / math.tan(math.radians(MI["angle"]))


def prism_xz(pts_uv, y0, y1):
    """Polygon in (u=X, v=Z) extruded from Y=y0 to Y=y1."""
    w = cq.Workplane("XY").polyline(pts_uv).close().extrude(y1 - y0)
    s = w.val().rotate(V(0, 0, 0), V(1, 0, 0), 90)       # (u,v,w) -> (u,-w,v): spans Y -(y1-y0)..0
    return s.translate(V(0, y1, 0))


def cyl(r, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))


def board():
    s = cq.importers.importStep(str(CAD / "reference" / "ESP32-S3-Touch-AMOLED-1_75.stp")).val()
    return s.rotate(V(0, 0, 0), V(1, 1, 1), 120)


# ---------------------------------------------------------------- D01 shell
def shell():
    r_o, r_b = P["od"] / 2, P["bore_d"] / 2
    z_lip_back = B["glass_front"] + P["lip_gap"]
    z_front = z_lip_back + P["lip_t"]
    s = cyl(r_o, P["split_z"], z_front).cut(cyl(r_b, P["split_z"] - 1, z_lip_back))
    s = s.cut(cyl(P["lip_id"] / 2, z_lip_back - 1, z_front + 1))
    # 45 deg chamfer on the lip's inner front edge (keeps the screen edge unshaded) and 0.8 on the outer front edge
    s = s.cut(cq.Solid.makeCone(P["lip_id"] / 2, P["lip_id"] / 2 + 1.2, 0.8, V(0, 0, z_front - 0.8)))
    ring = cyl(r_o + 1, z_front - 0.8, z_front + 0.1).cut(cq.Solid.makeCone(r_o, r_o - 0.9, 0.9, V(0, 0, z_front - 0.8)))
    s = s.cut(ring)
    # screw bosses at the back edge, underside sloped 45 deg into the wall
    for deg in P["shell_screw_deg"]:
        a = math.radians(deg)
        x, y = P["shell_screw_r"] * math.cos(a), P["shell_screw_r"] * math.sin(a)
        boss = cyl(P["boss_d"] / 2, P["split_z"], P["shell_boss_top"], x, y)
        n = V(math.cos(a), math.sin(a), 0)             # outward
        cutter = cq.Solid.makeBox(20, 20, 20, V(-10, -10, 0))
        # plane through (r_b along n, z=boss_top), rising 45 deg outward: remove material above it
        cutter = cutter.rotate(V(0, 0, 0), V(0, 1, 0), -45)   # bottom face becomes a plane rising outward
        cutter = cutter.rotate(V(0, 0, 0), V(0, 0, 1), deg)
        cutter = cutter.translate(V(r_b * n.x, r_b * n.y, P["shell_boss_top"]))
        boss = boss.cut(cutter)
        s = s.fuse(boss)
        s = s.cut(cyl(P["m2_pilot"] / 2, P["split_z"] - 1, P["shell_boss_top"] + 1, x, y))
    # USB-C opening (bottom)
    zc = sum(B["usb_z"]) / 2
    usb = (cq.Workplane("XZ").rect(P["usb_w"], P["usb_h"]).extrude(-12).edges("|Y").fillet(P["usb_r"])
           .val().translate(V(0, -r_o - 2, zc)))
    s = s.cut(usb)
    # PWR / BOOT pin holes
    for sgn in (-1, 1):
        a = math.radians(90 - sgn * B["btn_angle"])
        d = V(math.cos(a), math.sin(a), 0)
        s = s.cut(cq.Solid.makeCylinder(P["btn_hole_d"] / 2, 6, V(d.x * (r_b - 1.5), d.y * (r_b - 1.5), B["btn_z"]), d))
    return s.clean()


# ---------------------------------------------------------------- D02 back with the female MI-1 channel
def back():
    r_o = P["od"] / 2
    s = cyl(r_o, P["back_z"], P["split_z"])
    for (x, y) in B["standoff_xy"]:
        s = s.fuse(cyl(P["boss_d"] / 2, P["split_z"] - 0.5, B["standoff_bottom"], x, y))
    # channel: trapezoid, 20.00 at the floor (Z = back_z + depth), open_w at the back face
    zf = P["back_z"] + MI["depth"]
    h_o, h_f = MI["open_w"] / 2, MI["floor_w"] / 2
    ch = prism_xz([(-h_o, P["back_z"] - 0.01), (h_o, P["back_z"] - 0.01), (h_f, zf), (-h_f, zf)], MI["y_open"], MI["y_stop"])
    s = s.cut(ch)
    g = cq.Solid.makeCylinder(MI["groove_r"], MI["open_w"], V(-MI["open_w"] / 2, MI["groove_y"], zf + MI["groove_depth"] - MI["groove_r"]), V(1, 0, 0))
    s = s.cut(g)
    # screw holes: clearance through, counterbore from the back face to the head seat
    holes = list(B["standoff_xy"]) + [(P["shell_screw_r"] * math.cos(math.radians(d)), P["shell_screw_r"] * math.sin(math.radians(d))) for d in P["shell_screw_deg"]]
    for (x, y) in holes:
        s = s.cut(cyl(P["m2_clear"] / 2, P["back_z"] - 1, B["standoff_bottom"] + 1, x, y))
        s = s.cut(cyl(P["cbore_d"] / 2, P["back_z"] - 1, P["head_seat_z"], x, y))
    # 0.6 chamfer on the back outer edge
    ring = cyl(r_o + 1, P["back_z"] - 0.1, P["back_z"] + 0.6).cut(cq.Solid.makeCone(r_o - 0.6, r_o, 0.6, V(0, 0, P["back_z"])))
    return s.cut(ring).clean(), holes


# ---------------------------------------------------------------- MI-1 male rail (adapter side), local frame
def rail_local(with_bump=True):
    """Rail in the display's frame when fully home: root face on the back face plane (Z = back_z),
    rising into the channel (toward +Z). Spans Y from y_stop - rail_len to y_stop."""
    t = math.tan(math.radians(MI["angle"]))
    dn = MI["clear"] / math.sin(math.radians(MI["angle"]))   # horizontal offset of a flank moved 0.2 along its normal
    z0, z1 = P["back_z"], P["back_z"] + MI["rail_h"]
    w0 = MI["open_w"] / 2 - dn
    w1 = MI["open_w"] / 2 + MI["rail_h"] / t - dn
    y_top = MI["y_stop"]
    y_bot = y_top - MI["rail_len"]
    r = prism_xz([(-w0, z0), (w0, z0), (w1, z1), (-w1, z1)], y_bot, y_top)
    # tongue: U slot through the rail, void under the tongue
    ya, yb = y_top - MI["tongue_to"], y_top - MI["tongue_from"]
    tw, sl = MI["tongue_w"] / 2, MI["slot"]
    r = r.cut(cq.Solid.makeBox(sl, yb - ya + sl, MI["rail_h"] + 1, V(tw, ya, z0 - 0.5)))
    r = r.cut(cq.Solid.makeBox(sl, yb - ya + sl, MI["rail_h"] + 1, V(-tw - sl, ya, z0 - 0.5)))
    r = r.cut(cq.Solid.makeBox(2 * tw + 2 * sl, sl, MI["rail_h"] + 1, V(-tw - sl, yb, z0 - 0.5)))
    r = r.cut(cq.Solid.makeBox(2 * tw, yb - ya, MI["rail_h"] - MI["tongue_t"], V(-tw, ya, z0 - 0.5)).translate(V(0, 0, 0.5 - 0.0)))
    if not with_bump:
        return r.clean()
    # bump on the tongue (cylinder segment across X)
    yb_c = y_top - MI["bump_at"]
    bump = cq.Solid.makeCylinder(MI["bump_r"], 2 * tw, V(-tw, yb_c, z1 + MI["bump_h"] - MI["bump_r"]), V(1, 0, 0))
    bump = bump.intersect(cq.Solid.makeBox(2 * tw, 4 * MI["bump_r"], MI["bump_h"], V(-tw, yb_c - 2 * MI["bump_r"], z1)))
    return r.fuse(bump).clean()


# ---------------------------------------------------------------- A00 desk foot
F = dict(tilt=15.0, base_w=60.0, base_d=72.0, base_t=4.0, up_w=26.0, up_t=6.0, centre_h=80.0)


def upright_local():
    """Upright behind the back face in the display frame; its front face carries the rail."""
    y_top = MI["y_stop"] + 6.0
    return cq.Solid.makeBox(F["up_w"], 140.0, F["up_t"], V(-F["up_w"] / 2, y_top - 140.0, P["back_z"] - F["up_t"]))


def desk_foot():
    """Built in the display frame (rail + upright behind the back face), then tilted back and stood on a base.
    Returns (foot_in_world, transform) where transform places display-frame shapes in the world (Z up)."""
    up = upright_local().fuse(rail_local())
    # display frame -> world: rotate so display Y -> world Z (up), display Z -> world -Y... then tilt back
    def place(s):
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), 90)            # (x,y,z) -> (x,-z,y): display Y up, display front toward -Y
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), -F["tilt"])    # lean back: top moves toward +Y (away from viewer at -Y)
        return s.translate(V(0, 0, F["base_t"] + F["centre_h"]))
    up_w = place(up)
    base_top = F["base_t"]
    up_w = up_w.cut(cq.Solid.makeBox(400, 400, 400, V(-200, -200, base_top - 400)))   # trim at the base top
    sec = up_w.intersect(cq.Solid.makeBox(400, 400, 1.0, V(-200, -200, base_top)))
    sb = sec.BoundingBox()
    yc = (sb.ymin + sb.ymax) / 2
    base = (cq.Workplane("XY").rect(F["base_w"], F["base_d"]).extrude(F["base_t"]).edges("|Z").fillet(6)
            .val().translate(V(0, yc - 6.0, 0)))   # base reaches further forward, under the display
    foot = base.fuse(up_w).clean()
    return foot, place


def main():
    out = {"checks": [], "numbers": {}}
    fail = []

    def check(name, ok, detail):
        out["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            fail.append(name)

    brd = board()
    bb = brd.BoundingBox()
    out["numbers"]["board_bbox"] = [round(v, 2) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)]
    check("board orientation", abs(bb.zmax - B["glass_front"]) < 0.05 and abs(bb.zmin - B["header_bottom"]) < 0.05,
          f"board Z {bb.zmin:.2f}..{bb.zmax:.2f}, want {B['header_bottom']}..{B['glass_front']}")

    d01 = shell()
    d02, holes = back()
    rail = rail_local()

    def inter(a, b):
        try:
            return a.intersect(b).Volume()
        except Exception:
            return -1.0

    v1 = sum(inter(s, d01) for s in brd.Solids())
    v2 = sum(inter(s, d02) for s in brd.Solids())
    v3 = inter(d01, d02)
    rail_nb = rail_local(with_bump=False)
    v4 = inter(rail, d02)
    v4b = inter(rail_nb, d02) + inter(rail_nb, d01)
    v4c = inter(upright_local(), d02) + inter(upright_local(), d01)
    check("board vs shell", 0 <= v1 < 0.01, f"overlap {v1:.4f} mm3")
    check("board vs back", 0 <= v2 < 0.01, f"overlap {v2:.4f} mm3")
    check("shell vs back", 0 <= v3 < 0.01, f"overlap {v3:.4f} mm3")
    check("rail (without bump) vs display unit", 0 <= v4b < 0.01, f"overlap {v4b:.4f} mm3")
    check("upright vs display unit", 0 <= v4c < 0.01, f"overlap {v4c:.4f} mm3")
    out["numbers"]["bump_overlap_nominal_mm3"] = round(v4, 3)   # nominal = rail root on the face; real seat is 0.4 further out

    zf = P["back_z"] + MI["depth"]
    nums = out["numbers"]
    nums["od"] = round(P["od"], 2)
    nums["depth_total"] = round(B["glass_front"] + P["lip_gap"] + P["lip_t"] - P["back_z"], 2)
    nums["header_to_back_inner_face"] = round(B["header_bottom"] - P["split_z"], 2)
    nums["glass_radial_clearance"] = round((P["bore_d"] - B["glass_d"]) / 2, 2)
    nums["mi1_open_w"] = round(MI["open_w"], 3)
    nums["mi1_rail_neck_w"] = round(MI["open_w"] - 2 * MI["clear"] / math.sin(math.radians(MI["angle"])), 3)
    nums["mi1_rail_top_w"] = round(nums["mi1_rail_neck_w"] + 2 * MI["rail_h"] / math.tan(math.radians(MI["angle"])), 3)
    nums["mi1_rail_top_to_floor"] = round(MI["depth"] - MI["rail_h"], 2)
    nums["bump_preload_when_home"] = round(MI["bump_h"] - (MI["depth"] - MI["rail_h"]) - MI["groove_depth"] - MI["axial_play"], 2)
    nums["tongue_deflection_while_sliding"] = round(MI["bump_h"] - (MI["depth"] - MI["rail_h"]) - MI["axial_play"], 2)
    check("detent: preload 0.1-0.3 when home, tongue deflection < void under it",
          0.1 <= nums["bump_preload_when_home"] <= 0.3 and nums["tongue_deflection_while_sliding"] < MI["rail_h"] - MI["tongue_t"] - 0.3,
          f"preload {nums['bump_preload_when_home']}, deflection {nums['tongue_deflection_while_sliding']}, void {MI['rail_h'] - MI['tongue_t']:.2f}")
    # screw stack, M2 x 6 everywhere
    head_seat = P["head_seat_z"]
    nums["board_screw_tip_z"] = round(head_seat + 6.0, 2)
    nums["board_screw_engagement"] = round(head_seat + 6.0 - B["standoff_bottom"], 2)
    nums["board_screw_tip_to_pcb"] = round(B["pcb_bottom"] - (head_seat + 6.0), 2)
    check("M2x6 into the 3.5 standoff: engages 2.5-3.3 mm, tip clear of the PCB",
          2.5 <= nums["board_screw_engagement"] <= 3.3 and nums["board_screw_tip_to_pcb"] > 0.3,
          f"engagement {nums['board_screw_engagement']}, tip {nums['board_screw_tip_to_pcb']} below the PCB")
    nums["shell_screw_engagement_at_axis_min"] = round(P["shell_boss_top"] - 0.8 - P["split_z"], 2)
    check("header clear of the back", nums["header_to_back_inner_face"] >= 0.4, f"{nums['header_to_back_inner_face']} mm")

    # place the display unit on the desk foot and check it
    foot, place = desk_foot()
    du_w = place(d01.fuse(d02))
    dbb = du_w.BoundingBox()
    nums["desk_display_lowest_point_above_base_top"] = round(dbb.zmin - F["base_t"], 1)
    check("display clears the desk foot base for a USB-C plug", dbb.zmin - F["base_t"] > 35, f"{dbb.zmin - F['base_t']:.1f} mm")
    fbb = foot.BoundingBox()
    nums["desk_foot_bbox"] = [round(v, 1) for v in (fbb.xlen, fbb.ylen, fbb.zlen)]

    # exports
    pr = CAD / "print"; pr.mkdir(parents=True, exist_ok=True)
    asm = CAD / "assembly"; asm.mkdir(parents=True, exist_ok=True)
    parts = {
        "D01_PETG_display_shell": d01,
        "D02_PETG_display_back_MI1": d02,   # back face is already the lowest face: prints back face down
        "A00_PETG_desk_foot_MI1": foot,
    }
    # shell prints lip face down
    parts["D01_PETG_display_shell"] = d01.rotate(V(0, 0, 0), V(1, 0, 0), 180)
    manifest = []
    for name, s in parts.items():
        b = s.BoundingBox()
        s = s.translate(V(-(b.xmin + b.xmax) / 2, -(b.ymin + b.ymax) / 2, -b.zmin))
        w = cq.Workplane().add(s)
        for ext in ("step", "stl", "3mf"):
            kw = {"tolerance": 0.02, "angularTolerance": 0.1} if ext in ("stl", "3mf") else {}
            cq.exporters.export(w, str(pr / f"{name}.{ext}"), **kw)
        bb2 = s.BoundingBox()
        manifest.append({"part": name, "volume_mm3": round(s.Volume(), 1), "petg_g": round(s.Volume() / 1000 * 1.27, 1),
                         "size_mm": [round(bb2.xlen, 1), round(bb2.ylen, 1), round(bb2.zlen, 1)]})
    (pr / "manifest.json").write_text(json.dumps(manifest, indent=2))
    # without the board: its 3D model makes each assembly file 188 MB
    cq.exporters.export(cq.Workplane().add(cq.Compound.makeCompound([d01, d02])), str(asm / "display_unit.step"))
    cq.exporters.export(cq.Workplane().add(cq.Compound.makeCompound([foot, du_w])), str(asm / "desk_foot_with_display_unit.step"))
    out["parts"] = manifest
    out["failed"] = fail
    (CAD / "checks").mkdir(parents=True, exist_ok=True)
    (CAD / "checks" / "fit_check.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
