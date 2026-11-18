# Parts

Owner decisions, 2026-11-14: no light sensor ("lets use only data the pc can pick up"). Pick one of the two builds below; both were in stock when checked on 2026-11-14.

## Basic build: one Electrokit order, 308 SEK ≈ €27 before shipping

| # | Part | Electrokit article | Price | Stock (14 Nov) | Link |
|---|------|--------------------|-------|----------------|------|
| 1 | Seeed Studio XIAO ESP32C3 (board, USB-C, pin headers and antenna included) | 41024000 | 109 SEK | 15 | https://www.electrokit.com/en/seeed-studio-xiao-esp32c3 |
| 2 | 1.28" LCD IPS 240×240 round SPI, GC9A01 | 41036507 | 199 SEK | 4 | https://www.electrokit.com/en/lcd-module-round-1.28240x240px-spi |

## Upgraded build (chosen: the housing in cad/ is designed around this board)

Waveshare ESP32-S3-Touch-AMOLED-1.75: board and round 1.75" AMOLED screen in one, no wiring. We print our own housing, so the Waveshare case is optional (with case = SKU 31262 "-B", without = 31261).

**Buy at The Pi Hut** (owner, 2026-11-14: "the pi hut was actually perfect"): option "Standard + Case", £36.60, 12 in stock on 14 Nov, https://thepihut.com/products/esp32-s3-1-75-amoled-round-touch-display-dev-board-466x466 . To Finland it currently ships only by DHL Express (£30, 1–2 working days); Finnish VAT is charged at checkout. Since 1 July 2026 the EU also charges a flat €3 customs duty on parcels under €150, and Pi Hut does not collect it, so DHL may ask about €3 (possibly plus a DHL fee) before delivery (see DELIVERY.md).

Seller bar (owner, 2026-11-14): a shop is recommended only with a physical shop, or at least 300 Trustpilot reviews and a real online presence. Grobotronics and OpenELAB (cheaper listings found 14 Nov) fail it and are not used.

Why it works for this build: ESP32-S3 with native USB (the companion page talks to it over Web Serial); Waveshare's own Arduino example drives this exact screen (CO5300) with the same graphics library as our firmware; Waveshare's 3D model of the board sits in our housing with zero overlap (cad/checks/fit_check.json).

## Both builds
- Only if he does not already own one: a **USB-C data cable**, 1.5–2 m (a charge-only cable carries no data).
- Upgraded build housing: **6 × M2 × 6 socket-head screws** (ISO 4762), 1.5 mm hex key. Three go into the board's own brass standoffs, three into the printed shell.
- From JHC: thin hook-up wire, solder, heat-shrink (basic build only), PETG filament for the housing (about 30 g, 25 €/kg).

## Stand adapter #1 for the classmate's arm (plan M06)

Printed at JHC in PETG (plan M05 booking): A10 33.05 g, A11 3.89 g, A12 4.61 g as sliced (41.55 g; with D01 + D02 the whole plate is 54.86 g, about €1.40 of filament at 25 €/kg).

Bought hardware, all at K-Rauta (physical shops across Finland). Prices and stock from k-rauta.fi on 17 Nov; pick the Lappeenranta shop in the site's store selector to see its shelf stock before going. The M5×25 is in only 3 K-Rauta shops: if Lappeenranta has none, any M5×25 socket head screw to ISO 4762 / DIN 912 (steel 8.8 or stainless A2/A4) from another shop with a physical store fits.

| Qty | Part (any of these standards fits) | Buy | Price (17 Nov) |
|---|---|---|---|
| 2 | M4×10 set screw, hex socket, flat point, ISO 4026 / DIN 913 | K-Rauta "Pidätinruuvi Suki iso4026 Zn M4x10mm", product 502266493, sold singly, in 53 shops: https://www.k-rauta.fi/tuote/pidatinruuvi-suki-iso4026-zn-m4x10mm/4032526824033 | €0.20 each |
| 2 | M4 hex nut, 7 mm across flats, 3.2 thick, ISO 4032 / DIN 934 | K-Rauta "Kuusiomutteri PROF DIN934 M4 sähkösinkitty 200kpl", product 502245931, 63 shops: https://www.k-rauta.fi/tuote/kuusiomutteri-prof-din934-m4-i8i-sahkosinkitty-200kpl/6438313620204 | €2.95 / 200 |
| 1 | M5×25 socket head cap screw, ISO 4762 / DIN 912 | K-Rauta "Kuusiokoloruuvi Arctic Prosteel DIN912 AISI316 M5x25mm 12kpl", product 502578392, 3 shops: https://www.k-rauta.fi/tuote/kuusiokoloruuvi-arctic-marine-din912-aisi316-m5x25mm-12kpl/6430075570674 | €3.45 / 12 |
| 1 | M5 nyloc nut, 8 mm across flats, DIN 985 / ISO 10511 | K-Rauta "Nylock-mutteri DIN 985 A2-70 M5 10kpl", product 501509129, 37 shops: https://www.k-rauta.fi/tuote/nylock-mutteri-din-985-a2-70-m5-10kpl/6438313204855 | €3.95 / 10 |
| 1 | M5 washer 5.3 × 10 × 1, ISO 7089 / DIN 125 | K-Rauta "Aluslevy PROF DIN 125 rst A2 M5 10kpl", product 501509165, 44 shops: https://www.k-rauta.fi/tuote/aluslevy-prof-din-125-rst-a2-m5-10kpl/6438313204916 | €3.49 / 10 |

Total at K-Rauta: €14.24. Keep the hinge screw at 25 mm: the CAD checks were run with it (it passes the nyloc by 2.9 mm and clears the display through the whole tilt); other lengths are not checked. Tools: 2 mm hex key (set screws, finger-tight on the short arm) and 4 mm hex key (hinge; the nyloc sits in a hex pocket and needs no spanner).

## Shopping list: every screw the display and the clamp need (Eino, 2026-11-18)

Eino decided to buy the hardware as designed instead of changing the parts to fit other screws (after asking whether to redesign for M3: "so what need to buy"). Ask the JHC staff first whether they keep any of these; Eino was told JHC only has M3 (not checked).

| Qty | Part | Goes into | Where |
|---|---|---|---|
| 6 | M2×6 socket head cap screw, ISO 4762 / DIN 912 | D01/D02: 3 into the board's brass standoffs, 3 into the printed shell | no shop named yet; any hardware shop with M2 |
| 2 | M4×10 set screw, hex socket, flat point, ISO 4026 / DIN 913 | A10, push the A11 pad against the arm's tube | K-Rauta (table above) |
| 2 | M4 hex nut, ISO 4032 / DIN 934 | A10 nut slots, for the set screws | K-Rauta |
| 1 | M5×25 socket head cap screw, ISO 4762 / DIN 912, exactly 25 mm | A12 tilt hinge | K-Rauta (3 shops) or any DIN 912 M5×25 |
| 1 | M5 nyloc nut, DIN 985 / ISO 10511 | A12 hinge, hex pocket | K-Rauta |
| 1 | M5 washer 5.3 × 10 × 1, ISO 7089 / DIN 125 | under the hinge screw head | K-Rauta |

Tools: 1.5 mm, 2 mm and 4 mm hex keys.

Why not other screws (2026-11-18): the M2 size is fixed by the board's own standoffs; the hinge holds the display 110 mm out and was only checked with M5×25; an M3 or M6 version of A10/A12 means a redesign, new fit checks and a new print file. Eino's own screw stock (M6 and M8, no M2/M4/M5, no set screws) fits none of the holes.
