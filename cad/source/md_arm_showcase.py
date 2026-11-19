"""Showcase: the display and clamp A10-A12 on Eino's WHOLE arm, in his own CAD pose, for looking at (not for checks).

Reads Eino's assembly STEP (cad/reference/arm_eino_step/A00_..., git-ignored) with every part in his pose, places the
clamp on the upper bar exactly as md_arm_adapter.py does (same functions, display on the user's right), adds the bought
hardware as simple solids (2 x M4x10 set screw, 2 x M4 nut, M5x25 + washer + nyloc) and writes, all git-ignored
because they contain Eino's geometry:
  cad/assembly/showcase/MD_showcase_on_Eino_arm.step            every part a named, coloured component
  cad/assembly/showcase/MD_showcase_on_Eino_arm_exploded.step   the same with the clamp parts pulled apart
  cad/assembly/showcase/showcase_parts.json                     names, groups, colours, explode vectors (A-frame mm)
  viewer/models/showcase.glb                                    one mesh per part (metres, y up), explode vector in
                                                                each node's extras, for viewer/index.html
Display: Waveshare's -B case kept whole (W00 envelope) + printed back D03 when cad/print/W00_*.step and
cad/print/D03_PETG_*.step exist; until then D01 + D02 as placeholder.

SolidWorks: cad/source/solidworks/sw_showcase.ps1 -Mode build, then -Mode final, turns the parts/ STEPs into the two SLDASM files.
Run (Windows):  %LOCALAPPDATA%\\mic-display\\venv\\Scripts\\python.exe cad\\source\\md_arm_showcase.py
"""
from pathlib import Path
import json, math, struct, sys

import numpy as np
import cadquery as cq
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name

sys.path.insert(0, str(Path(__file__).resolve().parent))
import md_arm_adapter as A  # noqa: E402  (functions only; its main() is not run)
import md_model as M        # noqa: E402

ROOT = A.ROOT
OUT = ROOT / "cad" / "assembly" / "showcase"
VIEW = ROOT / "viewer" / "models"
SIDE = -1          # display on the user's right (Eino, 2026-11-19); the printed A10 is base[-1]
EPS = 50.0         # display tilt shown: glass normal 50 deg above the bar (the pose of arm_adapter_on_bar.step)

ARM_NAMES = {  # Eino's part numbers -> plain English, for the viewer and the SolidWorks tree
    "P01": "desk clamp", "P02": "swivel foot", "P03": "bar", "P04": "elbow", "P05": "head", "P06": "tilt piece",
    "P07": "clamp plate", "P08": "clamp knob", "P09": "Yeti (space)", "P10": "desk (helper)", "P11": "spring plug",
    "P12": "lower spring", "P13": "upper spring", "P19": "Yeti cradle",
}
COL = {  # rgb 0..1
    "alu": (0.70, 0.72, 0.75), "arm": (0.50, 0.52, 0.55), "spring": (0.36, 0.38, 0.41), "desk": (0.80, 0.74, 0.64),
    "yeti": (0.42, 0.44, 0.47), "petg": (0.95, 0.50, 0.12), "pad": (0.16, 0.52, 0.93), "steel": (0.20, 0.21, 0.23),
    "display": (0.05, 0.05, 0.06), "glass": (0.02, 0.02, 0.03),
}


# ------------------------------------------------------------------ Eino's assembly, read with its own placements
def read_eino_assembly():
    f = A.ARM / "A00_Mikrofonivarsi_Yeti_2palkki_v2.step"
    if not f.exists():
        sys.exit(f"missing {f}: Eino's STEP export goes in cad/reference/arm_eino_step/ (AGENTS.md)")
    doc = TDocStd_Document(TCollection_ExtendedString("eino"))
    r = STEPCAFControl_Reader(); r.SetNameMode(True)
    r.ReadFile(str(f)); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots = TDF_LabelSequence(); st.GetFreeShapes(roots)

    def name(lab):
        a = TDataStd_Name()
        return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else "?"

    comps = TDF_LabelSequence(); st.GetComponents_s(roots.Value(1), comps, False)
    shapes, inst = {}, []
    for j in range(1, comps.Length() + 1):
        c = comps.Value(j); ref = TDF_Label(); st.GetReferredShape_s(c, ref)
        n = name(ref)
        if n not in shapes:
            shapes[n] = cq.Shape.cast(st.GetShape_s(ref))
        T = st.GetLocation_s(c).Transformation()
        m = np.eye(4); m[:3, :] = [[T.Value(a, b) for b in range(1, 5)] for a in range(1, 4)]
        inst.append((n, m))
    return shapes, inst


