# mic-display: the project's memory (read this first)

A round 1.75" touch display that clips onto a microphone arm and shows the microphone's live state, read from the PC: a needle dial of the level, clipping, sample rate, device, plus swipeable faces and a settings app. Uni engineering project at LAB (Engineering Curiosity), started 2026-11-14.

This file is the single entry point for people and agents (Codex reads `AGENTS.md`; Claude Code reads `CLAUDE.md`, which only imports this file). No handoff is needed: everything known about the project is in this repo. If it is not in the repo, it is not known.

## Common asks: where the answer is
- **"3D print it" / "find the print file and settings"**: `cad/print/README.md`. At JHC (Prusa MK4S, HF 0.4 nozzle) print `cad/print/MD_plate_display_and_arm_clamp_MK4S_HF04_PETG.bgcode` as is (all 5 parts, PETG, 1 h 55 min, 54.9 g). Any other printer: `cad/print/MD_plate_display_and_arm_clamp.3mf` with PETG, 0.20 mm layers, 2 walls, 15 % infill, no supports. Hardware to buy afterwards: `docs/PARTS.md`.
- **"Flash the display"**: plan M03 in `docs/PLAN.md`; `md fw-flash`.
- **"Run the companion page"**: `md companion`, then Chrome or Edge.
- **"Fit the clamp on Eino's arm"**: plan M06 "Steps" in `docs/PLAN.md`, drawings in `cad/drawings/`.

## Who is who
| Person | GitHub | Role | Decides |
|---|---|---|---|
| Kalev Soininen | `KalevSensei` | owner, builds the display | scope, the display unit, firmware, companion page, budget, what gets bought and printed |
| Eino Laakso | `laaksoneino` | collaborator; designed the Yeti mic arm the first clamp fits; first end user | everything about his arm: where the clamp sits, whether anything mounts on his bar, his seat, his PC; his arm CAD stays his |

When the two disagree on something on Eino's arm, Eino's call stands. Agents act for whichever of them is running them and name that person in `docs/LOG.md`.

## Reading order
1. This file (rules, environment, current state).
2. `docs/LOG.md`, the last 20 lines: what happened most recently and who did it.
3. `docs/PLAN.md`: build steps M01 to M07 with status, the full design facts and what is not yet verified.
4. `docs/OPEN_ITEMS.md`: open and parked items (codes MD-nnn).
5. As needed: `docs/USE_SETUP.md` (who and what is where in real use), `docs/PARTS.md` (what to buy and where), `docs/PROTOCOL.md` (PC ↔ display serial lines), `docs/WIRING.md`, `docs/DELIVERY.md`, `README.md`.

## Current state (keep this section current in the same commit as any change to it)
- 2026-11-18: repo live on GitHub (private, KalevSensei/mic-display); Eino invited with write access and sent the handoff prompt (README > Start here with an agent).
- Display unit D01/D02, mounting interface MI-1 and desk foot A00: designed, fit-checked against Waveshare's board model (`cad/checks/fit_check.json`).
- Clamp A10–A12 for Eino's arm: designed and checked in CAD, 31 fit checks pass (`cad/checks/arm_adapter_fit_check.json`, plan M06). Not printed, not fitted.
- Print: booked at JHC, **Thu 19 Nov 2026 10:00–17:00, 3D printer 2** (extended from 14:00 on 19 Nov) (Prusa MK4S, HF 0.4 nozzle), file `cad/print/MD_plate_display_and_arm_clamp_MK4S_HF04_PETG.bgcode` (1 h 55 min, 54.9 g PETG).
- Board (Waveshare ESP32-S3-Touch-AMOLED-1.75): arrived 17 Nov 2026; flashed 18 Nov with firmware 0.2.0; the needle dial follows the live mic on the glass (Kalev: "the metre was already working quite well"). Touch (M03b) and the companion page in Chrome are tested next.
- Printing: everything to print and how is in `cad/print/README.md` (Kalev, 2026-11-18: so Eino can print it too).
- Hardware (`docs/PARTS.md` > Shopping list: 6 × M2×6 for the display, M4 set screws/nuts and the M5 hinge set for the clamp): not bought yet. Eino, 2026-11-18: buy it as designed, no redesign for other screws. Display on the right of Eino's arm (Eino, 2026-11-19: "on the right side"; MD-004 resolved), so the JHC plate file is the right one.
- Next: flash and test on the desk (M03/M03b), print (M05), buy hardware and fit on Eino's arm (M06), Windows PC app (MD-002), hand-over (M07).

## Environment (Windows and macOS, always current)
Everything is pinned in `env/`; one setup script per OS builds it all outside the repo (in `%LOCALAPPDATA%\mic-display` or `~/.mic-display`; set `MD_HOME` to move it), so a repo inside OneDrive or iCloud never syncs gigabytes of tools.

