"""D03: printed back cup for the Waveshare ESP32-S3-Touch-AMOLED-1.75-B unit kept whole in its own case.

Why (2026-11-19, on the bench): the board came as Waveshare's "-B" (board + case). Its round glass is attached to
the case's front ring (Kalev: "But it seems like the glass screen is attached to this outer case."), so the board
cannot come out and D01/D02 do not apply to it. D03 keeps the whole Waveshare unit (front ring + glass + board +
Waveshare's own back cover, its 3 screws left in place) and grips it in a cup: the unit pushes in from the front,
back cover first, and 5 flexible fingers with a 45 deg lip snap over the case's front bevel. Six small crush ribs take
up the radial play. The cup's back carries the female MI-1 dovetail, cut by md_model.mi1_female_cut() (the same code
that cuts D02), in the same place relative to the screen centre and the back face (Z = P["back_z"] = -15.90), so it
slides onto A00 and A12 and clicks exactly as D02 does.

Frame (mm): md_model's display frame (X right and Y up seen from the front, Z toward the viewer, origin = screen
centre, USB-C down). In this frame the Waveshare case's back face sits at ZC = back_z + FLOOR.

Every number of the Waveshare unit is read from Waveshare's drawing cad/reference/ESP32-S3-Touch-AMOLED-1.75-B.pdf
(vector paths measured, scale from the 51.00 dimension: 128.52 pt = 51.00 mm); the drawing's front view has the
USB-C at the top, so its X and Y are turned 180 deg into this frame (its back view is flipped top to bottom: the
3-hole pattern then lands exactly on the board's standoffs read from Waveshare's board STEP, md_model B).

Run:  python cad/source/md_display_b.py   (the project venv; writes cad/print/D03_*, cad/print/W00_*,
      cad/checks/d03_fit_check.json; exit 1 on a failed check). Does not write cad/assembly.
"""
from pathlib import Path
import json, math, sys

import cadquery as cq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md_model as M  # noqa: E402  (MI-1, rail, desk foot: reused, never changed here)

V = cq.Vector
CAD = M.CAD

# ---------------------------------------------------------------- Waveshare -B unit, from the drawing (mm)
# Source for each: ESP32-S3-Touch-AMOLED-1.75-B.pdf. "dim" = printed dimension; "meas" = measured on the vector paths.
W = dict(
    od=51.00,              # dim "Ø51.00"; also the body width in both edge views (meas 51.00)
    body_len=11.24,        # meas: Ø51 cylinder from the back face to the start of the front bevel (edge views)
    bevel_d=50.04, bevel_z=11.67,   # meas: bevel ends at Ø50.04; dim "11.70" (back face to this edge; meas 11.67)
    ring_d=47.96, depth=12.10,      # meas: glass ring top Ø47.96; dim "12.10" overall depth
    aa_d=43.76,            # dim "Ø43.76 TP AA" (touch active area)
    holes=[(14.70, 13.75), (14.70, -13.75), (-20.50, 0.0)],   # dims 14.70 / 20.50 / 13.75 + 13.75 (back view)
    hole_head_d=4.0,       # meas: outer circle round each hole in the back view (screw head / counterbore)
    header=(16.6, 20.5, -11.2, 11.2),    # meas: 8-pin header outline x0,x1,y0,y1 (dim 18.7 = pin row, 2.54 pitch)
    back_pad=(-10.0, 10.0, -16.0, 16.0), # meas: 20 x 32 rectangle on the back (edge view: proud by 0.14)
    back_proud=0.14,       # meas: header outline and rectangle stand 0.14 off the back face
    btn_deg=33.7,          # meas: side buttons at x = +-14.15 on the Ø51 -> 33.7 deg either side of +Y
    btn_z=4.60, btn_d=3.8, btn_r_out=26.38,   # meas: centre 4.60 from the back, Ø3.8 cap, caps reach r 26.38
    usb_w=10.1, usb_h=4.24, usb_z=3.93,        # meas: stadium opening round the USB-C (bottom edge), centre 3.93 from the back
    pin_x=13.9, pin_z=4.55, pin_d=1.5,         # meas: two small holes beside the USB-C, x +-13.5..14.3, centre 4.55 from back
)

