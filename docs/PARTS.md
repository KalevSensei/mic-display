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
