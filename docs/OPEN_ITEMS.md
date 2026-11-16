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

### MD-002 · Windows PC app (makes the PC settings on the display live)
- owner: US
- status: open 2026-11-15; next after the board runs the M03b firmware.
- why: the display's settings app (plan M03b) has six PC settings: Mic mute, Input device, Input volume, Output device, PC volume and Output mute. A web page cannot change Windows sound settings, so five of them show "Needs the PC app" until this app answers (Input device already works through the companion page). Owner, 2026-11-15: "And can control output device, input device, volume of ur pc i don't know stuff like that that might be usefull?"
- what it does: a small Windows background app that
  - reads the microphone level through Windows audio (level, peak, clipping, sample rate, device name, frequency bands, loudness, talk time) and sends it to the board over the USB cable, so no Chrome tab has to stay open;
  - sets microphone mute, Windows input volume and the default microphone; output mute, Windows master volume (PC volume) and the default output device (speakers or headphones);
  - speaks the protocol in `docs/PROTOCOL.md` (adds the `O` line and answers `C,mute`, `C,vol`, `C,mic`, `C,out`, `C,outvol`, `C,outmute`);
  - finds the board's USB port by itself, starts with Windows, sits in the notification area, and comes as one installer.
- done when: on Kalev's PC, after one install and a restart, the display shows the level with no browser open, and all six PC settings on the display change Windows and follow changes made in Windows.

### MD-003 · Clamp that holds the display on the classmate's mic arm (parked)
- owner: US
- status: parked 2026-11-16 (owner: "bank that open item 4 now i wanna finnisht he monitor stand").
- what: design the clamp that fixes the display unit (MI-1 dovetail) to the arm's aluminium tube, sized from the tube's real diameter and length.
- input received 2026-11-16: the arm assembly A00_Mikrofonivarsi_Yeti_2palkki_v2.SLDASM (in Kalev's Downloads). It contains no geometry: its 18 components are separate part files on the classmate's Google Drive (G:\Oma Drive\Mikrofonivarsi_Yeti_2palkki_v2\), and none of them were sent. The tube is P03_Varsiputki_2palkki_v2.SLDPRT (used twice). P05_Paa_2palkki_v2 (head) and P04_Kyynarnivel_2palkki_v2 (elbow) show where a clamp can sit.
- needed to resume: P03_Varsiputki_2palkki_v2.SLDPRT, or better the whole Mikrofonivarsi_Yeti_2palkki_v2 folder or a SolidWorks Pack and Go zip, from the classmate. The reader C:\Users\kalev\tools\swprobe\probe.ps1 opens it in an invisible SolidWorks and lists every tube radius, axis and length.

## Resolved
- none yet
