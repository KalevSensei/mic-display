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
- why: the board, the round display and the light sensor are the only things JHC does not have.
1. One Electrokit order, the three items in `docs/PARTS.md`.

## M03 · Flash the display and wire it on the desk
- status: waiting for parts
- why: proves the display draws the same dial as the page, fed over the USB cable.
1. Arduino IDE: install the ESP32 boards package (Espressif) and the library "GFX Library for Arduino" (moononournation).
2. Open `firmware/mic_display/mic_display.ino`, board "XIAO_ESP32C3", USB CDC On Boot: Enabled, upload.
3. Solder the display wires from `docs/WIRING.md`; the screen shows "waiting for PC".
4. In the companion page click **Connect display**, pick the XIAO's port: the display now mirrors the dial.

## M04 · Mute-light sensor
- status: waiting for parts
- why: the Yeti does not tell the PC when its own mute button is pressed; its red LED does (steady = live, blinking = muted).
1. Solder the LDR divider (`docs/WIRING.md`). Test against any red LED: steady light reads "live", blinking reads "muted".
2. Print the sensor cup, fit it over the Yeti's LED (one 5-minute check on the classmate's mic).

## M05 · Housing
- status: later
- why: the display body is usable on its own; the stand clip waits for the stand's measurements.
1. Display body: 3D-printed in PETG on a JHC Prusa (book as in the monitor-stand plan S07).
2. Stand clip: designed after measuring the classmate's stand (tube or arm diameter, where the display should sit).

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