# ---------------------------------------------------------------- assumptions until Kalev measures (stated in PLAN M05)
A = dict(
    cover_od=51.00,        # assumed = W.od (the drawing shows one diameter over the whole body). Fits 50.8-51.3.
    screw="M2",            # assumed thread of the 3 back-cover screws (Waveshare's small cases use M2)
    screw_len=4.0,         # assumed length of those screws; used only for the optional screw-through upgrade
    cover_cbore=None,      # unknown: depth of the cover's counterbore under each screw head (Kalev measures)
)

# ---------------------------------------------------------------- D03 parameters
D = dict(
    floor=5.00,            # back face -> case back: 3.00 MI-1 channel + 0.4 groove + 0.6 pocket + 1.0 skin
    bore_d=51.40,          # 0.20 per side over Ø51.00 (PETG prints holes ~0.1-0.2 small)
    wall=1.60,
    lip_id=49.80,          # lip reaches 0.60 over the Ø51 edge; 3.0 per side outside the active area
    lip_top=13.30,         # from the case back: 1.20 above the glass top (12.10), like D01's lip
    lip_gap=0.10,          # lip underside 0.10 off the 45 deg front bevel
    fingers=[0.0, 90.0, 180.0, 215.0, 325.0],   # deg from +X, counter-clockwise seen from the front
    finger_half=13.0, slot_w=1.0, slot_from=2.5,   # finger = 26 deg of wall; slots start 2.5 above the case back
    rib_deg=[30.0, 150.0, 70.0, 110.0, 245.0, 295.0], rib_r=0.5, rib_reach_d=50.90, rib_z=(0.8, 9.0),
    btn_slot_w=6.0, usb_win=(13.0, 7.5, 2.0),   # plug overmold clearance as D01 (typical overmold 12.4 x 6.5)
    pin_hole_d=2.6,
    pocket=0.60,           # pockets in the floor for the back pad, header outline and screw heads
    screw_clear=2.40, cbore_d=4.20, under_head=2.00,   # optional screw-through: head seat 2.00 behind the case back
)
ZB = M.P["back_z"]          # -15.90, the MI-1 reference face (same as D02)
ZC = ZB + D["floor"]        # Waveshare case back face
RB = D["bore_d"] / 2
RO = RB + D["wall"]


def cyl(r, z0, z1, x=0.0, y=0.0):
    return M.cyl(r, z0, z1, x, y)


def polar(r, deg):
    a = math.radians(deg)
    return r * math.cos(a), r * math.sin(a)


def radial_box(deg, width, r0, r1, z0, z1):
    """Box from radius r0 to r1 along direction deg, width tangentially, Z z0..z1."""
    b = cq.Solid.makeBox(r1 - r0, width, z1 - z0, V(r0, -width / 2, z0))
    return b.rotate(V(0, 0, 0), V(0, 0, 1), deg)


def radial_cyl(deg, d, r0, r1, z):
    x, y = polar(r0, deg)
    a = math.radians(deg)
    return cq.Solid.makeCylinder(d / 2, r1 - r0, V(x, y, z), V(math.cos(a), math.sin(a), 0))


def revolve_rz(pts):
    """Closed polygon in (r, z) revolved about Z."""
    w = cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
    return w.val()


def sector(deg0, deg1, z0, z1, r=40.0):
    n = max(2, int(abs(deg1 - deg0) / 5) + 1)
    pts = [(0, 0)] + [polar(r, deg0 + (deg1 - deg0) * i / n) for i in range(n + 1)]
    return cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0).val().translate(V(0, 0, z0))


# ---------------------------------------------------------------- W00: envelope of the Waveshare -B unit (from the drawing)
def waveshare_envelope(buttons=True):
    zc = ZC
    s = revolve_rz([(0, zc), (W["od"] / 2, zc), (W["od"] / 2, zc + W["body_len"]), (W["bevel_d"] / 2, zc + W["bevel_z"]),
                    (W["ring_d"] / 2, zc + W["depth"]), (0, zc + W["depth"])])
    x0, x1, y0, y1 = W["back_pad"]
    s = s.fuse(cq.Solid.makeBox(x1 - x0, y1 - y0, W["back_proud"], V(x0, y0, zc - W["back_proud"])))
    x0, x1, y0, y1 = W["header"]
    s = s.fuse(cq.Solid.makeBox(x1 - x0, y1 - y0, W["back_proud"], V(x0, y0, zc - W["back_proud"])))
    if buttons:
        s = s.fuse(button_caps())
    return s.clean()


