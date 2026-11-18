# Mic-stand audio display

A round display that clips onto a microphone stand and shows the microphone's live state from what the PC can read: a needle dial of the level, clipping, sample rate, device and a no-signal warning. Swipe for other watch faces (frequency bars, loudness, talk time, clock); tap for a settings app (the display's own settings now, the PC's sound settings once the Windows PC app exists).

Uni engineering project (LAB, Engineering Curiosity) by Kalev Soininen with Eino Laakso, started 2026-11-14. Built and tested on Kalev's own PC first; mounted on Eino's custom Yeti mic arm and installed on his PC last.

**Everything about the project (rules, plan, environment, current state) is in [AGENTS.md](AGENTS.md).**

**To 3D print it: [cad/print/README.md](cad/print/README.md)** (one ready plate for the JHC Prusa MK4S, plus STL/3MF files and settings for any printer).

## Start here with an agent
Give your agent (Claude Code, Codex or similar) this prompt, unchanged:

> Handoff: mic-display, the shared project of Kalev Soininen and Eino Laakso (LAB engineering). Clone https://github.com/KalevSensei/mic-display (private; accept the GitHub invite first) and run `git pull --rebase` before anything. Read AGENTS.md: it is the project's whole memory (what it is, who decides what, the plan, open items, how to set up and run everything) and it names the setup script for your OS. Work only from the repo. Every decision, measured fact, instruction or test result goes into the repo docs in the same commit as the change, with a dated line in docs/LOG.md saying who. Then push; never force-push, and rebase if the other one pushed first. State on 18 Nov 2026: the display unit and the clamp for Eino's Yeti arm are designed and checked in CAD (31 fit checks pass), the print is booked at JHC on Thu 19 Nov 10:00 (printer 2), and the display board has arrived and is being flashed next.

Set up by hand instead: Windows `powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1`, macOS `sh scripts/setup-macos.sh`.

## The request, verbatim (2026-11-14)
> "What if I made for him a display that shows like your current microphone like settings? Like it's somehow connected to his computer or his microphone, and then it's like a display that goes on his microphone stand, and it shows like its current, like, I don't know, volume, maybe even like a dial or something. … Maybe it doesn't have to be like touchscreen or control, just like it displays all the info and stuff."

> "Can I design it first to work with my pc and microphone then mounting or whatever attatching and attatchments i ll put to my friends pc later just mount it for him and download software?"

> "I want for now to only have the 2 planned projects in mem, and decide final what parts need to be bought for the audio display. I wanna make the first now"

## How it works
- **Companion page** (`companion/index.html`, runs in Chrome or Edge on Windows or Mac, nothing to install): listens to the microphone, measures level, peak and clipping, reads the sample rate and device name, draws the exact dial the display will show, and streams it to the display over the USB cable (Web Serial). It follows the face the display shows and switches its input when the display asks.
- **Display** (`firmware/mic_display/`): Waveshare ESP32-S3-Touch-AMOLED-1.75, a 1.75" round 466 × 466 AMOLED with the processor on its back, no wiring. Draws the same faces as the page, in the page's typeface, from what the page sends; shows NO SIGNAL after 3 s of silence (the mic's own mute) and "waiting for PC" when nothing arrives. USB powers everything. Touch: swipe between faces, tap for settings (docs/PLAN.md M03b). Build and flash: docs/PLAN.md M03. (The first firmware for the XIAO ESP32C3 + GC9A01 basic build is in git history, commit be7ddd2.)

## Files
- `AGENTS.md`: the project's memory and entry point (who is who, rules, environment, current state).
- `docs/LOG.md`: one dated line per change, saying who.
- `docs/PLAN.md`: the build steps in order, with status.
- `env/`, `scripts/`: pinned environment, setup scripts and the `md` command.
- `docs/PROTOCOL.md`: every line the PC and the display send each other.
- `docs/previews/settings/`: pictures of every face and settings screen, drawn by the firmware's own code (`contact_sheet.png` shows them all).
- `docs/OPEN_ITEMS.md`: parked and open items (MD-002: the Windows PC app).
- `docs/PARTS.md`: what to buy (one Electrokit order) and what comes from JHC.
- `docs/WIRING.md`: every wire, pin by pin (basic build; the upgraded board needs none).
