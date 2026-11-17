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
| Display on the arm | on the upper arm bar beside the Yeti head, 110 mm out from the bar on the user's right, below the Yeti body; 389–401 mm from the eyes | the user (glass towards the face, 16° off its axis) | design (A10–A12, plan M06), traced in CAD |
| User's eyes (arm trace) | seated in line with the arm beyond the Yeti head; mouth level with the capsule (280 mm above the head pivot) and 100–200 mm in front of it; eyes 75 mm above the mouth and 10 mm behind it; head moves ±40 mm sideways | the Yeti and the monitor | assumed (used for the M06 CAD trace) |
| Display on the desk foot | on the desk, glass centre 80 mm above the desk top, glass tilted 15° back | the user | design (A00) |
| USB cable | leaves the display at the bottom edge (USB-C opening in D01), runs down the arm or the foot to the PC | – | design (D01) |

## Checks traced through the layout
1. **Webcam / stream viewers:** the webcam on the monitor looks at the user from the front; the display's glass also faces the user, so the camera sees the **back** of the display (D02 with the dovetail and the cable). Viewers cannot read the screen. So the **back of the case is the side that appears on camera** and has to look tidy (clean D02 face, cable exit at the bottom). Exception: a second camera beside the user, which nobody has said they use. Someone standing behind the user can read the screen, the same as the monitor.
2. **Reading distance:** 466 px across 44.5 mm of glass = 10.5 px/mm. Smallest label on the dial ≈ 21 px ≈ 2.0 mm tall; at 40 cm that subtends about 17 arcminutes, which is just readable. The level numbers (≈ 90 px ≈ 8.6 mm) read easily at arm's length. On the arm adapter (M06) the CAD distance is 389–401 mm, so the smallest label subtends about 17 arcminutes there too; checked again from his real seat.
3. **Desk foot viewing angle:** eye 45 cm above the desk and 50 cm away, glass centre 8 cm above the desk, so the eye is 36.5° above horizontal as seen from the display. The glass normal points 15° up, so the view is 21° off the screen's axis. AMOLED has no colour shift at that angle.
4. **Touch reach and noise:** the arm is within arm's reach while seated. A tap travels through the arm into the mic, so touch is for use between takes (faces, settings), not while recording.
5. **Light:** at night the AMOLED lights the face from below and in front; the Brightness setting and screen sleep (15 min default) cover this. Glare from a window behind the user would land on the glass; it is checked at M06.
6. **Mounting orientation:** on the arm adapter (M06) the display's left-right axis lies along the tilt hinge, which is perpendicular to the arm's upright plane, so it stays level in every arm pose; tilting only turns the glass towards the eye. The picture stays upright from the user's seat without the motion sensor.
7. **Arm adapter sight lines (M06, CAD trace from the assumed eye):** the whole glass is visible past the Yeti, its cradle and the bar at bar angles −28.5°, −20°, 0° and +20° with the Yeti tilted ±10° (at least 98.4 % at ±20°); the display sits at least 54° below horizontal while the monitor's lower edge is 28° below, so it never covers the monitor; its top stays at most 41 mm above the head pivot, under the Yeti body (144 mm), out of the mouth-to-capsule path. The webcam sees its back (check 1).

## To measure on the friend's setup (M06)
- Arm type: known from his CAD (2026-11-17, plan M06). Still to check from his real seat: the distance from his eyes to the display and the eye position assumed above.
- Where his webcam is, and whether any camera films from the side.
- Light sources behind or beside him (windows, lamps).
- How the arm carries the cable to the PC.
