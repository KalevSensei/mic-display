# Mic-stand audio display

A round display that clips onto a microphone stand and shows the microphone's live state: a needle dial of the level, clipping, sample rate, device, recording status and the Blue Yeti's mute light. Display only, no controls.

Uni engineering project (LAB, Engineering Curiosity), Kalev, started 2026-11-14. Built and tested on Kalev's own PC first; mounted on a classmate's custom Yeti stand and installed on his PC last.

## The request, verbatim (2026-11-14)
> "What if I made for him a display that shows like your current microphone like settings? Like it's somehow connected to his computer or his microphone, and then it's like a display that goes on his microphone stand, and it shows like its current, like, I don't know, volume, maybe even like a dial or something. … Maybe it doesn't have to be like touchscreen or control, just like it displays all the info and stuff."

> "Can I design it first to work with my pc and microphone then mounting or whatever attatching and attatchments i ll put to my friends pc later just mount it for him and download software?"

> "I want for now to only have the 2 planned projects in mem, and decide final what parts need to be bought for the audio display. I wanna make the first now"

## How it works
- **Companion page** (`companion/index.html`, runs in Chrome or Edge on Windows or Mac, nothing to install): listens to the microphone, measures level, peak and clipping, reads the sample rate and device name, optionally reads OBS recording status, draws the exact dial the display will show, and streams it to the display over the USB cable (Web Serial).
- **Display** (`firmware/mic_display/`): Seeed XIAO ESP32C3 + 1.28" round GC9A01 LCD. Draws the dial from what the page sends and shows "waiting for PC" when nothing arrives. USB powers everything.
- **Mute sensor**: a light sensor (LDR) in a small printed cup over the Yeti's red LED. The Yeti's LED is steady when live and blinks when muted; the board tells the two apart and sends the state back to the page.

## Files
- `docs/PLAN.md`: the build steps in order, with status.
- `docs/PARTS.md`: what to buy (one Electrokit order) and what comes from JHC.
- `docs/WIRING.md`: every wire, pin by pin.
