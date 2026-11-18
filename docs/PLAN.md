# Plan

Living plan, updated after every step. Physical steps are ticked only when physically done.

## M01 · Companion page and dial design on Kalev's PC
- status: done 2026-11-14 (digital)
- why: the dial is designed and tested against a real microphone before any part arrives, so the display only has to copy it.
1. Open `companion/index.html` in Chrome or Edge (or run `npx serve companion` and open the localhost address).
2. Click **Start microphone**, allow the mic, talk: the needle follows the level, the ring turns red on clipping.
3. **Demo signal** runs the dial without a mic.

## M02 · Order the parts
- status: **received 2026-11-17** (ordered by Kalev 2026-11-14 from The Pi Hut, ESP32-S3 1.75" AMOLED board "Standard + Case", DHL Express; EUR 5.00 import charge paid 17 Nov; collected 17 Nov). Summary: docs/DELIVERY.md. Next: M03.
- why: the board is the only part JHC does not have.

## M03 · Flash the display and test it on the desk
- status: **flashed 2026-11-18** on Kalev's laptop (COM3, 617,568 bytes written, hash verified). The board answers `C,hello,0.2.0`, `C,face,dial`, `C,peakhold,1` every 5 s and took 297 `S` lines of the laptop's real microphone (−96 to −56 dBFS) over 15 s with no reset (`firmware/tools/feed_mic.py COM3`, headless). Still to check by eye: the dial on the glass follows the voice (step 8), then M03b touch.
- why: proves the display draws the same dial as the page, fed over the USB cable.
- nothing to wire: board and screen are one piece; one USB-C data cable to the PC powers it and carries the data. No cable comes in the box.
- who does it: Kalev plugs the board into his PC; the agent uploads the firmware with `scripts/md.ps1 fw-flash` (Windows) or `scripts/md.sh fw-flash` (macOS), toolchain from the setup script (AGENTS.md > Environment), and opens the companion page (`md companion`). The Arduino IDE steps below are only the fallback and the record for anyone rebuilding it.
- sources: Waveshare wiki https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75 and Waveshare's demo code https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75 (pins from `examples/arduino/libraries/Mylibrary/pin_config.h`, display start-up from `examples/arduino/01_HelloWorld`, touch start-up from `examples/arduino/10_Touch_CST9217` with the 466 × 466 mirrored mapping of `examples/arduino/06_LVGL_Widgets`, core version and flash settings from `docs/getting-started.md`). The wiki still names esp32 core 3.1.0; Waveshare's repository (updated Aug 2026) validates 3.3.10, which is used here.

Versions: Arduino IDE 2, board package **esp32 by Espressif Systems 3.3.10**, library **GFX Library for Arduino 1.6.4** (moononournation) in **Waveshare's copy**. The 1.6.4 from the Arduino Library Manager does not compile on core 3.3.10 (checked 2026-11-15); Waveshare's copy carries the fix. Second library (since M03b, for the touch screen): **SensorLib 0.3.1** (Lewis He), also **Waveshare's copy** from the same folder; it holds the CST9217 touch driver Waveshare's own touch example uses. The power chip and sound are not used.

1. Install **Arduino IDE 2** from https://www.arduino.cc/en/software and open it.
2. Board package: **File → Preferences**, in "Additional boards manager URLs" paste `https://espressif.github.io/arduino-esp32/package_esp32_index.json`, OK. Then **Tools → Board → Boards Manager**, search `esp32`, at "esp32 by Espressif Systems" pick version **3.3.10**, **Install** (a large download, several minutes).
3. Library: download Waveshare's demo code as a ZIP from https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/archive/refs/heads/main.zip and unzip it. Inside, copy the two folders `examples/arduino/libraries/GFX_Library_for_Arduino` and `examples/arduino/libraries/SensorLib` into your Arduino libraries folder (**File → Preferences → Sketchbook location**; the `libraries` folder inside it; create it if missing). If "GFX Library for Arduino" or "SensorLib" was ever installed from the Library Manager, remove it there first, so the IDE uses Waveshare's copies.
4. **File → Open** `firmware/mic_display/mic_display.ino` from this repository (the files `ui.h` and `fonts.h` next to it open as extra tabs; leave them).
5. **Tools** menu, set exactly these and leave the rest as they are:
   - Board: **ESP32S3 Dev Module** (under esp32)
   - USB CDC On Boot: **Enabled** (the page talks to the display over this)
   - Flash Size: **16MB (128Mb)**
   - Partition Scheme: **16M Flash (3MB APP/9.9MB FATFS)**
   - PSRAM: **OPI PSRAM** (the whole picture is drawn in it; without it the screen says "PSRAM is off")
6. Take the board out of its bag (the screen's protective film can stay on for now). Plug it into the PC with a USB-C **data** cable. **Tools → Port**: pick the COM port that appeared when you plugged it in.
7. Click **Upload** (the right-arrow button). It compiles (a few minutes the first time), then writes; done when it says "Hard resetting via RTS pin". The screen shows **waiting for PC**. If it does not change, unplug the cable and plug it back in.
   - If the upload says it cannot connect: unplug the cable, hold the **BOOT** button on the board's side, plug the cable back in, let go of BOOT, then click Upload again. Afterwards unplug and replug once so the new firmware starts.
8. Close the Arduino IDE's Serial Monitor if it is open (only one program can use the port at a time). Open the companion page (`companion/index.html` in Chrome or Edge), click **Start microphone** (or **Demo signal**), then **Connect display** and pick the board's port (it is listed as a USB serial device with the same COM number as in step 6). The display now mirrors the dial: needle, coloured zones, peak dot, red ring on clipping, sample rate, device name, NO SIGNAL after 3 s of silence. Touch (faces and the settings app) is tested in M03b.

Same build from the command line (what is used to verify it): `scripts/md.ps1 fw-build` / `scripts/md.sh fw-build`; upload: `fw-flash [PORT]`. Both call arduino-cli 1.5.1 with FQBN `esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi,CDCOnBoot=cdc` (env/pins.json).

## M03b · Touch: watch faces and a settings app on the display
- status: **firmware compiled with zero errors** (2026-11-15, the command in M03; 617,414 bytes of program storage = 19 % of 3 MB, 26,500 bytes of RAM for globals = 8 %; the picture itself sits in PSRAM). **Not yet run on the board** (board not received). The companion page speaks the new protocol and was checked in the browser with the demo signal. The PC settings stay greyed ("Needs the PC app") until the Windows PC app exists (open item MD-002); that later step is what makes them live, except Input device, which the companion page already answers.
- owner's words, verbatim:
  - 2026-11-15: "So can we control settings with the touch screen?"
  - 2026-11-15: "Like it shows regular settings in a speedometer looking thing, if u tap it opens a settings app we design"
  - 2026-11-15: "And can control output device, input device, volume of ur pc i don't know stuff like that that might be usefull? Maybe if u tap opens all these settings, and if you swipe it switches between watch faces? Is this possible?"
- why: the display stays a glanceable dial, and the few things worth changing mid-recording are one tap away on the stand instead of in Windows menus.
- how it behaves:
  - main screen = five **watch faces**, swipe left or right between them (page dots show for 3 s along the bottom): **needle dial** (the original, default), **frequency bars** (a ring of 32 bars, bass lower left over the top to treble lower right, level in the middle), **loudness** (short-term LUFS big, the session's integrated loudness under it), **talk time** (time the voice was above the silence floor this session, of the session's length), **clock** (time from the PC). The face is saved on the board. The companion page draws whichever face the display shows.
  - a **tap** on any face opens the **settings app**: one setting per screen, swipe left or right between them (page dots along the bottom), change the value with big − / + or ‹ › buttons (88 px drawn, 116 px touch area, about 11 mm on the glass), a big round toggle (148 px drawn), or by dragging around the ring. Back to the face with **Done**, a swipe down, or 10 s without touch.
  - settings, in order: Mic mute [PC], Input device [PC], Input volume [PC], Output device [PC], PC volume [PC], Output mute [PC], Brightness, Screen sleep (never / 5 / 15 / 30 min; wakes on touch or sound), Peak hold (off / 1 s / 3 s), Reset peak & clips, About (firmware version, PC link). Display settings are saved in the board's flash and survive unplugging.
  - protocol (PC ↔ board, backwards compatible, the `S` line unchanged): `docs/PROTOCOL.md`.
- files: `firmware/mic_display/ui.h` (everything drawn and every gesture; plain C++), `firmware/mic_display/mic_display.ino` (screen, touch, USB, flash), `companion/index.html`, `docs/PROTOCOL.md`.
- previews (what the board draws, rendered on the PC from the same `ui.h` by `firmware/tools/previews.py`): `docs/previews/settings/` (one PNG per face and per settings screen, both PC states, and `contact_sheet.png`). Re-render after any change to `ui.h`: `md previews [folder with the IBM Plex TTFs]` (the project Python has Pillow and the Zig C++ compiler, `ziglang` 0.17.1). New font sizes: `firmware/tools/make_fonts.py`, same Python.
1. When the board arrives (after M03 step 8): on the face, swipe left and right through all five faces; unplug and replug, check the last face comes back.
2. Tap a face: the settings app opens on Mic mute. Swipe through all eleven settings; on Brightness drag the ring and tap − +; on Screen sleep pick 5 min, wait, check the screen goes dark and wakes on a touch and on speaking; unplug and replug, check Brightness, Screen sleep and Peak hold kept their values.
3. With the companion page connected: on Input device tap ‹ ›, check the page switches its input; check Mic mute, Input volume and the three output settings show "Needs the PC app".
4. Done, a swipe down and 10 s idle each bring the face back.

## M04 · Mute-light sensor (dropped)
- status: dropped 2026-11-14 (owner: "i think we can skip the light sensor, letys use only data the pc can pick up")
- why: the display shows only what the PC can read. The Yeti's own mute button still shows on the dial: the level falls to silence, and after 3 s the display says NO SIGNAL.

## M05 · Housing: one display unit, interchangeable stand adapters
- status: in progress (digital design); order owner, 2026-11-14: "lets design the display, the join, and the holder first get it fully ready and physical. then we can make the first adapter, proprietary to his microphone arm". The display unit and the mounting interface are finished and printed before anything is measured on his arm; a **desk foot** (adapter #0, generic) carries the male side of the interface so the join is tested and the display stands on Kalev's desk meanwhile.
- designed around the upgraded board (Waveshare ESP32-S3-Touch-AMOLED-1.75; The Pi Hut "Standard + Case" = Waveshare -B, board + case + speaker). The board comes out of Waveshare's case and goes into the printed display unit; the Waveshare case stays spare.
- why: the display unit is the same on every stand; only a small, cheap adapter changes per stand (owner, 2026-11-14: "that second part can be interchnaged … if u have 3 diffefent mic stands … the first piece is always the same, has all the stuff in it").
- names: **display unit** (the housing with the screen, the board and the USB port; one design) and **stand adapter** (one per stand model). They join through one fixed **mounting interface**: a quick-release dovetail slide with a snap catch, so an adapter slides on and clicks off without tools.
1. Display unit: front bezel holding the round screen, rear shell holding the board with its USB-C port reachable at the bottom, the female dovetail on the back. 3D-printed in PETG on a JHC Prusa (JHC is open Mon–Fri 8:30–18:00; the printers need a staff introduction first).
2. Interface: the dovetail and snap dimensions are fixed once and written down here, so every future adapter fits every display unit.
3. Stand adapter #1: the male dovetail on one side, a clamp shaped for the classmate's stand on the other, designed after measuring it (tube or arm diameter, where the display should sit).

### M05 design state (2026-11-14, digital)
- Parts: **D01 display shell** (front lip over the glass edge, USB-C opening at the bottom, two pin holes for PWR/BOOT, 3 screw bosses), **D02 display back** with the female side of the mounting interface **MI-1**, **A00 desk foot** (male MI-1 rail, stands the display on Kalev's desk, 15° back). All PETG. Sizes: Ø53.4 × 20.0 deep; 6.3 g + 12.0 g + 43.2 g.
- MI-1 (fixed for every adapter): dovetail channel 20.00 wide at its floor, 16.54 at the face, 3.00 deep, flanks 60°, open at the bottom, stop at the top; rail 0.20 off the flanks; a flexible tongue with a 1.2 mm bump clicks into a 0.4 mm groove across the channel floor (0.15 mm preload when home, so it does not wobble). Slide the display down onto a rail, pull up to take it off.
- Assembly: board face-down into D01, D02 on the back, 3 × M2×6 into the board's standoffs (2.9 mm thread engagement, tip 0.6 mm short of the PCB) and 3 × M2×6 into the shell bosses.
- Files: `cad/source/md_model.py` (CadQuery; run with `md cad`), print files in `cad/print/` (STEP, STL, 3MF), checks in `cad/checks/fit_check.json` (all pass: zero overlap with Waveshare's board model). Board model: `cad/reference/` (download link in its README).
- Printing (decided 2026-11-17): no separate fit coupon. The real D01 and D02 print on the 19 Nov plate with the clamp (the whole plate is under 2 h, so a coupon saves nothing); MI-1 is tested on the real parts. Renders are done (`cad/renders/`); a dimensioned drawing PDF of D01/D02/A00 is still to do (for the project file, not needed to print). Fit the board when it arrives.

### M05 print booking (booked 2026-11-17)
- status: booked, not printed. Physical print: not done.
- **JHC 3D printer 2** (Prusa MK4S, HF 0.4 nozzle), **Thu 19 Nov 10:00–14:00**, booked by Kalev in LUT Outlook (printer as attendee, event title = Kalev's uni email only). JHC is open Mon–Fri 8:30–18:00; the printers need a staff introduction first.
- File: `cad/print/MD_plate_display_and_arm_clamp_MK4S_HF04_PETG.bgcode`: D01 + D02 + A10 (right-hand) + A11 + A12 on one plate, PETG, **1 h 54 min 37 s, 54.86 g** (read from the file's own metadata: MK4S, nozzle 0.4 high-flow, PETG). Sliced with PrusaSlicer 2.9.7 and the profile `cad/slicing/mk4s_hf04_petg_SPEED.ini` (`md slice`) (0.20 mm SPEED @MK4S HF0.4, Prusament PETG @HF0.4, 2 perimeters, 15 % infill); no supports generated. The editable plate is `cad/print/MD_plate_display_and_arm_clamp.3mf`.
- If D01/D02 are printed separately: `cad/print/MD_plate_arm_clamp_MK4S_HF04_PETG.bgcode` prints only A10 + A11 + A12 (1 h 29 min 11 s, 41.43 g).
- Optional second file, only if the plate is off the bed by 12:20: `cad/print/A00_desk_foot_MK4S_HF04_PETG.bgcode`, the desk foot alone (1 h 34 min 03 s, 21.42 g PETG, same profile, no supports), so the display can stand on Kalev's desk while the firmware is tested. Otherwise it prints on a later booking.
- Per part (separate prints): D01 6.18 g 13 min 35 s; D02 7.30 g 17 min 07 s; A10 33.05 g 1 h 10 min 00 s; A11 3.89 g 8 min 30 s; A12 4.61 g 26 min 26 s (`cad/print/slice_summary_arm_adapter.json`). The slot leaves room to reprint any one part.
1. Copy the .bgcode to a USB stick; at JHC load PETG, start the file on printer 2.
2. When cool: take the parts off, check A10's U and slots are clean (no strings in the 3.3 mm finger slots or the nut slots).

## M06 · Stand adapter #1 for the classmate's microphone arm
- status: designed in CAD 2026-11-17 (digital), all CAD checks pass; printed: no; fitted on Eino's arm: no.
- input: Eino's SolidWorks 2026 Pack and Go of the arm (A00_Mikrofonivarsi_Yeti_2palkki_v2), read as STEP copies in `cad/reference/arm_eino_step/` (git-ignored; his geometry stays out of git). The adapter sits on the upper arm bar P03_Varsiputki_2palkki_v2, a 30 × 15 × 1.5 rectangular tube.

### Where it sits and why (traced in CAD through the arm's whole range)
- Spot: on the upper bar next to the head; the clamp's head-side face is **72 mm from the head pivot bolt centre**. It covers no hole of the bar (14.9 mm clear of the nearest spring hole behind it, 28.8 mm of the next hole toward the head) and stays 9 mm clear of the spring plug P11 even on its furthest hole pair. Further back the spring plugs are in the way; further forward the head fork P05.
- The display sits **110 mm out from the bar centreline on the user's right, beside the Yeti head, glass towards the user**, on a tilt hinge 22 mm back from the head pivot along the bar and 12.5 mm below the bar centre. It tilts −3…103° and holds any angle.
- Nothing rises above the bar's top face: in the head joint's end pose (bar 28.5° down towards the head) with the Yeti tipped back 55–62°, the Yeti lies 1.3–4 mm above the bar. So the clamp hangs under the bar and its walls end 0.5 mm below the top face.
- Seeing (eye position assumed as in docs/USE_SETUP.md): reading distance 389–401 mm, 16° off the glass axis. From the nominal eye, the whole glass is visible at bar angles −28.5°, −20°, 0° and +20° with the Yeti tilted up to ±10°; at ±20° tilt it is at least 98.4 % (worst: bar −28.5°). Over 27 eye positions (±40 mm sideways, 110–210 mm along, 330–380 mm up) the worst is 100 %. Rays traced through the head, Yeti, cradle, bar, clamp, bolts and the display's own lip.
- Mic and monitor: the display top stays at most 41 mm above the head pivot, the Yeti body starts 144 mm above it, so the display stays out of the mouth-to-capsule path. The user sees the display at least 54° below horizontal; the monitor's lower edge is 28° below, so it never covers the monitor.
- Motion: no contact with the head, tilt piece, Yeti cradle or Yeti over 117 head poses (bar −28.5…180° × Yeti tilt to its own limits); no contact with the lower bar, elbow, springs, spring plugs, swivel or desk clamp over 137 arm poses (shoulder −20…110°, elbow full circle, both display sides, 3 display tilts); closest at the head joint's stop 20.0 mm. The adapter never reaches the desk before Eino's own parts do.
- Webcam: it sees D02's back and the cable, as on the desk foot (USE_SETUP check 1).

### How it holds (no drilling, no crushing)
- **A10 clamp saddle**: a U that hangs under the bar, plus the outrigger arm and a 3-finger tilt knuckle. **A11 pressure pad** sits between the bar and the U's far wall; **2 × M4×10 set screws** run in captive M4 nuts in that wall and push the pad. The bar is squeezed across its two 30 mm faces, only on 2.5 mm strips next to the tube's top and bottom walls (180 mm² per side), so the faces do not bend in the middle.
- Snug (short arm of the 2 mm key, about 0.1 N·m per screw) = 250 N squeeze: 6.2 × the grip needed for a 20 N push along the bar; tube wall 2.3 MPa, face bending 11.6 MPa (34.7 MPa if over-tightened to 0.3 N·m; aluminium 6060-T5 yields at about 120). PETG: U wall 6.3 MPa, pad 7.1 MPa snug. Rotation round the bar is blocked by the U's shape; with only 10 % of the squeeze left it still carries itself, the display and a 5 N press (12.5 N of friction).
- **A12 tilt block**: the male MI-1 rail (identical to the desk foot's, never changed) on one face, 2 fingers on the other. **M5×25 + washer + M5 nyloc** through the knuckle is a friction hinge: 1.31 N·m holding against 0.27 N·m from a 5 N press on the glass edge. The display slides down onto A12's rail and clicks, as on the desk foot; its weight keeps it on the rail stop in every reading pose.
- Hardware and where to buy it: docs/PARTS.md.

### Files
- Model and checks: `cad/source/md_arm_adapter.py` (run with `md arm`; about 1.5 min; needs Eino's STEP export, AGENTS.md). Results: `cad/checks/arm_adapter_fit_check.json` (all pass).
- Print files: `cad/print/A10_PETG_arm_clamp_base_display_right.*` (display on the user's right; `_left` is the mirror image), `A11_PETG_arm_clamp_pad.*`, `A12_PETG_arm_MI1_tilt_block.*` (STEP, STL, 3MF each), plates and slices as in M05 above, masses in `cad/print/manifest_arm_adapter.json`.
- Drawings (4 × A3: assembly with parts list and steps, A10, A11 + A12, check list): `cad/drawings/A10-A12_arm_adapter_drawings.pdf` (made by `cad/source/md_arm_drawing.py`). Render: `cad/renders/A10_arm_adapter_on_arm.png`.

### Steps
1. Design the adapter from his arm's CAD: done 2026-11-17 (digital).
2. Print A10, A11, A12 (M05 booking, Thu 19 Nov). Not done.
3. Buy the hardware (PARTS.md). Not done.
4. On the bench: push the 2 M4 nuts down into A10's slots and thread the set screws in from outside until they just show inside; put A12's 2 fingers into A10's slots, M5×25 + washer from the outer finger, nyloc into its hex pocket, tighten until the display holds any angle against a firm tap (about 1 N·m). Slide the display onto A12 until it clicks. Not done.
5. On Eino's arm: measure the bar with calipers (30.0 × 15.0 expected) and look at its outer corner radius (the strips assume 1.5 or less). Saddle up under the bar, display arm on the user's right, head-side face 72 mm from the head pivot bolt centre; drop A11 in between the bar and the far wall, dimples towards the screws; set screws finger-tight on the short arm of the 2 mm key. Not done.
6. Check on the arm: a firm push along the bar does not slide it; swing the arm through its whole range and fold the Yeti down onto the bar; sit in his seat and read the display; route the USB-C cable along the arm. Not done.
7. One week later: re-snug the set screws once (PETG settles). Not done.

### Settled only on the real arm or by Eino
- The bar's real outside size, corner radius and material (aluminium assumed), and so the set-screw torque that holds without marking it.
- His seat, eye height and distance (the CAD trace assumes the eye position in USE_SETUP).
- The Yeti's side knobs (not in his CAD) and the real cable route.
- Eino's OK for the spot and for a clamp on his bar.

## M07 · Hand-over to the classmate
- status: later
- why: the build is finished when it works on his PC and his stand.
1. His PC is a Windows PC (owner, 2026-11-14: "he has pc"): the companion page runs in Chrome or Edge there.
2. Clip it on, plug in USB, open the companion page in Chrome/Edge and connect once.
3. The companion page gets a hosted address before hand-over, so his PC needs nothing installed: he opens a link.

## Not yet verified
- Touch (M03b), only checkable on the real board: that the touch points land where the finger is (Waveshare's X and Y mirroring is used as in their LVGL demo); that a finger held still keeps reporting (the firmware treats 120 ms without a report as "finger lifted"; a controller that stops reporting a still finger would end a ring drag early); that taps on the mic arm stay few and quiet enough; that the swipe distances (70 px sideways, 90 px down) and the 30 px tap limit feel right; that brightness 10 % is still readable; screen sleep and wake.
- The clip ring now sits at radius 207–212 px (page r 107.75), inside the shell's 424 px window; before M03b it was at 219–231 px, under the shell lip and invisible once mounted. The device name under the dial is cut with "..." at 190 px so it stays clear of the clip ring.
- Loudness (LUFS) on the page is measured from the K-weighted signal sampled once per animation frame, so it is close to a meter's reading but not certified; the Windows PC app (MD-002) can measure it sample-exact.
- The firmware compiles for the bought board (2026-11-15, zero errors) but has not run on it: the board has not arrived. Checked only on the real board (M03 steps 7–8): the screen starts and the picture sits centred in the round glass (Waveshare's column offset of 6 is used as in their demo); the dial looks like the page's; the frame rate (a full picture takes about 25–35 ms to send to the screen, estimated, not measured); the port name Chrome shows; that the default brightness (80 %, 204 of 255; changeable on the display under Brightness) is comfortable.
- AMOLED screens can keep a faint ghost of a picture that stays still for many hours. The dial's scale is static; Screen sleep (default 15 min without touch or sound, set on the display) turns it dark when nobody records; if a ghost still shows, lower Brightness on the display.
- The companion page was tested with the demo signal; Kalev's own microphone is tested when he opens it (M01 step 2).

## Open questions
- None for now. The arm adapter (M06) is designed from his CAD; the facts only the real arm or Eino can settle are listed under M06.
