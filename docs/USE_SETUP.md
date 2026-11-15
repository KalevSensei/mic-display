# Use setup: who and what is where

Owner rule, 2026-11-15: "In this engineering project and physical things we build thats a pretty important dimension we need to have right at all times." Every claim about seeing, reading, reaching, hearing, glare or privacy is checked against this layout first by tracing the actual line. A fact that is not known is marked "assumed" until it is measured. Measured facts replace assumed ones; then every check below is redone.

## Layout (top view, user seated at a desk)

```
        wall
  ┌──────────────────────────┐
  │   [ monitor ]  ◄ webcam on top, lens faces the user
  │        ▲
  │        │ 60–70 cm (assumed)
  │   (mic)▼◄─ display on the mic arm, glass faces the user
  │      ( user )
  └──────────────────────────┘
```

| Thing | Where | Faces | Source |
|---|---|---|---|
| User's eyes | seated, about 45 cm above the desk top | the monitor | assumed |
| Monitor + webcam | in front of the user, 60–70 cm from the eyes, webcam on the top edge | the user | assumed |
| Yeti mic | on a boom arm, capsule 10–20 cm from the mouth, in front of or slightly beside the face | the user (side-address: talk into the side with the logo) | assumed |
| Display on the arm | on the arm near the mic, 30–45 cm from the eyes | the user (glass towards the face) | design intent |
| Display on the desk foot | on the desk, glass centre 80 mm above the desk top, glass tilted 15° back | the user | design (A00) |
| USB cable | leaves the display at the bottom edge (USB-C opening in D01), runs down the arm or the foot to the PC | – | design (D01) |

## Checks traced through the layout
1. **Webcam / stream viewers:** the webcam on the monitor looks at the user from the front; the display's glass also faces the user, so the camera sees the **back** of the display (D02 with the dovetail and the cable). Viewers cannot read the screen. So the **back of the case is the side that appears on camera** and has to look tidy (clean D02 face, cable exit at the bottom). Exception: a second camera beside the user, which nobody has said they use. Someone standing behind the user can read the screen, the same as the monitor.
2. **Reading distance:** 466 px across 44.5 mm of glass = 10.5 px/mm. Smallest label on the dial ≈ 21 px ≈ 2.0 mm tall; at 40 cm that subtends about 17 arcminutes, which is just readable. The level numbers (≈ 90 px ≈ 8.6 mm) read easily at arm's length. The smallest text on the board is checked again at the real distance at M06.
3. **Desk foot viewing angle:** eye 45 cm above the desk and 50 cm away, glass centre 8 cm above the desk, so the eye is 36.5° above horizontal as seen from the display. The glass normal points 15° up, so the view is 21° off the screen's axis. AMOLED has no colour shift at that angle.
4. **Touch reach and noise:** the arm is within arm's reach while seated. A tap travels through the arm into the mic, so touch is for use between takes (faces, settings), not while recording.
5. **Light:** at night the AMOLED lights the face from below and in front; the Brightness setting and screen sleep (15 min default) cover this. Glare from a window behind the user would land on the glass; it is checked at M06.
6. **Mounting orientation:** on an arm the display may hang at an angle; the board's motion sensor can turn the picture upright (not built yet; check at M06 how the friend's arm holds it).

## To measure on the friend's setup (M06)
- Arm type and where the display can sit on it; the distance from the eyes to the display.
- Where his webcam is, and whether any camera films from the side.
- Light sources behind or beside him (windows, lamps).
- How the arm carries the cable to the PC.
