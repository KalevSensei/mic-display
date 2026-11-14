"""Line renders (SVG) of the printed parts and the assembly, for review. Run after md_model.py."""
from pathlib import Path
import cadquery as cq
CAD = Path(__file__).resolve().parents[1]
out = CAD / "renders"; out.mkdir(exist_ok=True)
opt = dict(width=900, height=700, marginLeft=40, marginTop=40, showAxes=False, strokeWidth=0.4, hiddenColor=(190, 190, 190), showHidden=False)
def load(n): return cq.importers.importStep(str(CAD / n))
views = {
  "D01_shell_front": ("print/D01_PETG_display_shell.step", (0.3, -0.5, -1.0)),
  "D01_shell_inside": ("print/D01_PETG_display_shell.step", (0.4, -0.6, 1.0)),
  "D02_back_inside": ("print/D02_PETG_display_back_MI1.step", (0.4, -0.6, 1.0)),
  "D02_back_join": ("print/D02_PETG_display_back_MI1.step", (0.4, -0.9, -0.7)),
  "A00_desk_foot": ("print/A00_PETG_desk_foot_MI1.step", (-0.8, -1.0, -0.5)),
  "assembly_desk": ("assembly/desk_foot_with_display.step", (-0.9, -1.0, -0.45)),
}
for name, (f, d) in views.items():
    w = load(f)
    cq.exporters.export(w, str(out / f"{name}.svg"), opt={**opt, "projectionDir": d})
    print("wrote", name)