# ------------------------------------------------------------------ hardware (bar frame, display on +z; mirrored for SIDE -1)
def hex_z(af, x, y, z0, z1, flats_x=True):
    R = af / math.sqrt(3)
    pts = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    if flats_x:   # points on +-y, flats facing +-x (the M4 nut pocket in A10)
        pts = [(-b, a) for a, b in pts]
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline([(x + a, y + b) for a, b in pts]).close().extrude(z1 - z0).val()


def set_screw(xs):
    """M4x10 ISO 4026 flat point, tip in the pad's dimple, 2 mm hex socket at the back end."""
    tip = A.CL["pad"][2] + A.CL["dimple"][1]
    back = tip - 10.0
    s = A.cyl_z(2.0, xs, A.CL["screw_y"], back, tip)
    return s.cut(hex_z(2.0, xs, A.CL["screw_y"], back - 0.01, back + 2.0, flats_x=False))


def m4_nut(xs):
    nz0, nz1 = sorted(A.CL["nut_z"])
    zc = (nz0 + nz1) / 2
    n = hex_z(7.0, xs, A.CL["screw_y"], zc - 1.6, zc + 1.6)
    return n.cut(A.cyl_z(2.0, xs, A.CL["screw_y"], zc - 2, zc + 2))


def m5_set():
    ax = A.KN["axis"]; zt = A.KN["fingers"][-1][1]; bz0 = A.KN["boss"][0]
    washer = A.cyl_z(5.0, ax[0], ax[1], zt, zt + 1.0).cut(A.cyl_z(2.7, ax[0], ax[1], zt - 1, zt + 2))
    head = A.cyl_z(4.25, ax[0], ax[1], zt + 1.0, zt + 6.0).cut(hex_z(4.0, ax[0], ax[1], zt + 3.0, zt + 6.01, flats_x=False))
    bolt = head.fuse(A.cyl_z(2.5, ax[0], ax[1], zt + 1.0 - 25.0, zt + 1.0))
    z1 = bz0 + A.KN["nyloc_depth"]
    nyloc = hex_z(8.0, ax[0], ax[1], z1 - 5.0, z1, flats_x=False).cut(A.cyl_z(2.5, ax[0], ax[1], z1 - 6, z1 + 1))
    return bolt.clean(), washer.clean(), nyloc.clean()


def mirror(s):
    return s.mirror("XY") if SIDE < 0 else s


# ------------------------------------------------------------------ the display: W00 + D03 when they exist, else D01 + D02
def display_parts():
    """[(name, shape in the display frame, colour key, label)], plus which variant was used."""
    pr = ROOT / "cad" / "print"
    w00 = sorted(pr.glob("W00_*.step")); d03 = sorted(pr.glob("D03_PETG_*.step"))
    if w00 and d03:
        try:   # md_display_b.py builds both in md_model's display frame (X right, Y up on the glass, Z to the viewer)
            import md_display_b as DB
            return [("W00 Waveshare case kept whole", DB.waveshare_envelope(), "display", "W00"),
                    ("D03 printed back PETG", DB.d03(), "petg", "D03")], "W00+D03"
        except Exception as e:  # noqa: BLE001
            print(f"W00/D03 files exist but md_display_b could not build them ({e}); using D01 + D02", flush=True)
    d02, _ = M.back()
    return [("D01 display shell (placeholder)", M.shell(), "display", "D01"), ("D02 display back (placeholder)", d02, "display", "D02")], "D01+D02 placeholder"


# ------------------------------------------------------------------ GLB writer (no extra packages)
def tess(shape, tol, ang):
    vs, ts = shape.tessellate(tol, ang)
    v = np.array([(p.x, p.y, p.z) for p in vs], dtype=np.float64)
    t = np.array(ts, dtype=np.uint32).reshape(-1, 3)
    return v, t


