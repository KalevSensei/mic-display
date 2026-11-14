# Plan

Living plan, updated after every step. Physical steps are ticked only when physically done.

## M01 · Companion page and dial design on Kalev's PC
- status: done 2026-11-14 (digital)
- why: the dial is designed and tested against a real microphone before any part arrives, so the display only has to copy it.
1. Open `companion/index.html` in Chrome or Edge (or run `npx serve companion` and open the localhost address).
2. Click **Start microphone**, allow the mic, talk: the needle follows the level, the ring turns red on clipping.
3. **Demo signal** runs the dial without a mic.

## M02 · Order the parts
- status: done 2026-11-14 (ordered by Kalev): The Pi Hut order #[order no. removed], ESP32-S3 1.75" AMOLED board "Standard + Case", DHL Express (2–3 working days). Dispatch expected Mon 16 Nov, arrival Tue 17 to Wed 18 Nov, Thu 19 Nov at the latest. Not yet received. Watched twice a day by the scheduled task mic-board-delivery-watch, which emails Kalev if dispatch, transit or delivery slips, if DHL asks for duty, or once it arrives; timeline, checkpoints and messages in docs/DELIVERY.md.
- why: the board is the only part JHC does not have.

## M03 · Flash the display and wire it on the desk
- status: waiting for parts
- why: proves the display draws the same dial as the page, fed over the USB cable.
1. Arduino IDE: install the ESP32 boards package (Espressif) and the library "GFX Library for Arduino" (moononournation).
2. Open `firmware/mic_display/mic_display.ino`, board "XIAO_ESP32C3", USB CDC On Boot: Enabled, upload.
3. Basic build: solder the display wires from `docs/WIRING.md`. Upgraded build: nothing to wire (the firmware is ported to the AMOLED board first). The screen shows "waiting for PC".
4. In the companion page click **Connect display**, pick the XIAO's port: the display now mirrors the dial.

## M04 · Mute-light sensor (dropped)
- status: dropped 2026-11-14 (owner: "i think we can skip the light sensor, letys use only data the pc can pick up")
- why: the display shows only what the PC can read. The Yeti's own mute button still shows on the dial: the level falls to silence, and after 3 s the display says NO SIGNAL.

## M05 · Housing: one display unit, interchangeable stand adapters
- status: in progress (digital design); order owner, 2026-11-14: "lets design the display, the join, and the holder first get it fully ready and physical. then we can make the first adapter, proprietary to his microphone arm". The display unit and the mounting interface are finished and printed before anything is measured on his arm; a **desk foot** (adapter #0, generic) carries the male side of the interface so the join is tested and the display stands on Kalev's desk meanwhile.
- designed around the upgraded board (Waveshare ESP32-S3-Touch-AMOLED-1.75; The Pi Hut "Standard + Case" = Waveshare -B, board + case + speaker). The board comes out of Waveshare's case and goes into the printed display unit; the Waveshare case stays spare.
- why: the display unit is the same on every stand; only a small, cheap adapter changes per stand (owner, 2026-11-14: "that second part can be interchnaged … if u have 3 diffefent mic stands … the first piece is always the same, has all the stuff in it").
- names: **display unit** (the housing with the screen, the board and the USB port; one design) and **stand adapter** (one per stand model). They join through one fixed **mounting interface**: a quick-release dovetail slide with a snap catch, so an adapter slides on and clicks off without tools.
1. Display unit: front bezel holding the round screen, rear shell holding the XIAO with its USB-C port reachable at the bottom, the female dovetail on the back. 3D-printed in PETG on a JHC Prusa (book as in the monitor-stand plan S07).
2. Interface: the dovetail and snap dimensions are fixed once and written down here, so every future adapter fits every display unit.
3. Stand adapter #1: the male dovetail on one side, a clamp shaped for the classmate's stand on the other, designed after measuring it (tube or arm diameter, where the display should sit).

### M05 design state (2026-11-14, digital)
- Parts: **D01 display shell** (front lip over the glass edge, USB-C opening at the bottom, two pin holes for PWR/BOOT, 3 screw bosses), **D02 display back** with the female side of the mounting interface **MI-1**, **A00 desk foot** (male MI-1 rail, stands the display on Kalev's desk, 15° back). All PETG. Sizes: Ø53.4 × 20.0 deep; 6.3 g + 12.0 g + 43.2 g.
- MI-1 (fixed for every adapter): dovetail channel 20.00 wide at its floor, 16.54 at the face, 3.00 deep, flanks 60°, open at the bottom, stop at the top; rail 0.20 off the flanks; a flexible tongue with a 1.2 mm bump clicks into a 0.4 mm groove across the channel floor (0.15 mm preload when home, so it does not wobble). Slide the display down onto a rail, pull up to take it off.
- Assembly: board face-down into D01, D02 on the back, 3 × M2×6 into the board's standoffs (2.9 mm thread engagement, tip 0.6 mm short of the PCB) and 3 × M2×6 into the shell bosses.
- Files: `cad/source/md_model.py` (CadQuery; run with `C:/Users/kalev/tools/cadenv/Scripts/python.exe -I cad/source/md_model.py`), print files in `cad/print/` (STEP, STL, 3MF), checks in `cad/checks/fit_check.json` (all pass: zero overlap with Waveshare's board model). Board model: `cad/reference/` (download link in its README).
- Still to do before printing: dimensioned drawings (PDF), shaded renders, then print a fit coupon of MI-1 and the display unit at JHC; fit the board when it arrives.

## M06 · Stand adapter #1 for the classmate's microphone arm
- status: after M05 is printed and works
1. Measure his microphone arm where the display should sit (tube or arm section, width, the spot), then design the adapter: male side of the mounting interface on one face, a clamp for his arm on the other.

## M07 · Hand-over to the classmate
- status: later
- why: the build is finished when it works on his PC and his stand.
1. His PC is a Windows PC (owner, 2026-11-14: "he has pc"): the companion page runs in Chrome or Edge there.
2. Clip it on, plug in USB, open the companion page in Chrome/Edge and connect once.
3. The companion page gets a hosted address before hand-over, so his PC needs nothing installed: he opens a link.

## Not yet verified
- The firmware has not been compiled or run: no Arduino toolchain on this PC and no parts yet. It is compiled at M03 step 2.
- The companion page was tested with the demo signal; Kalev's own microphone is tested when he opens it (M01 step 2).

## Open questions
- None for now. His microphone arm is measured at M06, after the display unit is printed.
