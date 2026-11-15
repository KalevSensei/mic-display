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

## M03 · Flash the display and test it on the desk
- status: firmware ported to the bought board (Waveshare ESP32-S3-Touch-AMOLED-1.75) and **compiles with zero errors** (verified 2026-11-15 with arduino-cli, command below). **Not yet run on the board** (board not received).
- why: proves the display draws the same dial as the page, fed over the USB cable.
- nothing to wire: board and screen are one piece; one USB-C data cable to the PC powers it and carries the data.
- sources: Waveshare wiki https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-1.75 and Waveshare's demo code https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75 (pins from `examples/arduino/libraries/Mylibrary/pin_config.h`, display start-up from `examples/arduino/01_HelloWorld`, core version and flash settings from `docs/getting-started.md`). The wiki still names esp32 core 3.1.0; Waveshare's repository (updated Aug 2026) validates 3.3.10, which is used here.

Versions: Arduino IDE 2, board package **esp32 by Espressif Systems 3.3.10**, library **GFX Library for Arduino 1.6.4** (moononournation) in **Waveshare's copy**. The 1.6.4 from the Arduino Library Manager does not compile on core 3.3.10 (checked 2026-11-15); Waveshare's copy carries the fix. No other library is needed (touch, power chip and sound are not used).

1. Install **Arduino IDE 2** from https://www.arduino.cc/en/software and open it.
2. Board package: **File → Preferences**, in "Additional boards manager URLs" paste `https://espressif.github.io/arduino-esp32/package_esp32_index.json`, OK. Then **Tools → Board → Boards Manager**, search `esp32`, at "esp32 by Espressif Systems" pick version **3.3.10**, **Install** (a large download, several minutes).
3. Library: download Waveshare's demo code as a ZIP from https://github.com/waveshareteam/ESP32-S3-Touch-AMOLED-1.75/archive/refs/heads/main.zip and unzip it. Inside, copy the folder `examples/arduino/libraries/GFX_Library_for_Arduino` into your Arduino libraries folder (**File → Preferences → Sketchbook location**; the `libraries` folder inside it; create it if missing). If "GFX Library for Arduino" was ever installed from the Library Manager, remove it there first, so the IDE uses Waveshare's copy.
4. **File → Open** `firmware/mic_display/mic_display.ino` from this repository (the file `fonts.h` next to it opens as a second tab; leave it).
5. **Tools** menu, set exactly these and leave the rest as they are:
   - Board: **ESP32S3 Dev Module** (under esp32)
   - USB CDC On Boot: **Enabled** (the page talks to the display over this)
   - Flash Size: **16MB (128Mb)**
   - Partition Scheme: **16M Flash (3MB APP/9.9MB FATFS)**
   - PSRAM: **OPI PSRAM** (the whole picture is drawn in it; without it the screen says "PSRAM is off")
6. Take the board out of its bag (the screen's protective film can stay on for now). Plug it into the PC with a USB-C **data** cable. **Tools → Port**: pick the COM port that appeared when you plugged it in.
7. Click **Upload** (the right-arrow button). It compiles (a few minutes the first time), then writes; done when it says "Hard resetting via RTS pin". The screen shows **waiting for PC**. If it does not change, unplug the cable and plug it back in.
   - If the upload says it cannot connect: unplug the cable, hold the **BOOT** button on the board's side, plug the cable back in, let go of BOOT, then click Upload again. Afterwards unplug and replug once so the new firmware starts.
8. Close the Arduino IDE's Serial Monitor if it is open (only one program can use the port at a time). Open the companion page (`companion/index.html` in Chrome or Edge), click **Start microphone** (or **Demo signal**), then **Connect display** and pick the board's port (it is listed as a USB serial device with the same COM number as in step 6). The display now mirrors the dial: needle, coloured zones, peak dot, red ring on clipping, sample rate, device name, REC/LIVE on top, NO SIGNAL after 3 s of silence.

Same build from the command line, run in the repository folder (what was used to verify it; arduino-cli 1.5.1 in `C:\Users\kalev\tools\arduino-cli`, with Waveshare's GFX copy in its `user\libraries` folder):
```
arduino-cli --config-file C:/Users/kalev/tools/arduino-cli/arduino-cli.yaml compile --fqbn "esp32:esp32:esp32s3:FlashSize=16M,PartitionScheme=app3M_fat9M_16MB,PSRAM=opi,CDCOnBoot=cdc" firmware/mic_display
```
Upload from the command line: the same with `upload -p COMx` in place of `compile`.

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
- The firmware compiles for the bought board (2026-11-15, zero errors) but has not run on it: the board has not arrived. Checked only on the real board (M03 steps 7–8): the screen starts and the picture sits centred in the round glass (Waveshare's column offset of 6 is used as in their demo); the dial looks like the page's; the frame rate (a full picture takes about 25–35 ms to send to the screen, estimated, not measured); the port name Chrome shows; that brightness 200 of 255 is comfortable.
- AMOLED screens can keep a faint ghost of a picture that stays still for many hours. The dial's scale is static; if a ghost shows, lower the brightness in the sketch (`BRIGHTNESS`) or unplug the display when not recording.
- The companion page was tested with the demo signal; Kalev's own microphone is tested when he opens it (M01 step 2).

## Open questions
- None for now. His microphone arm is measured at M06, after the display unit is printed.
