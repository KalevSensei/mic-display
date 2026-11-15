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

## Resolved
- none yet