| Piece | Pinned | Where pinned |
|---|---|---|
| Python | 3.12 | `env/pins.json` |
| CAD | CadQuery 2.8.0, OCP 7.9.3.1.1, every transitive package | `env/requirements-cad.txt`, `env/constraints-cad.txt` |
| Firmware | arduino-cli 1.5.1, esp32 core 3.3.10, Waveshare's GFX Library for Arduino 1.6.4 + SensorLib 0.3.1 copies at commit `e4344e7` of waveshareteam/ESP32-S3-Touch-AMOLED-1.75 (the Library Manager's GFX 1.6.4 does not compile on core 3.3.10) | `env/pins.json` |
| Slicer | PrusaSlicer 2.9.7; the flattened profile `cad/slicing/mk4s_hf04_petg_SPEED.ini` (Original Prusa MK4S HF0.4 + 0.20mm SPEED @MK4S HF0.4 + Prusament PETG @HF0.4, resolved from Prusa's vendor bundle by `cad/slicing/flatten_profile.py`) | `env/pins.json`, `cad/slicing/` |
| Previews | Pillow + ziglang 0.17.1 (C++ compiler for `firmware/tools/previews.py`) | `env/requirements-cad.txt` |
| Companion page | `companion/index.html`, nothing to install; Chrome or Edge (Web Serial + microphone) | – |

Setup (first time, and again whenever `env/` or the setup scripts change; the git hook says so after a pull):
- Windows: `powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1`
- macOS: `sh scripts/setup-macos.sh`

It installs Python 3.12 if missing (winget / Homebrew), the venv, arduino-cli with the core and libraries, PrusaSlicer, and the git hooks, then runs `doctor`.

Every task after that is one command (`scripts\md.ps1 <cmd>` on Windows, `scripts/md.sh <cmd>` on macOS):
| Command | Does |
|---|---|
| `doctor` | checks every tool, version and the hooks; says what is missing or stale |
| `cad` / `arm` / `drawing` / `render` | display unit + desk foot / Eino's clamp + fit checks / A10–A12 drawing PDF / renders |
| `slice OUT.bgcode IN.stl ...` | slices with the committed MK4S HF0.4 PETG profile |
| `profile` | regenerates the flattened profile from PrusaSlicer's bundle |
| `fw-build`, `fw-ports`, `fw-flash [PORT]` | compiles; lists ports; compiles and uploads (finds the board's port by itself) |
| `companion` | serves the companion page at http://127.0.0.1:8765 |
| `previews` | re-renders `docs/previews/settings/` from `firmware/mic_display/ui.h` |

Files that stay out of git and how to get them:
- Waveshare's board model `cad/reference/ESP32-S3-Touch-AMOLED-1_75.stp` (18.7 MB, needed by `cad`): download link in `cad/reference/README.md`.
- Eino's arm CAD (needed by `arm`): Eino's own SolidWorks files. Export the assembly's parts as STEP (one file per part, same names, `.step`) into `cad/reference/arm_eino_step/`; the originals go in `cad/reference/arm_eino/`. Both folders are git-ignored; only Eino may decide to commit them (`ALLOW_ARM_CAD=1 git commit`).

## Working rules (both of us and every agent)
1. `git pull --rebase` before starting and again before pushing. Never force-push. If a rebase conflicts in a file you did not change, stop and ask the other person.
2. The repo is the memory: every decision, measured fact, instruction from Kalev or Eino, test result or change lands in the docs it affects (`PLAN.md`, `OPEN_ITEMS.md`, `PARTS.md`, `USE_SETUP.md`, this file's Current state) **in the same commit** as the change, plus one dated line in `docs/LOG.md`: `- YYYY-MM-DD · Who · what and why`. Quote the person's own words when they decide something. Nothing lives only in a chat, an email or one machine.
3. Enforced: the pre-commit hook (`.githooks/`, installed by setup) refuses a commit without a new LOG line, with contact details, keys or tokens, with files over 10 MB, or with Eino's arm CAD. `.claude/settings.json` adds a session-start pull reminder and flags any commit that changed code or CAD without `docs/LOG.md`. Never use `--no-verify`.
4. Stage files by name (`git add path/to/file`), never `git add -A` or `.`.
5. No contact details (emails, phone numbers, addresses), order or tracking numbers, passwords, keys or tokens in the repo. Commit with your GitHub no-reply email (`git config user.email <id>+<user>@users.noreply.github.com`).
6. `docs/OPEN_ITEMS.md` is append-only: items move to Resolved, never disappear.
7. Physical steps are ticked only when physically done; CAD or a simulation is never physical proof.

## Project rules (decided by Kalev unless named)
- Only data the PC can read is shown (2026-11-14): no sensors on the mic.
- Build order (2026-11-14): display unit, mounting interface MI-1 and desk foot first, made physical; the adapter for Eino's arm after. MI-1 dimensions never change once printed.
- This project stands alone: nothing here leans on or mentions other projects; shared tools live in neutral folders.
- Buying (2026-11-14): only sellers with a physical shop, or at least 300 Trustpilot reviews and a real online presence; among those compare the delivered total to Finland (shipping, VAT, customs, stock) in `PARTS.md`. Kalev orders and pays himself. Every order gets a delivery record (`docs/DELIVERY.md` shows the format).
- Build for the real users (2026-11-15): features only for tools Kalev, Eino and the assessors use and understand; cut features are parked in `docs/OPEN_ITEMS.md` (OBS = MD-001), never deleted.
- Spatial layout first (2026-11-15): `docs/USE_SETUP.md` holds who and what is where in real use. Check every claim about seeing, reading, reaching, glare, noise or privacy against it by tracing the actual line; measure or ask unknowns. The webcam sees the back of the display, so the back of the case must look tidy.
- Printing at JHC (LUT/LAB): open Mon–Fri 8:30–18:00; printers need a staff introduction first; booked in LUT Outlook with "Laite: JHC 3D printer1/2/3 Prusa" as attendee and the booker's uni email as the only event title (2026-11-17). The printers have the HF 0.4 nozzle, so slice with the HF0.4 profile. The printer resources auto-decline any booking outside Mon–Fri 08:30–18:00 (a 14:00–Fri 01:00 attempt was declined, 2026-11-18). A long or overnight print is booked as the day's last slot (e.g. 17:00–18:00) and started then: nobody can book the printer 18:00–08:30, so it runs undisturbed until 08:30 (15.5 h).
- The board STEP and assemblies stay out of git (size).
