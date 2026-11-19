# What to 3D print

Everything printed for the mic display is in this folder. All parts are **PETG**, no supports, already laid flat in the right orientation. Totals: 5 parts, 54.9 g, 1 h 55 min on one plate.

## Print now (2026-11-19): D03 only
The board came in Waveshare's case with the glass fixed to the case's front ring, so the case stays whole and **D03** replaces D01 + D02 (plan M05, "M05 D03"). The clamp parts A10, A11, A12 already printed are fine (MI-1 never changed).

**`D03_display_back_waveshare_case_MK4S_HF04_PETG.bgcode`**: D03 alone, PETG, **29 min 32 s, 10.69 g** (JHC Prusa MK4S, HF 0.4 nozzle; same profile as below). Any other printer: `D03_PETG_display_back_waveshare_case.stl` or `.3mf`, PETG, 0.20 mm, 2 walls, 15 % infill, no supports, back face (the dovetail side) down as it lies.

After printing: push the Waveshare unit in from the front, back cover first, USB-C at the window and the two buttons in the notches, until the fingers click. Then slide it down onto A12 or A00 until it clicks. No screws needed.

## Fastest: one file, one plate (JHC Prusa MK4S, HF 0.4 nozzle)
The JHC 3D printers (LUT/LAB) are Prusa MK4S with the high-flow 0.4 nozzle, so this file is ready to print there as is:

**`MD_plate_display_and_arm_clamp_MK4S_HF04_PETG.bgcode`**: D01 + D02 + A10 + A11 + A12, PETG, 1 h 54 min 37 s, 54.86 g.

1. Copy the `.bgcode` to a USB stick (download it from GitHub: open the file, then the download button).
2. At the printer: load PETG, choose the file, print. Clean bed, no glue needed for PETG on the textured sheet.
3. When it has cooled: take the parts off and check A10's slots are clean (no strings in the 3.3 mm finger slots or the nut slots).

### Starting the print at JHC, step by step (Eino (agent), 2026-11-18)
1. Before going: the printers need a staff introduction first. Put the `.bgcode` on a USB stick.
2. At the printer: check it is an MK4S with the HF nozzle. If the printer warns that the nozzle or printer does not match the file, do not override it; ask the staff.
3. Sheet: textured sheet = clean it, no glue. Smooth PEI sheet = a thin layer of glue stick first, so the PETG does not bond too hard.
4. Load filament → PETG; at least about 70 g left on the spool.
5. Choose the file, check the preview shows 5 parts, Print (it levels the bed itself).
6. Watch the first layer (about 5 min): all 5 parts flat and stuck. If one lifts: stop, clean, restart.
7. After about 2 h: let it cool, flex the sheet, parts off. Check A10's slots, then slide D02 onto A12 until it clicks.

Slicing something yourself for JHC: pick the printer profile **Original Prusa MK4S HF0.4 nozzle** (or run `md slice`). A PrusaSlicer set up earlier for the standard "Original Prusa MK4S 0.4 nozzle" gives a file the HF printers warn about.

Checked 2026-11-18 (Eino (agent)): the plate file's own metadata says MK4S, nozzle 0.4 high-flow, PETG, 1 h 54 min 37 s, 54.86 g, 5 objects (D01, D02, A10 right, A11, A12), 34.6 mm tall, footprint x 9.8–240.2 / y 33.5–176.4 mm inside the 250 × 210 bed. Its "support_material = 1" comes from the profile's enforcers-only setting (`support_material_auto = 0`); no supports are generated. Fit checks: 31/31 (clamp), 10/10 (display unit).

Already have D01 and D02? Print **`MD_plate_arm_clamp_MK4S_HF04_PETG.bgcode`** instead (A10 + A11 + A12 only, 1 h 29 min, 41.4 g).

## Any other printer
Open **`MD_plate_display_and_arm_clamp.3mf`** (the same plate) in PrusaSlicer, Bambu Studio or OrcaSlicer, pick your printer and a PETG profile, and slice with:
- 0.20 mm layers, 2 perimeters (walls), 15 % infill (grid or gyroid), **no supports**
- PETG, your printer's normal PETG temperatures
- keep the parts as they lie on the plate (that orientation is what was checked)

Or print the parts one by one from their STL files with the same settings:

| Part | File | Qty | PETG | Time (MK4S HF0.4) | What it is |
|---|---|---|---|---|---|
| D01 | `D01_PETG_display_shell.stl` | 1 | 6.2 g | 14 min | front shell around the round screen |
| D02 | `D02_PETG_display_back_MI1.stl` | 1 | 7.3 g | 17 min | back cover with the slide-on dovetail |
| D03 | `D03_PETG_display_back_waveshare_case.stl` | 1 | 10.7 g | 30 min | **replaces D01 + D02 for the board in Waveshare's case**: cup the whole case snaps into, slide-on dovetail on the back |
| A10 | `A10_PETG_arm_clamp_base_display_right.stl` | 1 | 33.1 g | 1 h 10 min | clamp that hangs under the arm's upper bar; display on the user's **right** |
| A11 | `A11_PETG_arm_clamp_pad.stl` | 1 | 3.9 g | 9 min | pressure pad inside the clamp |
| A12 | `A12_PETG_arm_MI1_tilt_block.stl` | 1 | 4.6 g | 26 min | tilt hinge block the display slides onto |
| A00 | `A00_PETG_desk_foot_MI1.stl` | optional | 21.4 g | 1 h 34 min | desk stand instead of the arm (`A00_desk_foot_MK4S_HF04_PETG.bgcode` for JHC) |

Display on the user's **left** instead of the right: print `A10_PETG_arm_clamp_base_display_left.stl` in place of the right one (mirror image, 33.0 g, 1 h 10 min).

`.step` files: the same parts as exact CAD, for opening in SolidWorks or other CAD. `.3mf` per part: the part alone, ready to slice.

## After printing: hardware to put it together
Bought, not printed (details, shops and prices: `docs/PARTS.md`):
- Display: 6 × M2×6 socket-head screws (3 into the board's standoffs, 3 into the shell), 1.5 mm hex key.
- Clamp: 2 × M4×10 set screws + 2 × M4 nuts, 1 × M5×25 socket-head screw + M5 washer + M5 nyloc nut; 2 mm and 4 mm hex keys.
- Assembly and fitting on the arm, step by step: `docs/PLAN.md` M06 "Steps", with drawings in `cad/drawings/A10-A12_arm_adapter_drawings.pdf`.

## Changing a part
Parts come from code: `cad/source/md_model.py` (D01, D02, A00), `cad/source/md_display_b.py` (D03; also writes `W00_waveshare_B_case_envelope.step`, the Waveshare -B case as an envelope built from Waveshare's drawing, not Waveshare's own file) and `cad/source/md_arm_adapter.py` (A10–A12). Change the code, run `md cad` / `md arm` (AGENTS.md > Environment), re-slice with `md slice`, and commit the new files with a LOG line. The mounting interface MI-1 (the dovetail between D02 and A00/A12) never changes once printed.
