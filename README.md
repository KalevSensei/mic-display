# Mic-stand audio display

A round display that clips onto a microphone stand and shows the microphone's live state from what the PC can read: a needle dial of the level, clipping, sample rate, device and a no-signal warning. Swipe for other watch faces (frequency bars, loudness, talk time, clock); tap for a settings app (the display's own settings now, the PC's sound settings once the Windows PC app exists).

Uni engineering project (LAB, Engineering Curiosity), Kalev, started 2026-11-14. Built and tested on Kalev's own PC first; mounted on a classmate's custom Yeti stand and installed on his PC last.

## The request, verbatim (2026-11-14)
> "What if I made for him a display that shows like your current microphone like settings? Like it's somehow connected to his computer or his microphone, and then it's like a display that goes on his microphone stand, and it shows like its current, like, I don't know, volume, maybe even like a dial or something. … Maybe it doesn't have to be like touchscreen or control, just like it displays all the info and stuff."

> "Can I design it first to work with my pc and microphone then mounting or whatever attatching and attatchments i ll put to my friends pc later just mount it for him and download software?"

> "I want for now to only have the 2 planned projects in mem, and decide final what parts need to be bought for the audio display. I wanna make the first now"

## How it works
- **Companion page** (`companion/index.html`, runs in Chrome or Edge on Windows or Mac, nothing to install): listens to the microphone, measures level, peak and clipping, reads the sample rate and device name, draws the exact dial the display will show, and streams it to the display over the USB cable (Web Serial). It follows the face the display shows and switches its input when the display asks.
- **Display** (`firmware/mic_display/`): Waveshare ESP32-S3-Touch-AMOLED-1.75, a 1.75" round 466 × 466 AMOLED with the processor on its back, no wiring. Draws the same faces as the page, in the page's typeface, from what the page sends; shows NO SIGNAL after 3 s of silence (the mic's own mute) and "waiting for PC" when nothing arrives. USB powers everything. Touch: swipe between faces, tap for settings (docs/PLAN.md M03b). Build and flash: docs/PLAN.md M03. (The first firmware for the XIAO ESP32C3 + GC9A01 basic build is in git history, commit be7ddd2.)

## Files
- `docs/PLAN.md`: the build steps in order, with status.
- `docs/PROTOCOL.md`: every line the PC and the display send each other.
- `docs/previews/settings/`: pictures of every face and settings screen, drawn by the firmware's own code (`contact_sheet.png` shows them all).
- `docs/OPEN_ITEMS.md`: parked and open items (MD-002: the Windows PC app).
- `docs/PARTS.md`: what to buy (one Electrokit order) and what comes from JHC.
- `docs/WIRING.md`: every wire, pin by pin (basic build; the upgraded board needs none).
