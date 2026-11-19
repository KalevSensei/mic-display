# Protocol between the PC and the display

Version 2 (2026-11-15). One USB cable; the board shows up on the PC as a USB serial port. 115200 baud, plain text,
one message per line, ending in `\n` (a `\r` before it is ignored). Fields are separated by commas, so no field
may contain a comma (senders replace commas in device names with spaces). `-` in a field means "unknown or not
available". Lines the receiver does not know are ignored, so either side can be newer than the other.

Who talks:
- **PC side**: today the companion page (`companion/index.html`, Chrome or Edge); later the Windows PC app
  (open item MD-002), which speaks the same lines and adds the ones a browser cannot answer.
- **Board**: `firmware/mic_display/` (all parsing and drawing in `ui.h`).

Version 1 had only the `S` line. It is unchanged, so a version-1 page still drives a version-2 board.

## PC to board

| Line | Meaning | When |
|---|---|---|
| `S,<level>,<peak>,<clip>,0,<rate>,<name>` | `level`: RMS level in dBFS × 10 (needle, with the page's VU ballistics). `peak`: highest sample peak since the previous `S` line, dBFS × 10 (the board holds it as its Peak hold setting says). `clip`: 1 while clipping (held for 1 s by the sender). Fourth field reserved, always 0 (was the recording status, parked as MD-001). `rate`: sample rate in Hz. `name`: input device name, up to 22 characters. | 20 per second while measuring |
| `F,<n>,<b1>,…,<bn>` | Frequency bands for the bars face: `n` bands (up to 32; the page sends 32, log-spaced 50 Hz to 16 kHz), each 0–100 (0 = −90 dB, 100 = −25 dB per band). | 20 per second, only while the board shows the bars face (`C,face,bars`) |
| `L,<short>,<session>,<talk>,<sessiontime>` | `short`: short-term loudness, LUFS × 10 (3 s window, K-weighted). `session`: integrated loudness of the session, LUFS × 10 (400 ms blocks, gated at −70 LUFS and −10 LU, as ITU-R BS.1770). `talk`: seconds the level was above the silence floor (−55 dBFS) this session. `sessiontime`: seconds measured this session. `-` until known. | 4 per second while measuring |
| `T,<unix>,<offset>` | Clock: Unix time in seconds and the PC's UTC offset in minutes (Finland: 120 in winter, 180 in summer). The board keeps time between lines. | on connect, on the first `C,hello` from a board, and every minute |
| `H,<client>,<version>` | Who is talking: `Companion page` or `PC app`, and the protocol version (2). Shown under About. | on connect and every 2 s |
| `P,<mute>,<vol>,<index>,<count>,<name1>,…` | The PC's microphone side. `mute`: 1 muted, 0 live. `vol`: Windows input volume 0–100. `index`: which of the listed inputs is in use (0-based). `count`: how many names follow (up to 8, each up to 31 characters). | on connect, every 2 s, and right after any change |
| `O,<mute>,<vol>,<index>,<count>,<name1>,…` | The PC's sound output, same fields: output mute, Windows master volume 0–100, which output device (speakers, headphones) plays. | same as `P` (PC app only) |

A setting on the display is live only while its field arrived in the last 6 s and is not `-`. Otherwise it is
greyed with the line "Needs the PC app". The companion page sends `P,-,-,<index>,<count>,<names>`: a browser
cannot read or set Windows mute or volume, but it can choose which input it measures, so on the display
**Input device** works with the page alone and the other five PC settings wait for the PC app. The page sends no
`O` line.

## Board to PC

All board lines start with `C,`. Senders of the PC side act on the ones they can and ignore the rest; the board
changes its own screen at once and takes the PC's next `P`/`O` line as confirmation (it ignores an older value in
that field for 1.5 s, 3 s for a device change, so the screen does not flicker back).

| Line | Meaning | Sent | Companion page | PC app (MD-002) |
|---|---|---|---|---|
| `C,hello,<firmware>` | The board is here, firmware version (now `0.3.0`). | at start-up, when the `S` stream starts, every 5 s | answers with `H`, `P`, `T` | same, plus `O` |
| `C,face,<id>` | The face on screen: `dial`, `rings`, `big`, `modular`, `bars`, `loudness`, `talk`, `clock` (`rings`, `big`, `modular` new in 0.3.0; a PC side that does not know an id ignores it). | with every hello and on each swipe | draws the same face; sends `F` only for `bars` | same (no drawing needed) |
| `C,peakhold,<s>` | The board's Peak hold setting: 0 (off: momentary peak), 1 or 3 s. | with every hello and on change | uses the same hold on its own dial | ignore |
| `C,reset` | The user cleared peak and clip count on the display. | on the Reset tap | clears its own peak and clip count | ignore |
| `C,mic,<index>` | Use input `<index>` from the last `P` list. | Input device ‹ › | switches the input it measures | sets the Windows default recording device |
| `C,mute,<0/1>` | Mute or unmute the microphone. | Mic mute tap | not possible in a browser: no answer | Windows microphone mute |
| `C,vol,<0-100>` | Windows input volume. | Input volume ring or − + (at most 10 per second while dragging, and the final value) | no answer | sets it |
| `C,out,<index>` | Use output `<index>` from the last `O` list. | Output device ‹ › | no answer | sets the Windows default playback device |
| `C,outvol,<0-100>` | Windows master volume. | PC volume ring or − + | no answer | sets it |
| `C,outmute,<0/1>` | Mute or unmute the PC's sound. | Output mute tap | no answer | sets it |
| `C,perf,<render_ms>,<push_ms>,<fps>,<rows>` | How fast the screen runs, averaged over the last 5 s (new in 0.3.0): `render_ms` = time core 1 spends easing and drawing one frame (all 8 bands, hashing included), `push_ms` = time core 0 spends sending one frame's changed rows over QSPI (both run at once, so a frame takes about the larger of the two), `fps` = frames drawn per second (up to 60 while something moves, 2 at rest), `rows` = screen rows sent per frame (of 466). Decimals with a point. `C,perf,-,-,0.0,0` when no frame was drawn (screen asleep). | every 5 s | shows it under Now > Display speed | ignore |

Example, the page and a board after connecting (→ to the board, ← from it):
```
← C,hello,0.3.0
← C,face,dial
← C,peakhold,1
→ H,Companion page,2
→ P,-,-,0,2,Yeti Stereo Microphone,Webcam C920
→ T,1794750720,120
→ S,-142,-38,0,0,48000,Yeti Stereo Microphone
→ L,-184,-201,1694,2712
← C,face,bars          (the user swiped)
← C,perf,7.8,9.6,58.2,212   (every 5 s; example numbers, not measured)
→ F,32,22,31,44,…
← C,mic,1              (the user picked the webcam on the display)
→ P,-,-,1,2,Yeti Stereo Microphone,Webcam C920
```

## Settings stored on the board

Brightness (10–100 %, default 80), Screen sleep (never / 5 / 15 / 30 min, default 15; wakes on touch or on sound
above −55 dBFS), Peak hold (off / 1 s / 3 s, default 1 s) and the face shown (default dial) are saved in the
board's flash (NVS namespace `micdisp`) and survive unplugging. PC settings live on the PC; the board only shows
what the PC last reported.
