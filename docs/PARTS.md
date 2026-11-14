# Parts

Owner decisions, 2026-11-14: no light sensor ("lets use only data the pc can pick up"). Pick one of the two builds below; both were in stock when checked on 2026-11-14.

## Basic build: one Electrokit order, 308 SEK ≈ €27 before shipping

| # | Part | Electrokit article | Price | Stock (14 Nov) | Link |
|---|------|--------------------|-------|----------------|------|
| 1 | Seeed Studio XIAO ESP32C3 (board, USB-C, pin headers and antenna included) | 41024000 | 109 SEK | 15 | https://www.electrokit.com/en/seeed-studio-xiao-esp32c3 |
| 2 | 1.28" LCD IPS 240×240 round SPI, GC9A01 | 41036507 | 199 SEK | 4 | https://www.electrokit.com/en/lcd-module-round-1.28240x240px-spi |

## Upgraded build (chosen: the housing in cad/ is designed around this board)

Waveshare ESP32-S3-Touch-AMOLED-1.75: board and round 1.75" AMOLED screen in one, no wiring. We print our own housing, so the Waveshare case is optional (with case = SKU 31262 "-B", without = 31261). Shops checked 2026-11-14, delivered to Finland:

| Shop | Version | Price | Delivery to Finland | Stock |
|------|---------|-------|---------------------|-------|
| **Grobotronics** (Greece, EU: no customs) | with case | €44.90 incl. VAT | courier, cost shown at checkout | in stock |
| Grobotronics | without case | €39.90 | same | back 21 Nov |
| OpenELAB | with case | €41.53 incl. Finnish VAT + €7.95 | FedEx 3–5 days, but it is a **pre-order from China** | pre-order |
| The Pi Hut (UK) | with case | £36.60 | **EU orders only by DHL Express, £30** (UK checkout update), ≈ €80 total | 12 left |

Pick: Grobotronics, with case, in stock: https://grobotronics.com/waveshare-esp32-s3-touch-amoled-1-75-466466.html?sl=en . If its courier price at checkout is above about €30, The Pi Hut by DHL Express costs the same and arrives in 1–2 days.

Why it works for this build: ESP32-S3 with native USB (the companion page talks to it over Web Serial); Waveshare's own Arduino example drives this exact screen (CO5300) with the same graphics library as our firmware; Waveshare's 3D model of the board sits in our housing with zero overlap (cad/checks/fit_check.json).

## Both builds
- Only if he does not already own one: a **USB-C data cable**, 1.5–2 m (a charge-only cable carries no data).
- Upgraded build housing: **6 × M2 × 6 socket-head screws** (ISO 4762), 1.5 mm hex key. Three go into the board's own brass standoffs, three into the printed shell.
- From JHC: thin hook-up wire, solder, heat-shrink (basic build only), PETG filament for the housing (about 30 g, 25 €/kg).