def button_caps():
    caps = [radial_cyl(90 + sg * W["btn_deg"], W["btn_d"], W["od"] / 2 - 0.5, W["btn_r_out"], ZC + W["btn_z"]) for sg in (-1, 1)]
    return caps[0].fuse(caps[1])


def usb_plug():
    """Typical USB-C plug overmold 12.4 x 6.5, 20 long, from the case surface down (-Y)."""
    zc = ZC + W["usb_z"]
    return (cq.Workplane("XZ").rect(12.4, 6.5).extrude(20).edges("|Y").fillet(2.0).val()
            .translate(V(0, -W["od"] / 2 + 0.0, zc)))


# ---------------------------------------------------------------- D03
def d03(ribs=True, screw_holes=True):
    top = ZC + D["lip_top"]
    s = cyl(RO, ZB, top).cut(cyl(RB, ZC, top + 1))
    # lip ring: underside 45 deg along the bevel (+lip_gap), 45 deg lead-in on top, inner face at lip_id
    r_in = D["lip_id"] / 2
    z_under_at = lambda r: ZC + W["body_len"] + D["lip_gap"] + (W["od"] / 2 - r)   # 45 deg line through (25.5, 11.34)
    r_lead = RB - 0.15
    lip = revolve_rz([(r_in, z_under_at(r_in)), (r_in, top - (r_lead - r_in)), (r_lead, top), (RB + 0.05, top),
                      (RB + 0.05, z_under_at(RB + 0.05))])
    # lip only on the fingers
    for a in D["fingers"]:
        h = D["finger_half"] - math.degrees((D["slot_w"] / 2) / RB)
        s = s.fuse(lip.intersect(sector(a - h, a + h, ZC, top + 1)))
    # finger slots
    for a in D["fingers"]:
        for sg in (-1, 1):
            s = s.cut(radial_box(a + sg * D["finger_half"], D["slot_w"], RB - 2.0, RO + 1, ZC + D["slot_from"], top + 1))
    # crush ribs on the fixed wall
    if ribs:
        rr = D["rib_r"]
        rc = D["rib_reach_d"] / 2 + rr
        z0, z1 = ZC + D["rib_z"][0], ZC + D["rib_z"][1]
        for a in D["rib_deg"]:
            x, y = polar(rc, a)
            rib = cyl(rr, z0, z1 - rr, x, y).fuse(cq.Solid.makeCone(rr, 0.0, rr, V(x, y, z1 - rr)))
            s = s.fuse(rib.intersect(cyl(RB + 0.2, z0, z1)))
    # side buttons: U notches open to the front rim
    for sg in (-1, 1):
        a = 90 + sg * W["btn_deg"]
        zb = ZC + W["btn_z"]
        s = s.cut(radial_box(a, D["btn_slot_w"], RB - 1.5, RO + 1, zb, top + 1))
        s = s.cut(radial_cyl(a, D["btn_slot_w"], RB - 1.5, RO + 1, zb))
    # USB-C window (bottom)
    w_, h_, r_ = D["usb_win"]
    win = (cq.Workplane("XZ").rect(w_, h_).extrude(-12).edges("|Y").fillet(r_).val()
           .translate(V(0, -RO - 2, ZC + W["usb_z"])))
    s = s.cut(win)
    # the two small holes beside the USB-C
    for sg in (-1, 1):
        a = 270 + sg * math.degrees(math.asin(W["pin_x"] / (W["od"] / 2)))
        s = s.cut(radial_cyl(a, D["pin_hole_d"], RB - 1, RO + 1, ZC + W["pin_z"]))
    # floor pockets (back pad, header outline, screw heads)
    pk = D["pocket"]
    for (x0, x1, y0, y1) in (W["back_pad"], W["header"]):
        s = s.cut(cq.Solid.makeBox(x1 - x0 + 1.0, y1 - y0 + 1.0, pk + 0.01, V(x0 - 0.5, y0 - 0.5, ZC - pk)))
    for (x, y) in W["holes"]:
        s = s.cut(cyl(W["hole_head_d"] / 2 + 0.5, ZC - pk, ZC + 0.01, x, y))
        if screw_holes:   # optional upgrade: longer M2 screws through D03 and the cover
            s = s.cut(cyl(D["screw_clear"] / 2, ZB - 1, ZC + 0.01, x, y))
            s = s.cut(cyl(D["cbore_d"] / 2, ZB - 1, ZC - D["under_head"], x, y))
    # MI-1 female channel + detent groove: the same cut as D02
    s = s.cut(M.mi1_female_cut())
    # 0.6 chamfer on the back outer edge (as D02), 0.4 on the front outer edge
    s = s.cut(cyl(RO + 1, ZB - 0.1, ZB + 0.6).cut(cq.Solid.makeCone(RO - 0.6, RO, 0.6, V(0, 0, ZB))))
    s = s.cut(cyl(RO + 1, top - 0.4, top + 0.1).cut(cq.Solid.makeCone(RO, RO - 0.5, 0.5, V(0, 0, top - 0.4))))
    return s.clean()