def write_glb(path, parts):
    """parts: [dict(name, v (n,3) metres, t (m,3), color, extras)] -> one node + mesh + material each."""
    bin_ = bytearray(); views, accs, meshes, nodes, mats = [], [], [], [], []
    mat_idx = {}

    def add_view(data, target):
        while len(bin_) % 4:
            bin_.append(0)
        views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data), "target": target})
        bin_.extend(data)
        return len(views) - 1

    for p in parts:
        v = p["v"].astype(np.float32); t = p["t"]
        it = np.uint16 if len(v) < 65536 else np.uint32
        bv = add_view(v.tobytes(), 34962)
        accs.append({"bufferView": bv, "componentType": 5126, "count": len(v), "type": "VEC3",
                     "min": v.min(0).tolist(), "max": v.max(0).tolist()})
        pa = len(accs) - 1
        bi = add_view(t.astype(it).ravel().tobytes(), 34963)
        accs.append({"bufferView": bi, "componentType": 5123 if it is np.uint16 else 5125, "count": int(t.size), "type": "SCALAR"})
        ia = len(accs) - 1
        key = p["mat"]
        if key not in mat_idx:
            c = COL[key]
            rough, metal = {"steel": (0.45, 0.8), "alu": (0.4, 0.6), "spring": (0.45, 0.7), "glass": (0.15, 0.0)}.get(key, (0.65, 0.0))
            lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]   # glTF colour factors are linear
            mats.append({"name": key, "pbrMetallicRoughness": {"baseColorFactor": [*lin, 1.0], "metallicFactor": metal, "roughnessFactor": rough},
                         "doubleSided": True})
            mat_idx[key] = len(mats) - 1
        meshes.append({"name": p["name"], "primitives": [{"attributes": {"POSITION": pa}, "indices": ia, "material": mat_idx[key]}]})
        nodes.append({"name": p["name"], "mesh": len(meshes) - 1, "extras": p["extras"]})
    while len(bin_) % 4:
        bin_.append(0)
    gltf = {"asset": {"version": "2.0", "generator": "mic-display md_arm_showcase.py"}, "scene": 0,
            "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes, "materials": mats,
            "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(bin_)}]}
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942)); f.write(bin_)


