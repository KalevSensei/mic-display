# Open items

Append-only. Items move to "Resolved" and never disappear. Codes: MD-nnn.

## Open

### MD-001 · Recording status from OBS (parked)
- owner: US
- status: parked 2026-11-15 (owner: "Lets skip the OBS element of this and throw that in open items, neither my or my friend use it and i bet my professors have no idea what that is").
- what it was: the companion page connected to OBS Studio's WebSocket (ws://127.0.0.1:4455, password from OBS → Tools → WebSocket Server Settings) and showed a red "● REC" or "● LIVE" chip at the top of the dial while OBS was recording or streaming.
- removed 2026-11-15 from the page, the firmware drawing and the docs. The serial line keeps its fourth field (always 0) so the protocol does not change if it comes back.
- to bring it back: restore the OBS card and code in `companion/index.html` and the chip in `firmware/mic_display/mic_display.ino` from the commit before the removal (`git log -- companion/index.html`).
- comes back only if Kalev or the classmate starts using OBS.

### MD-003 · Clamp that holds the display on the classmate's mic arm (designed; physical fit open)
- owner: US
- status: designed in CAD 2026-11-17, all CAD checks pass (plan M06). Still open: print (Thu 19 Nov, JHC 3D printer 2, plan M05), buy the hardware (PARTS.md), fit it on Eino's arm and check it there (plan M06 steps 2–7). Moves to Resolved only when it holds the display on his arm. Earlier: parked 2026-11-16 (owner: "bank that open item 4 now i wanna finnisht he monitor stand"), resumed 2026-11-17.
- 2026-11-17, design: U saddle under the upper arm bar (P03, 30 × 15 × 1.5 tube), A11 pad pushed by 2 × M4×10 set screws, display 110 mm out on the user's right beside the Yeti head, M5 friction hinge (tilt −3…103°), male MI-1 rail on A12. Files: `cad/source/md_arm_adapter.py`, `cad/print/A10…A12_*`, `cad/drawings/A10-A12_arm_adapter_drawings.pdf`, `cad/checks/arm_adapter_fit_check.json`. Eino's geometry was read from STEP copies in `cad/reference/arm_eino_step/` (git-ignored).
- what: design the clamp that fixes the display unit (MI-1 dovetail) to the arm's aluminium tube, sized from the tube's real diameter and length.
- input received 2026-11-16: the arm assembly A00_Mikrofonivarsi_Yeti_2palkki_v2.SLDASM (in Kalev's Downloads). It contains no geometry: its 18 components are separate part files on the classmate's Google Drive (G:\Oma Drive\Mikrofonivarsi_Yeti_2palkki_v2\), and none of them were sent. The tube is P03_Varsiputki_2palkki_v2.SLDPRT (used twice). P05_Paa_2palkki_v2 (head) and P04_Kyynarnivel_2palkki_v2 (elbow) show where a clamp can sit.
- 2026-11-17: Eino sent a Pack and Go zip (A00_Mikrofonivarsi_Yeti_2palkki_v2_1.zip, 15 SolidWorks 2026 files incl. P03_Varsiputki, about 3.5 MB) as a share link on his LUT OneDrive (email "mic stand", 17 Nov 14:39, uni mail). Next: download it into cad/reference/arm/ (outside git), read the tube with the probe, design the clamp.
- needed to resume (before 17 Nov): P03_Varsiputki_2palkki_v2.SLDPRT, or better the whole Mikrofonivarsi_Yeti_2palkki_v2 folder or a SolidWorks Pack and Go zip, from the classmate. The reader C:\Users\kalev\tools\swprobe\probe.ps1 opens it in an invisible SolidWorks and lists every tube radius, axis and length.

### MD-005 · One-file installer for the PC app (Eino's PC)
- owner: US
- status: open 2026-11-19 (from MD-002).
- why: the PC app runs from the repo with the project Python, which `scripts/setup-windows.ps1` installs together with the CAD, firmware and slicer tools. That is fine on Kalev's laptop; Eino's PC (plan M07) should get the app alone.
- what: one Windows installer or single .exe of `pcapp/` (Python, numpy, scipy, sounddevice, comtypes, pystray bundled), per-user, no admin, with Start with Windows on by default.
- done when: on a Windows PC without the repo, one download and one double-click start the app, and the display shows the level and all six PC settings live.

## Resolved

### MD-002 · Windows PC app (makes the PC settings on the display live)
- owner: US
- status: open 2026-11-15; **built and resolved 2026-11-19**, after Kalev opened the settings on firmware 0.3.0: "yea fine but it says need an app".
- why: the display's settings app (plan M03b) has six PC settings: Mic mute, Input device, Input volume, Output device, PC volume and Output mute. A web page cannot change Windows sound settings, so five of them show "Needs the PC app" until this app answers (Input device already works through the companion page). Owner, 2026-11-15: "And can control output device, input device, volume of ur pc i don't know stuff like that that might be usefull?"
- what it does: a small Windows background app that
  - reads the microphone level through Windows audio (level, peak, clipping, sample rate, device name, frequency bands, loudness, talk time) and sends it to the board over the USB cable, so no Chrome tab has to stay open;
  - sets microphone mute, Windows input volume and the default microphone; output mute, Windows master volume (PC volume) and the default output device (speakers or headphones);
  - speaks the protocol in `docs/PROTOCOL.md` (adds the `O` line and answers `C,mute`, `C,vol`, `C,mic`, `C,out`, `C,outvol`, `C,outmute`);
  - finds the board's USB port by itself, starts with Windows, sits in the notification area, and comes as one installer.
- done when: on Kalev's PC, after one install and a restart, the display shows the level with no browser open, and all six PC settings on the display change Windows and follow changes made in Windows.
- built 2026-11-19 (plan M03c): `pcapp/mic_display_app.py` + `pcapp/core_audio.py`, started with `md app` (tray icon, no window; menu: status, Start with Windows, Quit) or `md app --console`. Finds the board by USB VID 0x303A, reconnects after unplug or sleep, says in the tooltip when the port is busy (the companion page has it); measures the Windows default recording device sample by sample (S, F, L with BS.1770 LUFS, talk time) and sends H "PC app", T, P and O; answers all six PC settings with Windows Core Audio (default devices switched through IPolicyConfig, layout from EarTrumpet). Firmware 0.3.1 adds the `C,pc` line so the PC side can read what the settings screens hold. Packages pinned in `env/requirements-app.txt` / `env/constraints-app.txt`, installed by `scripts/setup-windows.ps1`, checked by `md doctor`.
- verified 2026-11-19 on Kalev's laptop with the board on COM3 (firmware 0.3.1), 22 of 22 checks: the board reports all six PC settings live and "PC app" under About; from the display side (simulated: the board's own `C,mute` / `C,vol` / `C,mic` / `C,out` / `C,outvol` / `C,outmute` lines fed to the app, the glass was not touched) Windows changed and the board held the new value 0.03–0.12 s later; from the Windows side (mute, volumes, default microphone) the board held the change 0.08–0.5 s later. Output device switching ran only as "re-select the one output": the laptop has a single active output. The laptop's audio state was recorded first and restored exactly.
- not covered here: a real tap on the glass for each setting (Kalev, plan M03c step 3); a real unplug/replug and a Windows restart with Start with Windows on; switching between two real outputs (plug in headphones); the one-file installer for Eino's PC (new item MD-005).

### MD-004 · Which side of Eino's arm the display sits on (confirm before printing)
- owner: Eino
- status: open 2026-11-18; resolved 2026-11-19 (Eino: "on the right side"). The display sits on the user's right; print the right-hand A10, as the JHC plate file already does.
- what: the JHC plate file prints the right-hand clamp (`A10_PETG_arm_clamp_base_display_right`, display on the user's right beside the Yeti head). AGENTS.md says where the clamp sits is Eino's call, and no decision of his is recorded. If he wants it on the left, print `A10_PETG_arm_clamp_base_display_left.stl` instead (re-slice with `md slice`).
- done when: Eino's choice is quoted here and in PLAN.md M06.