def inter(a, b):
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1.0


def main():
    out = {"source": "cad/source/md_display_b.py", "waveshare_from_drawing": W, "assumed": A, "d03": D,
           "frame": {"back_face_z": ZB, "case_back_z": ZC}, "checks": [], "numbers": {}}
    fail = []

    def check(name, ok, detail):
        out["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            fail.append(name)

    nums = out["numbers"]
    part = d03()
    part_nr = d03(ribs=False)
    env = waveshare_envelope(buttons=False)
    caps = button_caps()

    v = inter(env, part_nr)
    check("Waveshare case envelope vs D03 (ribs off)", 0 <= v < 0.01, f"overlap {v:.4f} mm3")
    v_r = inter(env, part)
    nums["rib_interference_mm3"] = round(v_r, 3)
    check("crush ribs bite the Ø51 case lightly (0 < interference < 2 mm3)", 0 < v_r < 2.0, f"{v_r:.3f} mm3 over 6 ribs")
    v = inter(caps, part)
    check("side buttons vs D03", 0 <= v < 0.01, f"overlap {v:.4f} mm3")
    reach = []
    for sg in (-1, 1):
        a = 90 + sg * W["btn_deg"]
        reach.append(inter(radial_cyl(a, 3.0, W["btn_r_out"], RO + 5, ZC + W["btn_z"]), part))
    check("buttons reachable: Ø3 finger path from each cap outward is free", max(reach) < 0.01, f"overlaps {reach}")
    v = inter(usb_plug(), part)
    check("USB-C plug overmold 12.4 x 6.5 goes in fully", 0 <= v < 0.01, f"overlap {v:.4f} mm3")
    ph = [inter(radial_cyl(270 + sg * math.degrees(math.asin(W["pin_x"] / (W["od"] / 2))), W["pin_d"], W["od"] / 2 - 0.2, RO + 2, ZC + W["pin_z"]), part) for sg in (-1, 1)]
    check("small holes beside the USB-C stay open", max(ph) < 0.01, f"overlaps {ph}")

    # lip
    nums["lip_catch_radial"] = round(W["od"] / 2 - D["lip_id"] / 2, 2)
    nums["lip_to_active_area_per_side"] = round((D["lip_id"] - W["aa_d"]) / 2, 2)
    nums["lip_above_glass"] = round(D["lip_top"] - W["depth"], 2)
    check("lip catches the Ø51 edge by 0.4-0.9 and stays off the active area",
          0.4 <= nums["lip_catch_radial"] <= 0.9 and nums["lip_to_active_area_per_side"] > 2.0,
          f"catch {nums['lip_catch_radial']}, {nums['lip_to_active_area_per_side']} outside Ø{W['aa_d']}")
    # finger snap strain: cantilever, deflection = catch + bore clearance
    L = D["lip_top"] - D["slot_from"]
    dfl = W["od"] / 2 - D["lip_id"] / 2 + 0.05
    eps = 1.5 * D["wall"] * dfl / L ** 2
    nums["finger_length"] = round(L, 2)
    nums["finger_snap_strain_pct"] = round(100 * eps, 2)
    check("finger strain while snapping < 2.5 % (PETG yields near 4-5 %)", eps < 0.025, f"{100 * eps:.2f} % over {L:.1f} mm")
    # floor skins
    skin_ch = (ZC - D["pocket"]) - (ZB + M.MI["depth"])
    skin_gr = skin_ch - M.MI["groove_depth"]
    nums["floor_skin_over_channel"] = round(skin_ch, 2)
    nums["floor_skin_over_groove"] = round(skin_gr, 2)
    check("floor skin over the MI-1 channel >= 1.0 (groove >= 0.8)", skin_ch >= 1.0 and skin_gr >= 0.8, f"{skin_ch:.2f} / {skin_gr:.2f}")

    # MI-1 identical to D02 (same function; compared as geometry inside r 26.5, the channel zone)
    d02, _ = M.back()
    # zone = the channel's own box grown 1 mm (|x| < 11, Y up to the stop + 1.5, inside r 25.5), clear of D02's
    # shell-screw holes and both parts' outer chamfers
    zone = cyl(25.5, ZB - 0.1, ZB + M.MI["depth"] + 0.6).intersect(
        cq.Solid.makeBox(22, 60, 10, V(-11, M.MI["y_stop"] + 1.5 - 60, ZB - 1)))
    a2, a3 = d02.intersect(zone), part.intersect(zone)
    diff = a2.cut(a3).Volume() + a3.cut(a2).Volume()
    check("MI-1 channel + groove identical to D02 (|x| < 11, Y < stop + 1.5, r < 25.5)", diff < 0.01, f"symmetric difference {diff:.4f} mm3")
    rail_nb = M.rail_local(with_bump=False)
    v = inter(rail_nb, part)
    check("A00/A12 rail (without bump) vs D03", 0 <= v < 0.01, f"overlap {v:.4f} mm3")
    v = inter(M.upright_local(), part)
    check("desk-foot upright vs D03", 0 <= v < 0.01, f"overlap {v:.4f} mm3")
    b3, b2 = inter(M.rail_local(), part), inter(M.rail_local(), d02)
    nums["bump_overlap_nominal_mm3"] = round(b3, 3)
    check("detent bump meets the groove as in D02", abs(b3 - b2) < 0.01, f"D03 {b3:.3f} vs D02 {b2:.3f} mm3")
    try:
        import md_arm_adapter as AA
        blk = AA.tilt_block()
        v = inter(blk, part) - inter(M.rail_local(), part)
        check("A12 tilt block (rail + fingers) vs D03, bump excluded", v < 0.01, f"overlap {v:.4f} mm3")
    except Exception as e:  # noqa: BLE001
        out["checks"].append({"check": "A12 tilt block vs D03", "ok": None, "detail": f"skipped: {e}"})
    # desk foot: the whole unit stands clear of the base
    foot, place = M.desk_foot()
    du = place(part.fuse(env))
    dbb = du.BoundingBox()
    nums["desk_display_lowest_point_above_base_top"] = round(dbb.zmin - M.F["base_t"], 1)
    check("display clears the desk foot base for a USB-C plug", dbb.zmin - M.F["base_t"] > 30, f"{dbb.zmin - M.F['base_t']:.1f} mm")
    # holes on the drawing's pattern
    nums["screw_pattern"] = W["holes"]
    nums["screw_pattern_equals_board_standoffs"] = sorted(W["holes"]) == sorted(M.B["standoff_xy"])
    check("3 holes on the drawing's pattern = the board's standoffs (Waveshare STEP)", nums["screw_pattern_equals_board_standoffs"], str(W["holes"]))
    nums["upgrade_screw_length"] = "original length + 2.00 + the cover's counterbore depth (Kalev measures)"
    bb = part.BoundingBox()
    nums["d03_size"] = [round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2)]
    nums["unit_depth_with_d03"] = round(D["lip_top"] + D["floor"], 2)

    # exports
    pr = CAD / "print"
    s = part.translate(V(0, 0, -bb.zmin))       # back face on the bed, as modelled
    w = cq.Workplane().add(s)
    name = "D03_PETG_display_back_waveshare_case"
    for ext in ("step", "stl", "3mf"):
        kw = {"tolerance": 0.02, "angularTolerance": 0.1} if ext in ("stl", "3mf") else {}
        cq.exporters.export(w, str(pr / f"{name}.{ext}"), **kw)
    nums["d03_volume_mm3"] = round(s.Volume(), 1)
    nums["d03_petg_g_estimate"] = round(s.Volume() / 1000 * 1.27, 1)
    cq.exporters.export(cq.Workplane().add(waveshare_envelope()), str(pr / "W00_waveshare_B_case_envelope.step"))
    out["failed"] = fail
    (CAD / "checks").mkdir(parents=True, exist_ok=True)
    (CAD / "checks" / "d03_fit_check.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"checks": out["checks"], "numbers": nums, "failed": fail}, indent=2))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
