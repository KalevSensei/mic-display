# Plan

Living plan, updated after every step. Physical steps are ticked only when physically done.

## M01 · Companion page and dial design on Kalev's PC
- status: done 2026-11-14 (digital)
- why: the dial is designed and tested against a real microphone before any part arrives, so the display only has to copy it.
1. Open `companion/index.html` in Chrome or Edge (or run `npx serve companion` and open the localhost address).
2. Click **Start microphone**, allow the mic, talk: the needle follows the level, the ring turns red on clipping.
3. **Demo signal** runs the dial without a mic.

## M02 · Order the parts
- status: next (Kalev)
- why: the board and the round screen are the only things JHC does not have.
1. Pick the basic build (Electrokit, about €27) or the upgraded build (1.75" AMOLED from The Pi Hut, about €42) in `docs/PARTS.md`, and order it.

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
- status: later
- why: the display unit is the same on every stand; only a small, cheap adapter changes per stand (owner, 2026-11-14: "that second part can be interchnaged … if u have 3 diffefent mic stands … the first piece is always the same, has all the stuff in it").
- names: **display unit** (the housing with the screen, the board and the USB port; one design) and **stand adapter** (one per stand model). They join through one fixed **mounting interface**: a quick-release dovetail slide with a snap catch, so an adapter slides on and clicks off without tools.
1. Display unit: front bezel holding the round screen, rear shell holding the XIAO with its USB-C port reachable at the bottom, the female dovetail on the back. 3D-printed in PETG on a JHC Prusa (book as in the monitor-stand plan S07).
2. Interface: the dovetail and snap dimensions are fixed once and written down here, so every future adapter fits every display unit.
3. Stand adapter #1: the male dovetail on one side, a clamp shaped for the classmate's stand on the other, designed after measuring it (tube or arm diameter, where the display should sit).

## M06 · Hand-over to the classmate
- status: later
- why: the build is finished when it works on his PC and his stand.
1. Ask him whether his PC is Windows or Mac.
2. Clip it on, plug in USB, open the companion page in Chrome/Edge and connect once.
3. The companion page gets a hosted address before hand-over, so his PC needs nothing installed: he opens a link.

## Not yet verified
- The firmware has not been compiled or run: no Arduino toolchain on this PC and no parts yet. It is compiled at M03 step 2.
- The companion page was tested with the demo signal; Kalev's own microphone is tested when he opens it (M01 step 2).

## Open questions (owner's to answer)
- Classmate's PC: Windows or Mac.
- Classmate's stand: tube or arm diameter and mounting spot.