# ------------------------------------------------------------------ main
def main():
    OUT.mkdir(parents=True, exist_ok=True); VIEW.mkdir(parents=True, exist_ok=True)
    shapes, inst = read_eino_assembly()
    bars = [(n, m) for n, m in inst if n.startswith("P03")]
    Mu = max(bars, key=lambda b: b[1][0, 3])[1]          # the upper bar is the one nearer the head (larger x)
    Ru = Mu[:3, :3]

    items = []   # dict(name, shape, m (4x4 world), mat, group, explode (world mm), label)
    count = {}
    for n, m in inst:
        code = n[:3]
        count[code] = count.get(code, 0) + 1
        extra = ""
        if code == "P03":
            extra = " upper" if m is Mu else " lower"
        elif count[code] > 1 or sum(1 for k, _ in inst if k[:3] == code) > 1:
            extra = f" {count[code]}"
        mat = {"P03": "alu", "P12": "spring", "P13": "spring", "P10": "desk", "P09": "yeti"}.get(code, "arm")
        items.append(dict(name=f"Eino {code} {ARM_NAMES.get(code, n)}{extra}", shape=shapes[n], m=m, mat=mat, group="arm",
                          explode=[0, 0, 0], label=n))

    def bar_vec(v):
        return (Ru @ np.array(v, dtype=float)).tolist()

    md = A.display_to_bar(EPS, SIDE)
    zdir = SIDE   # +1: display on +z of the bar; the screw wall is on the opposite side
    slide = (md[:3, :3] @ np.array([0.0, 45.0, 0.0]))     # display slides up off A12's rail
    a12_out = np.array([0.0, 0.0, zdir * 35.0])
    items += [
        dict(name="A10 clamp saddle (PETG)", shape=A.clamp_base(SIDE), m=Mu, mat="petg", group="clamp", explode=[0, 0, 0], label="A10"),
        dict(name="A11 pressure pad (PETG)", shape=A.clamp_pad(SIDE), m=Mu, mat="pad", group="clamp", explode=bar_vec([0, 55, 0]), label="A11"),
    ]
    for i, xs in enumerate(A.CL["screw_x"], start=1):
        items.append(dict(name=f"M4x10 set screw {i}", shape=mirror(set_screw(xs)), m=Mu, mat="steel", group="screws",
                          explode=bar_vec([0, 0, -zdir * 40]), label="M4 set screw"))
        items.append(dict(name=f"M4 nut {i}", shape=mirror(m4_nut(xs)), m=Mu, mat="steel", group="screws",
                          explode=bar_vec([0, 35, 0]), label="M4 nut"))
    bolt, washer, nyloc = m5_set()
    items += [
        dict(name="A12 tilt block (PETG)", shape=A.tilt_block(), m=Mu @ md, mat="petg", group="hinge", explode=bar_vec(a12_out), label="A12"),
        dict(name="M5x25 hinge bolt", shape=mirror(bolt), m=Mu, mat="steel", group="hinge", explode=bar_vec([0, 0, zdir * 75]), label="M5x25"),
        dict(name="M5 washer", shape=mirror(washer), m=Mu, mat="steel", group="hinge", explode=bar_vec([0, 0, zdir * 65]), label="M5 washer"),
        dict(name="M5 nyloc nut", shape=mirror(nyloc), m=Mu, mat="steel", group="hinge", explode=bar_vec([0, 0, -zdir * 30]), label="M5 nyloc"),
    ]
    disp, variant = display_parts()
    for name, s, mat, lab in disp:
        items.append(dict(name=name, shape=s, m=Mu @ md, mat=mat, group="display",
                          explode=bar_vec(a12_out + slide), slide=bar_vec(slide), label=lab,
                          pull=bar_vec(md[:3, 2] * 28.0) if lab == "W00" else [0, 0, 0]))   # case drawn forward out of D03
    print(f"display: {variant}; {len(items)} components", flush=True)

    # ---- STEP assemblies (assembled + exploded), named and coloured
    for tag, ex in (("", False), ("_exploded", True)):
        asy = cq.Assembly(name="MD_showcase_on_Eino_arm" + tag)
        for it in items:
            m = it["m"].copy()
            if ex:
                m = A.tr(*it["explode"]) @ m
            c = COL[it["mat"]]
            asy.add(it["shape"], name=it["name"].replace(" ", "_").replace("(", "").replace(")", "").replace("+", "and"),
                    loc=A.loc(m), color=cq.Color(*c, 1.0))
        asy.export(str(OUT / f"MD_showcase_on_Eino_arm{tag}.step"))
    # ---- one STEP per distinct part (own frame) + placements, for building the SolidWorks assembly from parts
    pdir = OUT / "parts"; pdir.mkdir(exist_ok=True)
    files, place = {}, []
    for it in items:
        key = id(it["shape"])
        if key not in files:
            base = it["name"].rstrip("0123456789 ").replace(" lower", "").replace(" upper", "") if it["group"] == "arm" else it["name"]
            fn = "_".join(w for w in "".join(ch if ch.isalnum() else "_" for ch in base).split("_") if w)
            while fn in files.values():
                fn += "_b"
            files[key] = fn
            cq.exporters.export(cq.Workplane().add(it["shape"]), str(pdir / f"{fn}.step"))
        place.append({"name": it["name"], "file": files[key], "mat": it["mat"], "rgb": COL[it["mat"]],
                      "m": it["m"].tolist(), "m_exploded": (A.tr(*it["explode"]) @ it["m"]).tolist()})
    (OUT / "placements.json").write_text(json.dumps(place, indent=1))
    (OUT / "showcase_parts.json").write_text(json.dumps(
        {"display_variant": variant, "display_tilt_deg": EPS, "side": "right",
         "upper_bar_matrix": Mu.tolist(), "display_y_dir": (Ru @ md[:3, 1]).tolist(),
         "parts": [{k: it[k] for k in ("name", "mat", "group", "explode", "label")} | {"rgb": COL[it["mat"]]} for it in items]}, indent=1))

    # ---- GLB for the viewer: coarse on Eino's parts, fine on ours; bake the world placement, metres
    cache, glb = {}, []
    for it in items:
        key = id(it["shape"])
        if key not in cache:
            tol = (0.35, 0.5) if it["group"] == "arm" else (0.04, 0.2)
            cache[key] = tess(it["shape"], *tol)
        v, t = cache[key]
        vw = (it["m"] @ np.c_[v, np.ones(len(v))].T).T[:, :3] / 1000.0
        glb.append(dict(name=it["name"], v=vw, t=t, mat=it["mat"],
                        extras={"group": it["group"], "explode": [e / 1000.0 for e in it["explode"]], "label": it["label"],
                                "slide": [e / 1000.0 for e in it.get("slide", [0, 0, 0])],
                                "pull": [e / 1000.0 for e in it.get("pull", [0, 0, 0])],
                                "bar": it["group"] == "arm" and it["m"] is Mu}))
    write_glb(VIEW / "showcase.glb", glb)
    # camera targets for the viewer (metres, A-frame): clamp centre and display centre
    cc = Mu @ np.array([(A.CL["x0"] + A.CL["x1"]) / 2, 0, 0, 1])
    dc = Mu @ md @ np.array([0, 0, 0, 1])
    dn = Mu[:3, :3] @ md[:3, :3] @ np.array([0, 0, 1.0])
    (VIEW / "showcase_meta.json").write_text(json.dumps({
        "display_variant": variant, "clamp_centre": (cc[:3] / 1000).tolist(), "display_centre": (dc[:3] / 1000).tolist(),
        "display_normal": dn.tolist(), "bar_axis": (Ru @ np.array([1.0, 0, 0])).tolist(), "bar_z": (Ru @ np.array([0, 0, 1.0])).tolist(),
        "head_pivot": ((Mu @ np.array([200.0, 0, 0, 1]))[:3] / 1000).tolist()}, indent=1))
    tri = sum(len(p["t"]) for p in glb)
    print(f"wrote {OUT} and {VIEW / 'showcase.glb'} ({(VIEW / 'showcase.glb').stat().st_size / 1e6:.2f} MB, {tri} triangles)")


if __name__ == "__main__":
    main()
